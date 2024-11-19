from typing import Union, Annotated
from fastapi import Depends
from sqlmodel import Session, create_engine
from pydantic import BaseModel, Field
from .keys import timescale_url

engine = create_engine(timescale_url)

async def get_session():
    with Session(engine) as session:
        yield session

sessionDeps = Annotated[Session, Depends(get_session)]

class filterQueryParamsBase(BaseModel):
    limit: int = Field(default=10, le=100, gt=0)
    skip: int = Field(default=0, ge=0)

class filterQueryParams(filterQueryParamsBase):
    tags: str = Field(default=None)

filterBaseDeps = Annotated[filterQueryParamsBase, Depends(filterQueryParamsBase)]
filterDeps = Annotated[filterQueryParams, Depends(filterQueryParams)]