from fastapi import FastAPI, Depends, HTTPException
from typing import Union, Annotated
from sqlmodel import Session, create_engine, select
from .orm.models import *
from .keys import timescale_url
from .routers import collection, nft

app = FastAPI()
app.include_router(collection.router)

# @app.get('/collections/all')
# async def get_collections(filters: filterDeps) -> list[Collection]:
#     try:
#         if not filters.tags:
#             with Session(engine) as session:
#                 return session.exec(
#                     select(Collection)
#                     .offset(filters.skip)
#                     .limit(filters.limit)
#                 ).all()
#         else:
#             raise NotImplementedError("tags not implemented")
#     except Exception as e:
#         raise HTTPException(status_code=404, detail=e.args)
