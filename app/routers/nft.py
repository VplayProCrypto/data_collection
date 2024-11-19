from fastapi import APIRouter, HTTPException, Body, Query, Path, status
from sqlmodel import select, func, text, desc
from sqlalchemy.orm import aliased
from datetime import datetime, timedelta
from pprint import pprint
from typing import Annotated
from pydantic import BaseModel
from ..orm.models import NFT, NFTWithoutStatus, NFTDynamic, NFTEvent, NftOwnership
from ..dependencies import filterDeps, sessionDeps, filterBaseDeps
from ..api_requests.alchemy import Alchemy

router = APIRouter(
    prefix='/nft'
)

class NFTWithStats(BaseModel):
    metadata: NFTWithoutStatus
    current_stats: NFTDynamic

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
        raise HTTPException(status_code=500, detail=e.args)

@router.get('/events/all', response_model = list[NFTEvent])
async def get_nft_events(token_id: str, contract_address: str, session: sessionDeps, filters: filterBaseDeps):
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
        raise HTTPException(status_code=500, detail = e.args)

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
        raise HTTPException(status_code=500, detail = e.args)

@router.post('/dynamic/{contract_address}', response_model = list[NFTWithStats])
async def get_nft_dynamic_batch(
    contract_address: str,
    token_ids: Annotated[list[str], Body(embed=True)],
    session: sessionDeps
):
    query = """
            select distinct on (token_id) *
            from nft_dynamic
            where contract_address = :contract_address
            and token_id = any(:token_ids)
            order by token_id, event_timestamp desc;
    """

    try:
        if not token_ids:
            raise ValueError("The token ids can not be empty")
        recs_dynamic = session.exec(
            text(query),
            params = {
                'contract_address': contract_address,
                'token_ids': token_ids
            }
        ).all()

        # print(token_ids)
        # print(len(recs_dynamic))
        stats = [
            NFTDynamic.model_validate(i) for i in recs_dynamic
        ]
        # print(len(stats))
        # pprint(stats)

        recs_metadata = session.exec(
            select(NFT)
            .where(func.lower(NFT.contract_address) == func.lower(contract_address))
            .where(NFT.token_id.in_(token_ids))
            .order_by(NFT.token_id)
        ).all()
        print(len(recs_metadata))
        pprint(recs_metadata)

        nfts = list(map(
            lambda x: NFTWithStats(metadata=x[0], current_stats=x[1]),
            zip(recs_metadata, stats)
        ))
        print(len(nfts))
        return nfts
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.args)
    except Exception as e:
        # print(e)
        raise HTTPException(status_code=500, detail = e.args)
    # try:
    #     stats = session.exec(
    #         select(NFTDynamic)
    #         .where(NFTDynamic.event_timestamp)
    #     )

@router.get('/dynamic/{contract_address}/{token_id}', response_model = list[NFTDynamic])
async def get_nft_dynamic(
    token_id: str,
    contract_address: str,
    session: sessionDeps,
    history: Annotated[bool, Query(title = "Whether to retrive history")] = False,
    start_date: Annotated[datetime, Query(title = "Start Date from which to retreive the records. Not used if history is false. In ISO 8601 format")] = None):
    try:
        smt = select(NFTDynamic).where(NFTDynamic.token_id == token_id)\
                .where(func.lower(NFTDynamic.contract_address) == func.lower(contract_address))
        if not history:
            smt = smt.order_by(NFTDynamic.event_timestamp.desc()).limit(1)
        elif start_date:
            smt = smt.where(NFTDynamic.event_timestamp >= start_date)
        nft_stats = session.exec(smt).all()
        return nft_stats
    except Exception as e:
        raise HTTPException("Error occured while fetching NFT stats", detail=e.args)

def get_column_name(user_input: str) -> str:
    column_name_mapping = {
        "reward value": "rr_val",
        "rewards": "rr_val",
        "rr": "rr_val"
    }
    # Normalize the user input (e.g., lowercasing and removing spaces)
    user_input_normalized = user_input.strip().lower()
    # Look up the column name in the dictionary
    return column_name_mapping.get(user_input_normalized, None)

@router.get('/top/{contract_address}', response_model = list[NFTWithStats])
async def get_top_nfts(
    *,
    contract_address: str,
    session: sessionDeps,
    tag: str = 'rr',
    filters: filterBaseDeps):
    try:
        # Translate the user input to the actual column name
        ordering_column = get_column_name(tag)

        if not ordering_column:
            raise ValueError(f"Invalid ordering field: '{tag}' is not recognized.")
        
        # Get the appropriate column attribute from the model
        column_attr = getattr(NFTDynamic, ordering_column, None)

        if not column_attr:
            raise ValueError(f"Invalid column reference: '{ordering_column}' is not an attribute of NFTDynamic.")
        
        time_filter_30_days = datetime.now() - timedelta(days = 30)
        
        # Use SQLAlchemy's window function to create the ROW_NUMBER() with PARTITION BY
        row_number = func.row_number().over(
            partition_by=[NFTDynamic.contract_address, NFTDynamic.token_id],
            order_by=[desc(NFTDynamic.event_timestamp)]
        ).label("row_number")

        # Create a subquery that includes the row_number window function
        subquery = (
            select(
                NFTDynamic.collection_slug,
                NFTDynamic.token_id,
                NFTDynamic.embedding,
                NFTDynamic.contract_address,
                NFTDynamic.rr_val,
                NFTDynamic.rr_symbol,
                NFTDynamic.event_timestamp,
                row_number
            )
            .where(NFTDynamic.event_timestamp >= time_filter_30_days)
            .where(func.lower(NFTDynamic.contract_address) == func.lower(contract_address))
            .subquery()
        )

        # Create an aliased version of the subquery for further filtering
        ranked_nft = aliased(NFTDynamic, subquery)

        # Select the final rows where row_number = 1 and order by the dynamic field
        query = (
            select(ranked_nft)
            .where(subquery.c.row_number == 1)
            .order_by(desc(subquery.c[ordering_column]))
            .limit(filters.limit)
        )
        # Execute the query and return results
        nfts = session.exec(query).all()
        # print(nfts[0])
        token_ids = [i.token_id for i in nfts]
        # print(len(token_ids))
        metadatas = session.exec(
            select(NFT)
            .where(func.lower(NFT.contract_address) == func.lower(contract_address))
            .where(NFT.token_id.in_(token_ids))
            .order_by(NFT.token_id)
        ).all()
        nfts = sorted(nfts, key = lambda x: x.token_id)
        # print(len(nfts))
        return list(map(
            lambda x: NFTWithStats(metadata=x[0], current_stats=x[1]),
            zip(metadatas, nfts)
        ))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail = e.args)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail = e.args)
    # smt = (
    #     select(NFTDynamic)
    #     .where(func.lower(NFTDynamic.contract_address) == func.lower(contract_address))
    #     .offset(filters.skip)
    #     .limit(filters.limit)
    # )
    # try:
    #     nfts = session