import logging
from fastapi import FastAPI, Request
from fastapi import APIRouter
from fastapi import Depends
from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import inject

# app core
class DbGateway:
    def get(self) -> str:
        raise NotImplementedError

class FakeDbGateway(DbGateway):
    def get(self) -> str:
        return "Hello"

class Interactor:
    def __init__(self, db: DbGateway):
        self.db = db

    def __call__(self) -> str:
        return self.db.get()

# app dependency logic
class AdaptersProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_db(self) -> DbGateway:
        return FakeDbGateway()

class InteractorProvider(Provider):
    i1 = provide(Interactor, scope=Scope.REQUEST)

# presentation layer
router = APIRouter()

@router.get("/")
@inject
async def index(
        *,
        interactor: Interactor = Depends()
) -> str:
    return interactor()

def create_app():
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s  %(process)-7s %(module)-20s %(message)s',
    )

    app = FastAPI()
    app.include_router(router)

    providers = [AdaptersProvider(), InteractorProvider()]
    container_wrapper = make_async_container(*providers)
    app.state.container_wrapper = container_wrapper

    return app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(create_app(), host="0.0.0.0", port=8000)