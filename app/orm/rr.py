import time
import json
from pprint import pprint
from logging import Logger
from datetime import datetime, timezone
from sqlalchemy import desc, Float, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session as alchemy_session
from sqlmodel import SQLModel, create_engine, select, func, Session, cast

# from pyspark.sql import SparkSession
# from pyspark.sql.functions import col, explode, udf
# from pyspark.sql.types import StringType, MapType
# from pyspark.ml.clustering import KMeans
# from pyspark.ml.feature import VectorAssembler

import app.keys as keys
from app.orm.transform import Mapper
from app.orm.models import NFT, NFTDynamic, NFTEvent, Collection, CollectionDynamic, NftOwnership, ERC20Transfer

logger = Logger(__name__)

def sell_time_correction(ownership: NftOwnership):
    if ownership.sell_time:
        sell_time = ownership.sell_time
    else:
        sell_time = datetime.now(timezone.utc)
    return sell_time
    
# Function to fetch NFT ownership data in batches
def fetch_nft_ownership_batch(session: Session, batch_size: int, offset: int, game_id: str) -> list[NftOwnership]:
    return session.exec(
        select(NftOwnership).where(NftOwnership.game_id == game_id).limit(batch_size).offset(offset)
    ).all()

# Function to calculate average buy price for each NFT by each wallet
def calculate_average_buy_price(session: Session, ownership: NftOwnership) -> float:
    t = time.time()
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

def preprocess_nft_data(nft_data: list[NFT]):
    return [i.model_dump() for i in nft_data]

def cluster_nft(session: alchemy_session, game_id: str):
    t = time.time()
    # spark: SparkSession = (
    #     SparkSession.builder
    #     .appName('NFT Clustering')
    #     .config('spark.jars.packages', 'org.postgresql:postgresql:42.2.0')
    #     .getOrCreate()
    # )

    # df = (
    #     spark.read
    #     .format('jdbc')
    #     .option('url')
    # )
    nfts_with_trait = session.execute(
        select(NFT.contract_address, NFT.token_id, NFT.traits)
        .where(NFT.game_id == game_id)
        .where(NFT.traits.isnot(None))
    ).scalars().all()



# Function to calculate ROI for each NFT
def calculate_nft_roi(session: alchemy_session, game_id: str, games: dict):
    t = time.time()
    token_contracts = [i.lower() for i in games[game_id]['erc20Tokens']]
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

    results = session.execute(roi_query).all()
    logger.info(f"NFT ROIs Calculated. Time taken {time.time() - t}")
    return [
        {
            'collection_slug': r.collection_slug,
            'rr_symbol': r.symbol,
            'rr_val': r.roi,
            'event_timestamp': datetime.now(timezone.utc),
            'token_id': r.token_id,
            'contract_address': r.contract_address
        }
        for r in results
    ]

def calculate_collection_sale_stats(session: Session, collection_slug: str):
    res = session.exec(
        select(
            func.count("*"),
            func.sum(
                cast(NFTEvent.price_val, Float) / func.pow(10, 18)
            ),
            func.avg(
                cast(NFTEvent.price_val, Float) / func.pow(10, 18)
            )
        ).where(
            NFTEvent.collection_slug == collection_slug
            ).where(
                NFTEvent.event_type == 'sale'   
            )
    ).first()
    sales, volume, average_sales = res
    return res

# Function to calculate and store ROI for each collection within the specified game
def calculate_and_store_collection_roi(session: Session, game_id: str, mapper: Mapper):
    # Get all collections within the specified game
    collections = session.execute(
        select(Collection.opensea_slug).where(Collection.game_id == game_id)
    ).all()
    
    for collection_slug in collections:
        # Fetch ROI for all NFTs in the collection
        # latest_nft_rois_subquery = (
        #     select(
        #         NFTDynamic.token_id,
        #         NFTDynamic.contract_address,
        #         NFTDynamic.rr_val,
        #         NFTDynamic.rr_symbol,
        #         NFTDynamic.event_timestamp,
        #         func.row_number().over(
        #             partition_by = [NFTDynamic.token_id, NFTDynamic.contract_address],
        #             order_by = desc(NFTDynamic.event_timestamp)
        #         ).label("row_num")
        #     )
        #     .where(NFTDynamic.collection_slug == collection_slug)
        #     .subquery()
        # )

        # latest_nft_rois = session.exec(
        #     select(
        #         latest_nft_rois_subquery.c.token_id,
        #         latest_nft_rois_subquery.c.contract_address,
        #         latest_nft_rois_subquery.c.event_timestamp,
        #         latest_nft_rois_subquery.c.rr_val,
        #         latest_nft_rois_subquery.c.rr_symbol
        #     )
        #     .where(latest_nft_rois_subquery.c.row_num == 1)
        # ).all()

        t = time.time()
        with session.begin():
            collection_rois = session.execute(
                select(
                    NFTDynamic.collection_slug,
                    NFTDynamic.rr_symbol,
                    func.avg(NFTDynamic.rr_val)
                )
                .where(NFTDynamic.collection_slug == collection_slug)
                .group_by(NFTDynamic.collection_slug, NFTDynamic.rr_symbol)
            ).first()
            logger.info(f"Collection ROI calculated for game {game_id}. Time taken {time.time() - t}")

            if not collection_rois:
                print(f"No collection roi present for {collection_slug}")
                return
            _, rr_symbol, avg_collection_roi = collection_rois
            # Calculate average ROI for the collection
            # if latest_nft_rois:
            #     avg_collection_roi = sum([i.rr_val for i in latest_nft_rois]) / len(latest_nft_rois)
            # else:
            #     avg_collection_roi = None
            
            # print('-----------------------')
            # print(avg_collection_roi)
            # print('-----------------------')

            collection_dynamic = None

            # tot_avg_price = calculate_average_buy_price(session)
            
            total_sales, total_volume, total_average_price = calculate_collection_sale_stats(session, collection_slug)
            other_stats = mapper.get_collection_stats(collection_slug)
            if collection_rois:
                if collection_dynamic:
                    collection_dynamic.roi = avg_collection_roi
                    collection_dynamic.event_timestamp = datetime.now().replace(tzinfo=timezone.utc)
                else:
                    collection_dynamic = CollectionDynamic(
                        collection_slug=collection_slug,
                        game_id=game_id,
                        rr_val=avg_collection_roi,
                        # rr_symbol = latest_nft_rois[0].rr_symbol,
                        rr_symbol = rr_symbol,
                        total_average_price=total_average_price,
                        total_sales=total_sales,
                        total_volume=total_volume,
                        total_market_cap=other_stats['market_cap'],
                        floor_price=other_stats['floor_price'],
                        floor_price_currency=other_stats['floor_price_currency'],
                        total_num_owners=other_stats['num_owners'],
                        event_timestamp = datetime.now().replace(tzinfo=timezone.utc),
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
    with open('games.json') as f:
        games = json.load(f)
    
    with Session(engine) as session:
        nft_rois = calculate_nft_roi(session, game_id, games)
        pprint(nft_rois[:3])
        session.bulk_insert_mappings(NFTDynamic, nft_rois)
        
        # Calculate and store ROI for each collection within the specified game
        calculate_and_store_collection_roi(session, game_id)
    return 

if __name__ == "__main__":
    main()
