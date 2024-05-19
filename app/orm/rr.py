from sqlmodel import SQLModel, create_engine, Session, select, func
from datetime import datetime
from typing import List, Optional
import pytz
from ..orm.models import NFT, NFTDynamic, NFTEvent, Collection, CollectionDynamic, NftOwnership, ERC20Transfer

# Define the database URL
DATABASE_URL = "sqlite:///example.db"  # Replace with your database URL

# Create the database engine
engine = create_engine(DATABASE_URL)

# Function to fetch NFT ownership data in batches
def fetch_nft_ownership_batch(session: Session, batch_size: int, offset: int, game_id: str) -> List[NftOwnership]:
    return session.exec(
        select(NftOwnership).where(NftOwnership.game_id == game_id).limit(batch_size).offset(offset)
    ).all()

# Function to calculate average buy price for each NFT by each wallet
def calculate_average_buy_price(session: Session, ownership: NftOwnership) -> float:
    avg_price = session.exec(
        select(func.avg(ERC20Transfer.price)).where(
            ERC20Transfer.buyer == ownership.buyer,
            ERC20Transfer.collection_slug == ownership.collection_slug,
            ERC20Transfer.event_timestamp >= ownership.buy_time,
            ERC20Transfer.event_timestamp <= ownership.sell_time
        )
    ).first()
    
    return avg_price or 0.0

# Function to calculate ROI for each NFT
def calculate_nft_roi(session: Session, nft_ownerships: List[NftOwnership]) -> List[NFTDynamic]:
    nft_dynamic_entries = []
    for ownership in nft_ownerships:
        # Fetch corresponding ERC20 transfers for this NFT
        erc20_transfers = session.exec(
            select(ERC20Transfer).where(
                ERC20Transfer.buyer == ownership.buyer,
                ERC20Transfer.collection_slug == ownership.collection_slug,
                ERC20Transfer.event_timestamp >= ownership.buy_time,
                ERC20Transfer.event_timestamp <= ownership.sell_time
                # ERC20Transfer.event_timestamp.between(ownership.buy_time, ownership.sell_time or datetime.utcnow())
            )
        ).all()
        
        # Calculate total earnings in ERC20 tokens
        total_erc20_earned = sum(transfer.price for transfer in erc20_transfers)
        
        # Calculate average buy price
        avg_buy_price = calculate_average_buy_price(session, ownership)
        
        if avg_buy_price > 0:
            roi = (total_erc20_earned - avg_buy_price) / avg_buy_price
        else:
            roi = 0.0
        
        # Create an entry for nft_dynamic
        nft_dynamic = NFTDynamic(
            collection_slug=ownership.collection_slug,
            token_id=ownership.token_id,
            contract_address=ownership.contract_address,
            rr=roi,
            event_timestamp=datetime.utcnow().replace(tzinfo=pytz.UTC)
        )
        nft_dynamic_entries.append(nft_dynamic)
    
    return nft_dynamic_entries

# Function to calculate and store ROI for each collection within the specified game
def calculate_and_store_collection_roi(session: Session, game_id: str):
    # Get all collections within the specified game
    collections = session.exec(
        select(Collection.opensea_slug).where(Collection.game_id == game_id)
    ).all()
    
    for collection_slug in collections:
        # Fetch ROI for all NFTs in the collection
        nft_rois = session.exec(
            select(NFTDynamic.rr).where(NFTDynamic.collection_slug == collection_slug)
        ).all()
        
        # Calculate average ROI for the collection
        if nft_rois:
            avg_collection_roi = sum(nft_rois) / len(nft_rois)
        else:
            avg_collection_roi = 0.0
        
        # Update the collection_dynamic table
        collection_dynamic = session.exec(
            select(CollectionDynamic).where(CollectionDynamic.collection_slug == collection_slug)
        ).first()
        
        if collection_dynamic:
            collection_dynamic.roi = avg_collection_roi
            collection_dynamic.event_timestamp = datetime.utcnow().replace(tzinfo=pytz.UTC)
        else:
            collection_dynamic = CollectionDynamic(
                collection_slug=collection_slug,
                game_id=game_id,
                roi=avg_collection_roi,
                event_timestamp=datetime.utcnow().replace(tzinfo=pytz.UTC)
            )
        
        session.add(collection_dynamic)
        session.commit()

# Main function to execute the batch processing and calculations
def main():
    batch_size = 1000
    offset = 0
    game_id = 'YOUR_GAME_ID'  # Replace with your specific game ID
    
    with Session(engine) as session:
        while True:
            nft_ownerships = fetch_nft_ownership_batch(session, batch_size, offset, game_id)
            if not nft_ownerships:
                break
            
            nft_dynamic_entries = calculate_nft_roi(session, nft_ownerships)
            
            session.bulk_save_objects(nft_dynamic_entries)
            session.commit()
            
            offset += batch_size
        
        # Calculate and store ROI for each collection within the specified game
        calculate_and_store_collection_roi(session, game_id)
    return 

if __name__ == "__main__":
    main()
