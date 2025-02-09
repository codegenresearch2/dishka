import logging
from fastapi import FastAPI, Request
import uvicorn
from dishka.integrations.fastapi import Depends, DishkaApp, inject
from dishka import Provider, make_async_container

# app core
class DbGateway:
    def get(self) -> str:
        raise NotImplementedError

class FakeDbGateway(DbGateway):
    def get(self) -> str:
        return 'Hello'

class Interactor:
    def __init__(self, db: DbGateway):
        self.db = db

    def __call__(self) -> str:
        return self.db.get()

# app dependency logic
class AdaptersProvider(Provider):
    @inject
    def get_db(self) -> DbGateway:
        return FakeDbGateway()

class InteractorProvider(Provider):
    i1 = inject(Interactor, scope=Scope.REQUEST)

# presentation layer
router = APIRouter()

@router.get('/')
@inject
async def index(*, interactor: Annotated[Interactor, Depends()]):
    result = interactor()
    return result

def create_app():
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s  %(process)-7s %(module)-20s %(message)s',
    )

    app = FastAPI()
    app.include_router(router)
    return DishkaApp(
        providers=[AdaptersProvider(), InteractorProvider()],
        app=app,
    )

if __name__ == '__main__':
    uvicorn.run(create_app(), host='0.0.0.0', port=8000)
