from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint, ForeignKeyConstraint

class GamesMetadata(SQLModel, table=True):
    __tablename__ = "games_metadata"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = None
    opensea_slug: Optional[str] = Field(default=None, unique=True)
    description: Optional[str] = None
    image_url: Optional[str] = None
    banner_image_url: Optional[str] = None
    own: Optional[str] = None
    category: Optional[str] = None
    opensea_url: Optional[str] = None
    project_url: Optional[str] = None
    wiki_url: Optional[str] = None
    discord_url: Optional[str] = None
    telegram_url: Optional[str] = None
    twitter_username: Optional[str] = None
    instagram_username: Optional[str] = None

class GamesDynamic(SQLModel, table=True):
    __tablename__ = "games_dynamic"

    id: Optional[int] = Field(default=None, foreign_key="games_metadata.id", primary_key=True)
    total_supply: Optional[float] = None
    volume: Optional[float] = None
    sales: Optional[float] = None
    average_price: Optional[float] = None
    time_stamp: Optional[date] = None

class Contracts(SQLModel, table=True):
    __tablename__ = "contracts"

    contract_address: str = Field(primary_key=True)
    game_id: int = Field(primary_key=True, foreign_key="games_metadata.id")
    chain: Optional[str] = None

class Fees(SQLModel, table=True):
    __tablename__ = "fees"

    game_id: int = Field(primary_key=True, foreign_key="games_metadata.id")
    fee: float = Field(default=0)
    recipient: str

class NFTs(SQLModel, table=True):
    __tablename__ = "nfts"

    contract_address: str = Field(primary_key=True)
    token_id: str = Field(primary_key=True)
    opensea_slug: Optional[str] = Field(default=None, foreign_key="games_metadata.opensea_slug")
    token_standard: Optional[str] = None
    descp: Optional[str] = None
    image_url: Optional[str] = None
    metadata_url: Optional[str] = None
    opensea_url: Optional[str] = None
    updated_at: Optional[date] = None
    traits: Optional[dict] = None

class NFTListing(SQLModel, table=True):
    __tablename__ = "nft_listing"

    order_hash: str = Field(primary_key=True)
    token_id: Optional[str] = None
    contract_address: Optional[str] = None
    current_currency: Optional[str] = None
    offerer: Optional[str] = None
    current_price_val: Optional[float] = None
    current_price_decimals: Optional[int] = None
    current_price_symbol: Optional[str] = None

class Events(SQLModel, table=True):
    __tablename__ = "events"

    order_hash: str = Field(primary_key=True)
    event_type: Optional[str] = None
    seller: Optional[str] = None
    buyer: Optional[str] = None
    event_timestamp: Optional[date] = None
    token_id: Optional[str] = None
    contract_address: Optional[str] = None

    __table_args__ = (
        ForeignKeyConstraint(
            ["contract_address", "token_id"],
            ["nfts.contract_address", "nfts.token_id"]
        ),
    )