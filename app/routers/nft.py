from fastapi import APIRouter, HTTPException
from sqlmodel import select, func, text
from datetime import datetime
from pprint import pprint
from ..orm.models import NFT, NFTWithoutStatus, NFTDynamic, NFTEvent, NftOwnership
from ..dependencies import filterDeps, sessionDeps
from ..api_requests.alchemy import Alchemy

router = APIRouter(
    prefix='/nft'
)

@router.get('/metadata', response_model = NFTWithoutStatus)
async def get_nft_metadata(token_id: str, contract_address: str, session: sessionDeps):
    try:
        nft_data = session.exec(
            select(NFT)
            .where(NFT.token_id == token_id)
            .where(func.lower(NFT.contract_address) == func.lower(contract_address))
        ).first()
        alchemy = Alchemy()
        rarities = alchemy.get_nft_rarity(contract_address=contract_address, token_id=token_id)
        nft_data.traits = rarities
        return nft_data
    except Exception as e:
        return HTTPException("Error occured while processing request", detail=e.args)

@router.get('/events/all', response_model = NFTEvent)
async def get_nft_events(token_id: str, contract_address: str, session: sessionDeps, filters: filterDeps):
    try:
        events =session.exec(
            select(NFTEvent)
            .where(NFTEvent.token_id == token_id)
            .where(func.lower(NFTEvent.contract_address) == func.lower(contract_address))
            .order_by(NFTEvent.event_timestamp.desc())
            .offset(filters.skip)
            .limit(filters.limit)
        ).all()
        return events
    except Exception as e:
        return HTTPException("Error occured while retreiving request", detail = e.args)

@router.get('/events/sales', response_model = list[NFTEvent])
async def get_nft_sales(token_id: str, contract_address: str, session: sessionDeps, start_date: datetime = None):
    try:
        smt = select(NFTEvent).where(NFTEvent.token_id == token_id)\
                .where(func.lower(NFTEvent.contract_address) == func.lower(contract_address))\
                .where(NFTEvent.event_type == 'sale')
                # .order_by(NFTEvent.event_timestamp.desc())
        if start_date:
            smt = smt.where(NFTEvent.event_timestamp >= start_date)
        events =session.exec(smt).all()
        return events
    except Exception as e:
        return HTTPException("Error occured while retreiving request", detail = e.args)

@router.get('/dynamic/{contract_address}')
async def get_nft_dynamic_batch(contract_address: str, nfts: list[str], session: sessionDeps):
    query = """
            select distinct on (token_id)
            from nft_dynamic
            where contract_address = :contract_address
            and token_id = any(:token_ids)
            order by token_id, event_timestamp desc;
    """

    
    # try:
    #     stats = session.exec(
    #         select(NFTDynamic)
    #         .where(NFTDynamic.event_timestamp)
    #     )

@router.get('/dynamic/{contract_address}/{token_id}')
async def get_nft_dynamic(token_id: str, contract_address: str, session: sessionDeps, history: bool = False, start_date: datetime = None):
    try:
        smt = select(NFTDynamic).where(NFTDynamic.token_id == token_id)\
                .where(func.lower(NFTDynamic.contract_address) == func.lower(contract_address))
        if not history:
            smt = smt.order_by(NFTDynamic.event_timestamp.desc()).limit(1)
        else:
            smt = smt.where(NFTDynamic.event_timestamp >= start_date)
        nft_stats = session.exec(smt).all()
        return nft_stats
    except Exception as e:
        return HTTPException("Error occured while fetching NFT stats", detail=e.args)