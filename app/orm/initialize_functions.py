import os
from sqlmodel import create_engine, Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from datetime import datetime
import json
import logging


from .models import CollectionDynamic
from app.api_requests.dappradar import get_uaw_from_dappradar
from app.api_requests.discord import get_guild_member_count
from app.api_requests.twitter import get_user_public_metrics
from app.api_requests.alchemy import Alchemy
from app.api_requests.etherscan import EtherScan
from app.api_requests.opensea import OpenSea
from app.orm.postgres_injector_orm import Injector
import app.keys as keys
from app.celery_config import celery_app as app
from app.utils import load_collections_from_file

from app.logging_config import setup_logging

setup_logging()

# engine = create_engine(os.environ.get("TIMESCALE_URL"))
engine = create_engine(keys.timescale_url)
# opensea = OpenSea()

def initialize_db(sql_files):
    with Session(engine) as session:
        for sql_file in sql_files:
            with open(sql_file, "r") as file:
                sql = file.read()
                session.execute(sql)
        session.commit()


# TODO compare follower count to db for how it ranks in percentage
def rank_social(site: str, followers: int) -> float:
    return 0.0


# if no data exists mark followers as -1
# for now since we can't get social data we need to manually input it when updating
def add_collection_dynamic(
    collection_slug: str,
    opensea: OpenSea,
    twitter_followers=-1,
    facebook_followers=-1,
    instagram_followers=-1,
    reddit_users=-1,
    discord_users=-1,
    telegram_supergroup_size=-1,
) -> None:
    collection_stats = opensea.get_collection_stats(collection_slug)
    collection_dynamic = CollectionDynamic(
        game_id=collection_stats["game_id"],
        total_average_price=collection_stats["total_average_price"],
        total_supply=collection_stats["total_supply"],
        total_volume=collection_stats["total_volume"],
        total_num_owners=collection_stats["total_num_owners"],
        total_wallets=collection_stats["total_num_owners"],
        total_sales=collection_stats["total_sales"],
        sales=collection_stats["sales"],
        volume=collection_stats["volume"],
        floor_price=collection_stats["floor_price"],
        floor_price_currency=collection_stats["floor_price_currency"],
        average_price=collection_stats["average_price"],
        monthly_uaw=get_uaw_from_dappradar("9495", "30d"),
        daily_uaw=get_uaw_from_dappradar("9495", "24h"),
        discord_users=discord_users,
        discord_sentiment=rank_social(
            "discord",
            discord_users,
            # get_guild_member_count(collection_response["collection"]["discord_url"]),
        ),
        twitter_followers=twitter_followers,
        twitter_sentiment=rank_social(
            "twitter",
            twitter_followers,
            # get_user_public_metrics(collection_response["collection"]["twitter_url"])["followers"],
        ),
        telegram_supergroup_size=telegram_supergroup_size,
        telegram_sentiment=rank_social(
            "telegram",
            telegram_supergroup_size,
            # get_supergroup_member_count(collection_response["collection"]["telegram_url"]),
        ),
        facebook_followers=facebook_followers,
        facebook_sentiment=rank_social(
            "facebook",
            facebook_followers,
            # get_user_public_metrics(collection_response["collection"]["facebook_url"])["followers"],
        ),
        instagram_followers=instagram_followers,
        instagram_sentiment=rank_social(
            "instagram",
            instagram_followers,
            # get_user_public_metrics(collection_response["collection"]["instagram_url"])["followers"],
        ),
        reddit_users=reddit_users,
        reddit_sentiment=rank_social(
            "reddit",
            reddit_users,
            # get_user_public_metrics(collection_response["collection"]["reddit_url"])["followers"],
        ),
    )


def initialize_collection(collection_response, dbengine) -> None:
    Session = sessionmaker(bind=dbengine)
    session = Session()

    session.add(collection_response["collection"])
    session.add_all(collection_response["fees"])
    session.add_all(collection_response["contracts"])
    session.add_all(collection_response["payment_tokens"])

    session.commit()
    session.close()




def add_game(collection_slug: str, num_pages: int = 10000) -> None:
    # engine = create_engine(os.environ.get("TIMESCALE_URL"))
    with open('app/games.json') as f:
        games = json.loads(f.read())
    engine = create_engine(keys.timescale_url)
    opensea = OpenSea()
    alchemy = Alchemy()
    etherscan = EtherScan()
    # all tables lead to collection
    collection_response = opensea.get_collection_new(collection_slug)
    contracts = [i.contract_address for i in collection_response['contracts']]
    after_date = collection_response['collection'].created_date
    # print('-'*100)
    # print('contracts:', contracts)
    # print('after date:', after_date)
    initialize_collection(
        collection_response,
        engine,
    )
    # print('contracts:', contracts)
    # print('after date:', after_date)
    # print('-'*100)

    # Session = sessionmaker(bind=engine)
    # session = Session()

    # with Session(engine) as session:
    #     opensea.save_all_nfts_for_collection(session, collection_slug, pages = num_pages)
    # with Session(engine) as session:
    #     opensea.save_all_nft_listings_for_collection(session, collection_slug)
    # # print('-'*100)
    # for contract in contracts:
    #     # print(contract)
    #     with Session(engine) as session:
    #         alchemy.save_all_nft_sales_for_contract(
    #             db=session,
    #             contract_address=contract,
    #             collection_slug=collection_slug,
    #             game_id=collection_response["game_id"],
    #         )
    #     with Session(engine) as session:
    #         alchemy.save_all_nft_transfers_for_contract(
    #             db=session,
    #             contract_address=contract,
    #             collection_slug=collection_slug,
    #             game_id=collection_response["game_id"],
    #         )
    # print('-'*100)
    
    for erc_contract in games[collection_response['game_id']]['erc20Tokens']:
        total_recs_saved = 0
        while True:
            transfers = etherscan.get_erc20_transfers_new(erc_contract, after_date, collection_slug)
            print('-'*50)
            print('transaction hash:', transfers[41].transaction_hash, 'time:', transfers[37].event_timestamp)
            print('transaction hash:', transfers[44].transaction_hash, 'time:', transfers[40].event_timestamp)
            print('-'*50)
            with Session(engine) as session:
                if transfers:
                    after_date = transfers[-1].event_timestamp
                    for i in transfers:
                        try:
                            session.add(i)
                            total_recs_saved += 1
                        except Exception as e:
                            session.rollback()
                            print('error while adding record. Skipping')
                            print(f'transaction hash: {i.transaction_hash}')
                            print('error:', e)
                    try:
                        session.commit()
                    except Exception as e:
                        session.rollback()
                        print('error:', e)
                        break
                    print('Added records:', total_recs_saved)
                else:
                    break
                # etherscan.save_erc20_transfers(
                #     db=session,
                #     contract_address=erc_contract,
                #     after_date=after_date,
                #     collection_slug=collection_slug,
                # )

    # TODO NFT OWNERSHIP

# @app.task
def add_collection(collection_slug: str):
    injector = Injector()
    
    game_id = injector.mapper._get_game_id(collection_slug)
    injector.insert_collection(collection_slug=collection_slug)
    injector.insert_nfts(collection_slug=collection_slug)
    injector.insert_nft_events(collection_slug=collection_slug, event_type='sale')
    injector.insert_nft_events(collection_slug=collection_slug, event_type='transfer')
    injector.insert_erc20_transfers(collection_slug)
    injector.calculate_and_store_rr(game_id)
    del injector

logger = logging.getLogger(__name__)
# logging.basicConfig(level = logging.DEBUG)

# @app.task
def add_all_collections(file_path: str):
    # collections = ['pixels-farm', 'mavia-land', 'decentraland']
    logger.debug('loading collection names')
    collections = load_collections_from_file(file_path)
    logger.debug('loaded collection names')
    print("collections", collections)
    # with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
    #     futures = [executor.submit(add_collection, collection) for collection in collections]
    #     concurrent.futures.wait(futures)
    # collections = ['decentraland']
    for c in collections:
        add_collection(c)

def init_db_new():
    sql_dir = os.path.join('db', 'raw_sql')
    sql_files = [os.path.join(sql_dir, i) for i in ['drop_tables.sql', 'tables.sql', 'hypertables.sql', 'triggers.sql', 'indexes.sql']]
    # sql_files = [os.path.join(sql_dir, i) for i in ['indexes.sql']]
    with Session(engine) as session:
        session.exec(text('CREATE EXTENSION IF NOT EXISTS vector'))
        for sql_file in sql_files:
            with open(sql_file, "r") as file:
                sql = file.read()
                session.exec(text(sql))
        session.commit()
    add_all_collections('games.json')


def main():
    init_db_new()

if __name__ == '__main__':
    main()