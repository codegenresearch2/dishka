__all__ = [
    'Depends', 'inject', 'DishkaApp',
]

from inspect import Parameter
from typing import Sequence, get_type_hints

from fastapi import FastAPI, Request

from dishka import Provider, make_async_container
from .base import Depends, wrap_injection

def inject(func):
    hints = get_type_hints(func)
    request_param = next(
        (name for name, hint in hints.items() if hint is Request),
        None,
    )
    if request_param:
        additional_params = []
    else:
        request_param = '____@request'
        additional_params = [Parameter(
            name=request_param,
            annotation=Request,
            kind=Parameter.KEYWORD_ONLY,
        )]

    return wrap_injection(
        func=func,
        remove_depends=True,
        container_getter=lambda kw: kw[request_param].state.dishka_container,
        additional_params=additional_params,
        is_async=True,
    )

async def request_container_middleware(request: Request, call_next):
    async with request.app.state.dishka_container({Request: request}) as request_container:
        request.state.dishka_container = request_container
        return await call_next(request)

class DishkaApp:
    def __init__(self, providers: Sequence[Provider], app: FastAPI):
        self.app = app
        self.container_wrapper = make_async_container(*providers)
        self.app.middleware('http')(request_container_middleware)

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'lifespan':
            async def my_recv():
                message = await receive()
                if message['type'] == 'lifespan.startup':
                    self.app.state.dishka_container = await self.container_wrapper.__aenter__()
                elif message['type'] == 'lifespan.shutdown':
                    await self.app.state.dishka_container.__aexit__(None, None, None)

            await self.app(scope, my_recv, send)
        else:
            return await self.app(scope, receive, send)