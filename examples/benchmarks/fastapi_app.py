import logging
from fastapi import FastAPI, APIRouter, Depends
import uvicorn
from dishka import Provider, Scope, provide, make_async_container
from dishka.integrations.fastapi import inject

# app core
class DbGateway:
    async def get(self) -> str:
        raise NotImplementedError

class FakeDbGateway(DbGateway):
    async def get(self) -> str:
        return 'Hello'

class Interactor:
    def __init__(self, db: DbGateway):
        self.db = db

    async def __call__(self) -> str:
        return await self.db.get()

# app dependency logic
class AdaptersProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def get_db(self) -> DbGateway:
        return FakeDbGateway()

class InteractorProvider(Provider):
    i1 = provide(Interactor, scope=Scope.REQUEST)

# presentation layer
router = APIRouter()

@router.get('/')
@inject
async def index(*, interactor: Annotated[Interactor, Depends(lambda: Interactor(db=AdaptersProvider().get_db()))]):
    result = await interactor()
    return result

# FastAPI app setup
async def lifespan(app: FastAPI):
    async with make_async_container(AdaptersProvider(), InteractorProvider()) as container:
        app.state.container = container

def create_app() -> FastAPI:
    logging.basicConfig(level=logging.WARNING)
    app = FastAPI(lifespan=lifespan)
    app.include_router(router)
    return app

if __name__ == '__main__':
    uvicorn.run(create_app(), host='0.0.0.0', port=8000)