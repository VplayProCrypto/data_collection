from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every

app = FastAPI()

@app.get("/")
def hello_world():
    return {"message": "OK"}

@app.on_event("startup")
@repeat_every(seconds=5)
def print_message() -> None:
    print("Server is running!")