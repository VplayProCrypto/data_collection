from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from db.dappradar import get_uaw_from_dappradar


app = FastAPI()

@app.get("/")
def hello_world():
    return {"message": "OK"}


# @app.on_event("startup")
# def print_uaw() -> None:
#     print(get_uaw_from_dappradar("9495", "30d"))


@app.on_event("startup")
@repeat_every(seconds=5)
def print_message() -> None:
    print("Server is running!")