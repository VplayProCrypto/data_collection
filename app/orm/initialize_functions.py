import os
from sqlmodel import create_engine, Session
from api_requests.opensea import OpenSea
from api_requests.dappradar import get_uaw_from_dappradar
from api_requests.discord import get_guild_member_count
from api_requests.twitter import get_user_public_metrics
from models import CollectionDynamic

engine = create_engine(os.environ.get("TIMESCALE_URL"))


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


def add_game(collection_slug: str, num_pages: int) -> None:
    opensea = OpenSea()
    collection_response = opensea.get_collection(collection_slug)
    nft_response = opensea.get_nfts_for_collection(collection_slug, num_pages)
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
        discord_sentiment=rank_social(
            "discord",
            get_guild_member_count(collection_response["collection"]["discord_url"]),
        ),
        twitter_sentiment=rank_social(
            "twitter",
            get_user_public_metrics(collection_response["collection"]["twitter_url"])[
                "followers"
            ],
        ),
        telegram_sentiment=rank_social(
            "telegram",
            get_supergroup_member_count(
                collection_response["collection"]["telegram_url"]
            ),
        ),
        # TODO add others later
    )
    # TODO NFT Listings, Events, -> get corresponding NFTs
