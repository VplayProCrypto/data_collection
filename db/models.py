from typing import List, Set
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

class Base(DeclarativeBase):
    pass

class Collection(Base):
    __tablename__ = "collection"
    # id: Mapped[int] = mapped_column(primary_key=True)
    opensea_slug: Mapped[str] = mapped_column(primary_key = True)
    name: Mapped[str] = mapped_column(String(50))
    game_name: Mapped[Optional[str]]
    game_id: Mapped[Optional[str]]
    description: Mapped[str]
    owner: Mapped[str]
    category: Mapped[str]
    is_nsfw: Mapped[bool]
    opensea_url: Mapped[Optional[str]]
    project_url: Mapped[Optional[str]]
    wiki_url: Mapped[Optional[str]]
    discord_url: Mapped[Optional[str]]
    telegram_url: Mapped[Optional[str]]
    twitter_url: Mapped[Optional[str]]
    instagram_url: Mapped[Optional[str]]
    created_date: Mapped[datetime]
    updated_at: Mapped[datetime] = mapped_column(default = datetime.now)
    fees: Mapped[List["Fee"]] = relationship(
        back_populates="collection", cascade="all, delete-orphan"
    )
    contracts: Mapped[List["Contract"]] = relationship(
        back_populates="collection", cascade="all, delete-orphan"
    )
    tokens: Mapped[List["PaymentTokens"]] = relationship(
        back_populates = "collection", cascade = "all, delete-orphan"
    )
    nfts: Mapped[List["Nft"]] = relationship(
        back_populates="collection", cascade="all, delete-orphan"
    )
    def __repr__(self) -> str:
        return f"Collection(id={self.opensea_slug!r}, name={self.name!r}, slug={self.opensea_slug!r})"

class CollectionDynamic(Base):
    __tablename__ = "collection_dynamic"
    collection_slug: Mapped[str] = mapped_column(ForeignKey("collection.opensea_slug"), primary_key=True)
    total_average_price: Mapped[float] = mapped_column(nullable=True)
    total_supply: Mapped[float] = mapped_column(nullable=True)
    game_id: Mapped[Optional[str]]
    total_volume: Mapped[float] = mapped_column(nullable=True)
    total_num_owners: Mapped[int] = mapped_column(nullable=True)
    total_sales: Mapped[float] = mapped_column(nullable=True)
    total_market_cap: Mapped[float] = mapped_column(nullable=True)
    sales: Mapped[float] = mapped_column(nullable=True)
    volume: Mapped[float] = mapped_column(nullable=True)
    floor_price: Mapped[float] = mapped_column(nullable=True)
    floor_price_currency: Mapped[str] = mapped_column(nullable=True)
    average_price: Mapped[float] = mapped_column(nullable=True)
    uaw: Mapped[Optional[int]]
    total_wallets: Mapped[Optional[int]]
    facebook_sentiment: Mapped[Optional[float]]
    twitter_sentiment: Mapped[Optional[float]]
    instagram_sentiment: Mapped[Optional[float]]
    reddit_sentiment: Mapped[Optional[float]]
    discord_sentiment: Mapped[Optional[float]]
    event_timestamp: Mapped[datetime] = mapped_column(primary_key=True)

class PaymentTokens(Base):
    __tablename__ = "payment_tokens"
    collection_slug: Mapped[str] = mapped_column(ForeignKey("collection.opensea_slug"), primary_key=True)
    contract_address: Mapped[str] = mapped_column(primary_key = True)
    chain: Mapped[str] = mapped_column(default = "ethereum", primary_key = True)
    symbol: Mapped[str] = mapped_column(nullable=True)
    decimals: Mapped[int]
    collection: Mapped["Collection"] = relationship(
        back_populates="tokens"
    )

class Contract(Base):
    __tablename__ = "contract"
    collection_slug: Mapped[str] = mapped_column(ForeignKey("collection.opensea_slug"))
    contract_address: Mapped[str] = mapped_column(primary_key = True)
    chain: Mapped[str] = mapped_column(default = "ehtereum", primary_key = True)
    collection: Mapped["Collection"] = relationship(
        back_populates="contracts"
    )
    def __repr__(self) -> str:
        return f"Contract(collection={self.collection_slug!r}, contract_address={self.contract_address!r}, chain={self.chain!r})"

class Fee(Base):
    __tablename__ = "fee"
    collection_slug: Mapped[str] = mapped_column(ForeignKey("collection.opensea_slug"), primary_key = True)
    fee: Mapped[float]
    recipient: Mapped[str]
    collection: Mapped["Collection"] = relationship(
        back_populates="fees"
    )

class Nft(Base):
    __tablename__ = "nft"
    collection_slug: Mapped[str] = mapped_column(ForeignKey("collection.opensea_slug"))
    token_id: Mapped[str] = mapped_column(primary_key=True)
    contract_address: Mapped[str] = mapped_column(primary_key=True)
    token_standard: Mapped[str]
    game_id: Mapped[Optional[str]]
    name: Mapped[str]
    description: Mapped[str]
    image_url: Mapped[str]
    metadata_url: Mapped[str]
    opensea_url: Mapped[str]
    updated_at: Mapped[datetime] = mapped_column(default = datetime.now)
    traits = mapped_column(JSONB, nullable = True)
    is_nsfw: Mapped[bool]
    is_disabled: Mapped[bool]
    # events: Mapped[List["NftEvent"]] = relationship(
    #     back_populates = "nft"
    # )
    collection: Mapped["Collection"] = relationship(
        back_populates="nfts"
    )
    # transfers: Mapped[List["NftTransfer"]] = relationship(
    #     back_populates = "nft"
    # )
    # listings: Mapped[List["NftListing"]] = relationship(
    #     back_populates = "nft"
    # )
    
    def __repr__(self) -> str:
        return f"Nft(id={self.id!r}, email_address={self.chain!r})"

class NftEvent(Base):
    __tablename__ = "nft_events"
    transaction_hash: Mapped[str]
    event_type: Mapped[Optional[str]]
    token_id: Mapped[str] = mapped_column(primary_key = True)
    contract_address: Mapped[str] = mapped_column(primary_key = True)
    game_id: Mapped[Optional[str]]
    collection_slug: Mapped[str]
    seller: Mapped[str]
    buyer: Mapped[str]
    price_val: Mapped[str]
    price_currency: Mapped[str]
    price_decimals: Mapped[int]
    quantity: Mapped[int] = mapped_column(default=1)
    start_date: Mapped[Optional[datetime]]
    expiration_date: Mapped[Optional[datetime]]
    event_timestamp: Mapped[str] = mapped_column(default = datetime.now, primary_key = True)
    # nft: Mapped["Nft"] = relationship(
    #     back_populates = "events"
    # )

# class NftListing(Base):
#     __tablename__ = "nft_listing"
#     transaction_hash: Mapped[str] = mapped_column(primary_key = True)
#     token_id: Mapped[str]
#     contract_address: Mapped[str]
#     seller: Mapped[str]
#     collection_slug: Mapped[str]
#     price_val: Mapped[str]
#     price_currnecy: Mapped[str]
#     price_symbol: Mapped[str]
#     start_date: Mapped[datetime]
#     expiration_date: Mapped[Optional[datetime]]
#     event_timestamp: Mapped[str] = mapped_column(default = datetime.now)
#     nft: Mapped["Nft"] = relationship(
#         back_populates = "listings"
#     )

class NftOwnership(Base):
    __tablename__ = "nft_ownership"
    buyer: Mapped[str]
    seller: Mapped[str]
    token_id: Mapped[str] = mapped_column(primary_key = True)
    contract_address: Mapped[str] = mapped_column(primary_key = True)
    game_id: Mapped[Optional[str]]
    transaction_hash: Mapped[str]
    buy_time: Mapped[datetime] = mapped_column(primary_key = True)
    sell_time: Mapped[datetime]
    collection_slug: Mapped[str]

class Erc20Transfer(Base):
    __tablename__ = "erc20_transfers"
    buyer: Mapped[str]
    seller: Mapped[str]
    contract_address: Mapped[str]
    price: Mapped[float]
    symbol: Mapped[str]
    decimals: Mapped[int]
    transaction_hash: Mapped[str] = mapped_column(primary_key = True)
    event_timestamp: Mapped[datetime]
    collection_slug: Mapped[Optional[str]]

class TokenPrice(Base):
    __tablename__ = "token_price"
    contract_address: Mapped[str] = mapped_column(primary_key=True)
    eth_price: Mapped[float]
    usdt_price: Mapped[float]
    usdt_conversion_price: Mapped[Optional[float]]
    eth_conversion_price: Mapped[Optional[float]]
    event_timestamp: Mapped[datetime] = mapped_column(primary_key=True)

class NftDynamic:
    __tablename__ = "nft_dynamic"
    token_id: Mapped[str] = mapped_column(primary_key = True)
    contract_address: Mapped[str] = mapped_column(primary_key = True)
    collection_slug: Mapped[str]
    rr: Mapped[Optional[float]]
    event_timestamp: Mapped[datetime]

def get_metadata():
    return Base.metadata