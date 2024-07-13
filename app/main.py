from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from celery.schedules import crontab
import asyncio

# from .api_requests.dappradar import get_uaw_from_dappradar
from orm.initialize_functions import add_all_collections, init_db_new, add_collection
from utils import load_collections_from_file
from app.celery_config import celery_app

lock = asyncio.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print('server started')
    init_db_new()
    # Schedule periodic tasks
    # collections = load_collections_from_file('games.json')
    # print(add_collection.__name__)
    # for collection in collections:
    #     celery_app.conf.beat_schedule[f'fetch-data-{collection}'] = {
    #         'task': 'orm.intialize_functions.add_collection',
    #         'schedule': crontab(minute='*/5'),
    #         'args': (collection,),
    #     }
    yield
    print('server stopped')

app = FastAPI(lifespan=lifespan)

@app.get("/")
def hello_world():
    return {"message": "OK"}

# @app.on_event('startup')
# @repeat_every(seconds=300)
# async def fetch_data() -> None:
#     async with lock:
#         collections = load_collections_from_file('games.json')
#         add_all_collections(collections)

# initial_sql = [
#     "./db/raw_sql/drop_tables.sql",
#     "./db/raw_sql/tables.sql",
#     "./db/raw_sql/hypertables.sql",
#     "./db/raw_sql/indexes.sql",
# ]


# @app.on_event("startup")
# def init() -> None:
#     initialize_db_tables(initial_sql)


# @app.on_event("startup")
# def print_uaw() -> None:
#          print(get_uaw_from_dappradar("9495", "30d"))


# @app.on_event("startup")
# @repeat_every(seconds=5)
# def print_message() -> None:
#     print("Server is running!")