from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from api_requests.dappradar import get_uaw_from_dappradar
from orm.initialize_functions import initialize_db_tables

app = FastAPI()

@app.get("/")
def hello_world():
    return {"message": "OK"}



initial_sql = [
    "./db/raw_sql/drop_tables.sql",
    "./db/raw_sql/tables.sql",
    "./db/raw_sql/hypertables.sql",
    "./db/raw_sql/indexes.sql",
]


# @app.on_event("startup")
# def init() -> None:
#     initialize_db_tables(initial_sql)


# @app.on_event("startup")
# def print_uaw() -> None:
#          print(get_uaw_from_dappradar("9495", "30d"))


@app.on_event("startup")
@repeat_every(seconds=5)
def print_message() -> None:
    print("Server is running!")