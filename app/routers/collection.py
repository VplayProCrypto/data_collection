from fastapi import APIRouter, HTTPException
from sqlmodel import select
from datetime import datetime
import requests
from ..orm.models import Collection, CollectionBase, CollectionDynamic, ContractBase, PaymentTokenBase, FeeBase
from ..dependencies import filterDeps, sessionDeps

router = APIRouter(
    prefix='/collections'
)

class CollectionWithRelationships(CollectionBase):
    contracts: list[ContractBase]
    # fees: list[FeeBase]
    payment_tokens: list[PaymentTokenBase]

@router.get('/all/')
async def get_collections(filters: filterDeps, session: sessionDeps) -> list[CollectionWithRelationships]:
    try:
        if not filters.tags:
            return session.exec(
                select(Collection)
                .offset(filters.skip)
                .limit(filters.limit)
            ).all()
        else:
            raise NotImplementedError("tags not implemented")
    except Exception as e:
        raise HTTPException(status_code=404, detail=e.args)

@router.get('/{game_id}/')
async def get_collection(game_id: str, session: sessionDeps) -> list[CollectionWithRelationships]:
    collections = session.exec(
        select(Collection)
        .where(Collection.game_id == game_id)
    ).all()
    for collection in collections:
        print("--", collection.contracts, "--")

    return collections

@router.get('/{collection_slug}/stats')
async def get_stats(*, collection_slug: str, start_date: datetime | None = None, session: sessionDeps) -> list[CollectionDynamic]:
    try:
        if start_date:
            stats = session.exec(
                select(CollectionDynamic)
                .where(CollectionDynamic.event_timestamp >= start_date)
                .where(CollectionDynamic.collection_slug == collection_slug)
            ).all()
        else:
            stats = session.exec(
                select(CollectionDynamic)
                .where(CollectionDynamic.collection_slug == collection_slug)
            ).all()
        return stats
    except Exception as e:
        raise HTTPException(status_code=418, detail = e.args)