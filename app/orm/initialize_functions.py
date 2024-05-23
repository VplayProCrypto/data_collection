import os
from sqlmodel import create_engine, Session
from api_requests.opensea import OpenSea
from api_requests.dappradar import get_uaw_from_dappradar
from api_requests.discord import get_guild_member_count
from api_requests.twitter import get_user_public_metrics
from api_requests.alchemy import get_nft_sales, Alchemy
from api_requests.etherscan import EtherScan
from models import CollectionDynamic

# engine = create_engine(os.environ.get("TIMESCALE_URL"))


def initialize_db(sql_files):
    with Session(engine) as session:
        for sql_file in sql_files:
            with open(sql_file, "r") as file:
                sql = file.read()
                session.execute(sql)
        session.commit()


# if no data exists mark followers as -1
# for now since we can't get social data we need to manually input it when updating
# no sentiment for now just rank them, done in triggers
def add_collection_dynamic(
    collection_slug: str,
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
        average_price=collection_response["average_price"],
        monthly_uaw=get_uaw_from_dappradar("9495", "30d"),
        daily_uaw=get_uaw_from_dappradar("9495", "24h"),
        discord_users=discord_users,
        discord_sentiment="-1",
        twitter_followers=twitter_followers,
        twitter_sentiment="-1",
        telegram_supergroup_size=telegram_supergroup_size,
        telegram_sentiment="-1",
        facebook_followers=facebook_followers,
        facebook_sentiment="-1",
        instagram_followers=instagram_followers,
        instagram_sentiment="-1",
        reddit_users=reddit_users,
        reddit_sentiment="-1",
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


from sqlalchemy.orm import sessionmaker


def add_game(collection_slug: str, num_pages: int, after_date: datetime) -> None:
    engine = create_engine(os.environ.get("TIMESCALE_URL"))
    opensea = OpenSea()
    alchemy = Alchemy()
    etherscan = EtherScan()
    # all tables lead to collection
    collection_response = opensea.get_collection_stats(collection_slug)
    initialize_collection(
        collection_response,
        engine,
    )

    Session = sessionmaker(bind=dbengine)
    session = Session()

    opensea.save_all_nfts_for_collection(session, collection_slug)
    opensea.save_all_nft_listings_for_collection(session, collection_slug)
    alchemy.save_all_nft_sales_for_contract(
        db=session,
        contract_address=collection_response["collection"]["contract_address"],
        collection_slug=collection_slug,
        game_id=collection_response["game_id"],
    )
    alchemy.save_all_nft_transfers_for_contract(
        db=session,
        contract_address=collection_response["collection"]["contract_address"],
        collection_slug=collection_slug,
        game_id=collection_response["game_id"],
    )
    etherscan.save_erc20_transfers(
        db=session,
        contract_address=collection_response["collection"]["contract_address"],
        after_date=after_date,
        collection_slug=collection_slug,
    )

    # TODO NFT OWNERSHIP
