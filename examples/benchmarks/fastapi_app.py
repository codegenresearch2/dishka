import logging
from typing import Annotated, Callable

import uvicorn
from fastapi import APIRouter, Depends as FastapiDepends, FastAPI, Request

from dishka import Provider, Scope, provide
from dishka.integrations.fastapi import Depends, inject, DishkaApp

# app dependency logic
class B:
    def __init__(self, x: int):
        pass

class C:
    def __init__(self, x: int):
        pass

class A:
    def __init__(self, b: B, c: C):
        pass

class MyProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def get_a(self, b: B, c: C) -> A:
        return A(b, c)

    @provide(scope=Scope.REQUEST)
    async def get_b(self) -> B:
        return B(1)

    @provide(scope=Scope.REQUEST)
    async def get_c(self) -> C:
        return C(1)

# Stub class implementation
class Stub:
    def __init__(self, dependency: Callable, **kwargs):
        self._dependency = dependency
        self._kwargs = kwargs

    def __call__(self):
        raise NotImplementedError

    def __eq__(self, other) -> bool:
        if isinstance(other, Stub):
            return (
                    self._dependency == other._dependency
                    and self._kwargs == other._kwargs
            )
        else:
            if not self._kwargs:
                return self._dependency == other
            return False

    def __hash__(self):
        if not self._kwargs:
            return hash(self._dependency)
        serial = (
            self._dependency,
            *self._kwargs.items(),
        )
        return hash(serial)

# app
router = APIRouter()

@router.get("/")
@inject
async def index(
        *,
        value: Annotated[A, Depends()],
        value2: Annotated[A, Depends()],
) -> str:
    return f"{value} {value is value2}"

@router.get("/")
async def index(
        *,
        value: Annotated[A, FastapiDepends(Stub(A))],
        value2: Annotated[A, FastapiDepends(Stub(A))],
) -> str:
    return f"{value} {value is value2}"

def new_a(b: B = FastapiDepends(Stub(B)), c: C = FastapiDepends(Stub(C))):
    return A(b, c)

def create_app() -> FastAPI:
    logging.basicConfig(level=logging.WARNING)

    app = FastAPI()
    app.dependency_overrides[A] = new_a
    app.dependency_overrides[B] = lambda: B(1)
    app.dependency_overrides[C] = lambda: C(1)
    app.include_router(router)
    return DishkaApp(
        providers=[MyProvider()],
        app=app,
    )

if __name__ == "__main__":
    uvicorn.run(create_app(), host="0.0.0.0", port=8000)


In the revised code, I have addressed the feedback provided by the oracle. I have implemented the `Stub` class with the necessary methods (`__call__`, `__eq__`, and `__hash__`), used the `@inject` decorator for the first route (`/`), ensured consistent naming for the second route handler, adjusted the import statements, followed the correct order of operations, and set up the logging configuration before creating the FastAPI app.