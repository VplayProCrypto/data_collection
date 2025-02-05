from typing import Optional
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import (
    Column,
    Boolean,
    Integer,
    String,
    TIMESTAMP,
    ForeignKeyConstraint,
    JSON,
)


# yes
class Collection(SQLModel, table=True):
    __tablename__ = "collection"

    opensea_slug: str = Field(primary_key=True)
    game_name: Optional[str]
    game_id: Optional[str]
    name: str = Field(max_length=50)
    description: str
    owner: str
    category: str
    is_nsfw: bool = Field(default=False)
    opensea_url: Optional[str]
    project_url: Optional[str]
    wiki_url: Optional[str]
    discord_url: Optional[str]
    telegram_url: Optional[str]
    twitter_url: Optional[str]
    instagram_url: Optional[str]
    created_date: TIMESTAMP = Field(default=TIMESTAMP(timezone=True))
    updated_at: TIMESTAMP = Field(default=TIMESTAMP(timezone=True))


# yes
class CollectionDynamic(SQLModel, table=True):
    __tablename__ = "collection_dynamic"

    collection_slug: str = Field(
        primary_key=True, foreign_key="collection.opensea_slug"
    )
    game_id: Optional[str]
    total_average_price: Optional[float]
    total_supply: Optional[float]
    total_volume: Optional[float]
    total_num_owners: Optional[int]
    total_sales: Optional[float]
    total_market_cap: Optional[float]
    sales: Optional[float]
    volume: Optional[float]
    floor_price: Optional[float]
    floor_price_currency: Optional[str]
    average_price: Optional[float]
    daily_uaw: Optional[int]
    monthly_uaw: Optional[int]
    total_wallets: Optional[int]
    twitter_followers: Optional[int]
    twitter_sentiment: Optional[float]
    facebook_followers: Optional[int]
    facebook_sentiment: Optional[float]
    instagram_followers: Optional[int]
    instagram_sentiment: Optional[float]
    reddit_users: Optional[int]
    reddit_sentiment: Optional[float]
    discord_users: Optional[int]
    discord_sentiment: Optional[float]
    telegram_supergroup_size: Optional[int]
    telegram_sentiment: Optional[float]
    twitter_rank: Optional[int]
    discord_rank: Optional[int]
    telegram_rank: Optional[int]
    event_timestamp: TIMESTAMP = Field(primary_key=True)


class TwitterLeaderboard(SQLModel, table=True):
    __tablename__ = "twitter_leaderboard"

    collection_slug: str = Field(
        primary_key=True, foreign_key="collection.opensea_slug"
    )
    twitter_followers: Optional[int]
    event_timestamp: TIMESTAMP = Field(primary_key=True)


class DiscordLeaderboard(SQLModel, table=True):
    __tablename__ = "discord_leaderboard"

    collection_slug: str = Field(
        primary_key=True, foreign_key="collection.opensea_slug"
    )
    discord_server_size: Optional[int]
    event_timestamp: TIMESTAMP = Field(primary_key=True)


class TelegramLeaderboard(SQLModel, table=True):
    __tablename__ = "telegram_leaderboard"

    collection_slug: str = Field(
        primary_key=True, foreign_key="collection.opensea_slug"
    )
    telegram_supergroup_size: Optional[int]
    event_timestamp: TIMESTAMP = Field(primary_key=True)


# yes
class Contract(SQLModel, table=True):
    __tablename__ = "contract"

    collection_slug: str = Field(foreign_key="collection.opensea_slug")
    contract_address: str = Field(primary_key=True)
    chain: str = Field(primary_key=True)


class ERC20Transfer(SQLModel, table=True):
    __tablename__ = "erc20_transfers"

    buyer: str
    seller: str
    contract_address: str
    price: float
    symbol: str
    decimals: int
    transaction_hash: str = Field(primary_key=True)
    event_timestamp: TIMESTAMP = Field(primary_key=True)
    collection_slug: Optional[str]


# yes
class Fee(SQLModel, table=True):
    __tablename__ = "fee"

    collection_slug: str = Field(
        primary_key=True, foreign_key="collection.opensea_slug"
    )
    fee: float
    recipient: str = Field(primary_key=True)


# yes
class NFT(SQLModel, table=True):
    __tablename__ = "nft"

    collection_slug: str = Field(foreign_key="collection.opensea_slug")
    game_id: Optional[str]
    token_id: str = Field(primary_key=True)
    contract_address: str = Field(primary_key=True)
    token_standard: str
    name: Optional[str]
    description: Optional[str]
    image_url: Optional[str]
    metadata_url: Optional[str]
    opensea_url: Optional[str]
    updated_at: Optional[TIMESTAMP]
    is_nsfw: bool = Field(default=False)
    is_disabled: bool = Field(default=False)
    traits: Optional[dict] = Field(sa_column=Column(JSON))


# yes
class PaymentToken(SQLModel, table=True):
    __tablename__ = "payment_tokens"

    collection_slug: str = Field(
        primary_key=True, foreign_key="collection.opensea_slug"
    )
    contract_address: str = Field(primary_key=True)
    symbol: Optional[str]
    decimals: int
    chain: str


class TokenPrice(SQLModel, table=True):
    __tablename__ = "token_price"

    contract_address: str = Field(primary_key=True)
    eth_price: float
    usdt_price: float
    usdt_conversion_price: Optional[float]
    eth_conversion_price: Optional[float]
    event_timestamp: TIMESTAMP = Field(primary_key=True)


# yes
class NFTEvent(SQLModel, table=True):
    __tablename__ = "nft_events"

    transaction_hash: Optional[str]
    marketplace: Optional[str]
    marketplace_address: Optional[str]
    block_number: Optional[int]
    order_hash: Optional[str]
    event_type: Optional[str]
    token_id: str = Field(primary_key=True)
    contract_address: str = Field(primary_key=True)
    collection_slug: str
    game_id: str
    seller: str
    buyer: Optional[str]
    quantity: Optional[int] = Field(default=1)
    price_val: Optional[str]
    price_currency: Optional[str]
    price_decimals: Optional[str]
    event_timestamp: TIMESTAMP = Field(primary_key=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["token_id", "contract_address"], ["nft.token_id", "nft.contract_address"]
        ),
    )


class NFTOwnership(SQLModel, table=True):
    __tablename__ = "nft_ownership"

    buyer: Optional[str]
    seller: str
    token_id: str = Field(primary_key=True)
    contract_address: str = Field(primary_key=True)
    transaction_hash: str
    buy_time: TIMESTAMP = Field(primary_key=True)
    quantity: Optional[int] = Field(default=1)
    sell_time: Optional[TIMESTAMP]
    collection_slug: str
    game_id: str

    __table_args__ = (
        ForeignKeyConstraint(
            ["token_id", "contract_address"], ["nft.token_id", "nft.contract_address"]
        ),
    )


class NFTDynamic(SQLModel, table=True):
    __tablename__ = "nft_dynamic"

    collection_slug: str
    token_id: str = Field(primary_key=True)
    contract_address: str = Field(primary_key=True)
    rr: Optional[float]
    event_timestamp: TIMESTAMP = Field(
        default=TIMESTAMP(timezone=True), primary_key=True
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["token_id", "contract_address"], ["nft.token_id", "nft.contract_address"]
        ),
    )


class NFTOffer(SQLModel, table=True):
    __tablename__ = "nft_offers"

    order_hash: str
    event_type: Optional[str]
    token_id: str = Field(primary_key=True)
    contract_address: str = Field(primary_key=True)
    collection_slug: str
    game_id: str
    seller: str
    quantity: Optional[int] = Field(default=1)
    price_val: Optional[str]
    price_currency: Optional[str]
    price_decimals: Optional[str]
    start_date: Optional[TIMESTAMP]
    expiration_date: Optional[TIMESTAMP]
    event_timestamp: TIMESTAMP = Field(primary_key=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["token_id", "contract_address"], ["nft.token_id", "nft.contract_address"]
        ),
    )


# yes
class NFTListing(SQLModel, table=True):
    __tablename__ = "nft_listings"

    order_hash: str
    token_id: str = Field(primary_key=True)
    contract_address: str = Field(primary_key=True)
    collection_slug: str
    game_id: str
    seller: str
    price_val: Optional[str]
    price_currency: Optional[str]
    price_decimals: Optional[str]
    start_date: Optional[TIMESTAMP]
    expiration_date: Optional[TIMESTAMP]
    event_timestamp: TIMESTAMP = Field(primary_key=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["token_id", "contract_address"], ["nft.token_id", "nft.contract_address"]
        ),
    )
