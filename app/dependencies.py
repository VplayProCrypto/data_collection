from typing import Union, Annotated
from fastapi import Depends
from sqlmodel import Session, create_engine
from .keys import timescale_url

engine = create_engine(timescale_url)

async def get_session():
    with Session(engine) as session:
        yield session

sessionDeps = Annotated[Session, Depends(get_session)]

class filterQueryParams:
    def __init__(self, tags: Union[str, None] = None, skip: int = 0, limit: int = 100):
        self.tags = tags
        self.skip = skip
        self.limit = limit

filterDeps = Annotated[filterQueryParams, Depends(filterQueryParams)]