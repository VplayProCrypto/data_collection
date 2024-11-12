from fastapi import APIRouter, HTTPException
from sqlmodel import select, func
from datetime import datetime
from ..orm.models import NFT, NFTDynamic, NFTEvent, NftOwnership
from ..dependencies import filterDeps, sessionDeps

router = APIRouter(
    prefix='/nft'
)

@router.