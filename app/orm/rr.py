from sqlmodel import SQLModel, create_engine, select, func, Session
from sqlalchemy import desc
# from sqlalchemy.orm import Session
from datetime import datetime
import time
from typing import List, Optional
import pytz
from orm.models import NFT, NFTDynamic, NFTEvent, Collection, CollectionDynamic, NftOwnership, ERC20Transfer
import keys
import json
from pprint import pprint
# import numpy as np

# Define the database URL
# DATABASE_URL = "sqlite:///example.db"  # Replace with your database URL

# Create the database engine
# engine = create_engine(DATABASE_URL)

def sell_time_correction(ownership: NftOwnership):
    if ownership.sell_time:
        sell_time = ownership.sell_time
    else:
        sell_time = datetime.now(pytz.UTC)
    return sell_time
    
# Function to fetch NFT ownership data in batches
def fetch_nft_ownership_batch(session: Session, batch_size: int, offset: int, game_id: str) -> List[NftOwnership]:
    return session.exec(
        select(NftOwnership).where(NftOwnership.game_id == game_id).limit(batch_size).offset(offset)
    ).all()

# Function to calculate average buy price for each NFT by each wallet
def calculate_average_buy_price(session: Session, ownership: NftOwnership) -> float:
    # sell_time = sell_time_correction(ownership)
    t = time.time()
    # avg_price = session.exec(
    #     select(func.avg(ERC20Transfer.price)).where(
    #         ERC20Transfer.buyer == ownership.buyer,
    #         ERC20Transfer.collection_slug == ownership.collection_slug,
    #         ERC20Transfer.event_timestamp >= ownership.buy_time,
    #         ERC20Transfer.event_timestamp <= sell_time
    #     )
    # ).first()
    avg_price_recs = session.exec(
        select(NFTEvent.price_val, NFTEvent.price_decimals, NFTEvent.price_currency).where(
            NFTEvent.contract_address == ownership.contract_address,
            NFTEvent.token_id == ownership.token_id,
            NFTEvent.event_type == 'sale',
            NFTEvent.event_timestamp <= ownership.buy_time
        )
    ).all()
    avg_prices = [(float(i.price_val) / (10 ** int(i.price_decimals))) for i in avg_price_recs]
    print(avg_prices[:5])
    if len(avg_prices) < 1:
        return 0
    avg_price = sum(avg_price_recs) / len(avg_price_recs)
    print(f'average nft price time: {time.time() - t} seconds. Price: {avg_price}')
    return avg_price or None

# def calculate_nft_roi_owner(session: Session, game_id: str, games: dict):
#     # for 
#     token_contracts = games[game_id]['erc20Tokens']
#     join_query = select(
#         NftOwnership.contract_address,
#         NftOwnership.token_id,
#         NftOwnership.buyer,
#         NftOwnership.buy_time,
#         NftOwnership.sell_time,
#         func.sum(ERC20Transfer.price / func.pow(10, ERC20Transfer.decimals)).label('total_earned')
#     ).where(
#         NftOwnership.game_id == game_id,
#         ERC20Transfer.contract_address in token_contracts,
#         ERC20Transfer.event_timestamp >= NftOwnership.buy_time,
#         ERC20Transfer.event_timestamp <= NftOwnership.sell_time
#     ).group_by(
#         NftOwnership.contract_address,
#         NftOwnership.token_id,
#         NftOwnership.buyer,
#         NftOwnership.buy_time,
#         NftOwnership.sell_time
#     )
#     rois = session.exec(join_query).all()
#     print(rois[:2])

# Function to calculate ROI for each NFT
def calculate_nft_roi(session: Session, game_id: str, games: dict):

    token_contracts = [i.lower() for i in games[game_id]['erc20Tokens']]
    # print(token_contracts)
    # Total earnings subquery
    total_earnings = (
        select(
            NftOwnership.token_id,
            NftOwnership.contract_address,
            NftOwnership.collection_slug,
            NftOwnership.buyer,
            (func.extract('epoch', func.coalesce(NftOwnership.sell_time, func.now()) - NftOwnership.buy_time) / (3600 * 24)).label('days_held'),
            ERC20Transfer.symbol,
            func.sum(ERC20Transfer.price / func.pow(10, ERC20Transfer.decimals)).label('earnings')
        )
        .join(ERC20Transfer, ERC20Transfer.buyer == NftOwnership.buyer)
        .where(
            NftOwnership.game_id == game_id,
            ERC20Transfer.contract_address.in_(token_contracts), 
            ERC20Transfer.event_timestamp.between(NftOwnership.buy_time, func.coalesce(NftOwnership.sell_time, func.now()))
        )
        .group_by(
            NftOwnership.contract_address,
            NftOwnership.token_id,
            NftOwnership.buyer,
            NftOwnership.buy_time,
            NftOwnership.sell_time,
            ERC20Transfer.symbol
        )
    ).subquery()

    # Main query to calculate ROI
    roi_query = (
        select(
            total_earnings.c.token_id,
            total_earnings.c.contract_address,
            total_earnings.c.collection_slug,
            total_earnings.c.symbol,
            (func.avg(total_earnings.c.earnings / total_earnings.c.days_held)).label('roi')
        )
        .group_by(
            total_earnings.c.token_id,
            total_earnings.c.contract_address,
            total_earnings.c.symbol,
            total_earnings.c.collection_slug
        )
    )

    # rr = session.exec(select(func.avg(total_earnings.c.earnings / total_earnings.c.days_held),
    #                          total_earnings.c.symbol,
    #                          total_earnings.c.token_id,
    #                          total_earnings.c.contract_address).group_by(
    #                              total_earnings.c.contract_address,
    #                              total_earnings.c.token_id,
    #                              total_earnings.c.symbol
    #                          )).all()
    # print(rr[:5])
    results = session.exec(roi_query).all()

    return [
        {
            'collection_slug': r.collection_slug,
            'rr_symbol': r.symbol,
            'rr_val': r.roi,
            'event_timestamp': datetime.now(pytz.UTC),
            'token_id': r.token_id,
            'contract_address': r.contract_address
        }
        for r in results
    ]

# Function to calculate and store ROI for each collection within the specified game
def calculate_and_store_collection_roi(session: Session, game_id: str):
    # Get all collections within the specified game
    collections = session.exec(
        select(Collection.opensea_slug).where(Collection.game_id == game_id)
    ).all()
    
    for collection_slug in collections:
        # Fetch ROI for all NFTs in the collection
        latest_nft_rois_subquery = (
            select(
                NFTDynamic.token_id,
                NFTDynamic.contract_address,
                NFTDynamic.rr_val,
                NFTDynamic.rr_symbol,
                NFTDynamic.event_timestamp,
                func.row_number().over(
                    partition_by = [NFTDynamic.token_id, NFTDynamic.contract_address],
                    order_by = desc(NFTDynamic.event_timestamp)
                ).label("row_num")
            )
            .where(NFTDynamic.collection_slug == collection_slug)
            .subquery()
        )

        # print(session.exec(select(latest_nft_rois_subquery.c.token_id,
        #                           latest_nft_rois_subquery.c.contract_address,
        #                           latest_nft_rois_subquery.c.rr_val,
        #                           latest_nft_rois_subquery.c.row_num)).all()[:5])
        latest_nft_rois = session.exec(
            select(
                latest_nft_rois_subquery.c.token_id,
                latest_nft_rois_subquery.c.contract_address,
                latest_nft_rois_subquery.c.event_timestamp,
                latest_nft_rois_subquery.c.rr_val,
                latest_nft_rois_subquery.c.rr_symbol
            )
            .where(latest_nft_rois_subquery.c.row_num == 1)
        ).all()
        
        # print(latest_nft_rois[:5])
        # symbol = latest_nft_rois[0].rr_symbol
        # Calculate average ROI for the collection
        if latest_nft_rois:
            avg_collection_roi = sum([i.rr_val for i in latest_nft_rois]) / len(latest_nft_rois)
        else:
            avg_collection_roi = None
        
        print('-----------------------')
        print(avg_collection_roi)
        print('-----------------------')

        # Update the collection_dynamic table
        # collection_dynamic = session.exec(
        #     select(CollectionDynamic).where(
        #         CollectionDynamic.collection_slug == collection_slug,
        #         CollectionDynamic.rr_val.is_(None)
        #         # CollectionDynamic.event_timestamp <= latest_nft_rois[0].event_timestamp
        #     ).order_by(
        #         CollectionDynamic.event_timestamp.desc()
        #     )
        # ).first()
        
        collection_dynamic = None

        # tot_avg_price = calculate_average_buy_price(session)
        
        if latest_nft_rois:
            if collection_dynamic:
                collection_dynamic.roi = avg_collection_roi
                collection_dynamic.event_timestamp = datetime.now().replace(tzinfo=pytz.UTC)
            else:
                collection_dynamic = CollectionDynamic(
                    collection_slug=collection_slug,
                    game_id=game_id,
                    rr_val=avg_collection_roi,
                    rr_symbol = latest_nft_rois[0].rr_symbol,
                    event_timestamp = datetime.now(pytz.UTC).replace(tzinfo=pytz.UTC),
                )
            
            session.add(collection_dynamic)
            session.commit()

# Main function to execute the batch processing and calculations
def main():
    batch_size = 1000
    offset = 0
    # game_id = 'YOUR_GAME_ID'  # Replace with your specific game ID
    game_id = 'pixels'
    engine = create_engine(keys.timescale_url)
    with open('app/games.json') as f:
        games = json.load(f)
    
    with Session(engine) as session:
        # calculate_nft_roi_owner(session, game_id, games)
        # while True:
        #     nft_ownerships = fetch_nft_ownership_batch(session, batch_size, offset, game_id)
        #     if not nft_ownerships:
        #         break
            
        #     nft_dynamic_entries = calculate_nft_roi(session, nft_ownerships)
            
        #     session.bulk_save_objects(nft_dynamic_entries)
        #     session.commit()
            
        #     offset += batch_size
        #     print('Batch done. NEw batch starting from offset:', offset)
        nft_rois = calculate_nft_roi(session, game_id, games)
        pprint(nft_rois[:3])
        session.bulk_insert_mappings(NFTDynamic, nft_rois)
        
        # Calculate and store ROI for each collection within the specified game
        calculate_and_store_collection_roi(session, game_id)
    return 

if __name__ == "__main__":
    main()
