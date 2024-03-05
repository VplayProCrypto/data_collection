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
    fees: Mapped[List["Fee"]] = relationship(
        back_populates="collection_slug", cascade="all, delete-orphan"
    )
    contracts: Mapped[List["Contract"]] = relationship(
        back_populates="collection_slug", cascade="all, delete-orphan"
    )
    tokens: Mapped[List["PaymentTokens"]] = relationship(
        back_populates = "collection_slug", cascade = "all, delete-orphan"
    )
    nfts: Mapped[List["Nft"]] = relationship(
        back_populates="opensea_slug", cascade="all, delete-orphan"
    )
    def __repr__(self) -> str:
        return f"Collection(id={self.id!r}, name={self.name!r}, slug={self.opensea_slug!r})"

class CollectionDynamic(Base):
    __tablename__ = "collection_dynamic"
    collection_slug: Mapped[str] = mapped_column(ForeignKey("collection.opensea_slug"), primary_key=True)
    total_average_price: Mapped[float] = mapped_column(nullable=True)
    total_supply: Mapped[float] = mapped_column(nullable=True)
    total_volume: Mapped[float] = mapped_column(nullable=True)
    total_num_owners: Mapped[int] = mapped_column(nullable=True)
    total_sales: Mapped[float] = mapped_column(nullable=True)
    total_market_cap: Mapped[float] = mapped_column(nullable=True)
    sales: Mapped[float] = mapped_column(nullable=True)
    volume: Mapped[float] = mapped_column(nullable=True)
    floor_price: Mapped[float] = mapped_column(nullable=True)
    floor_price_currency: Mapped[str] = mapped_column(nullable=True)
    average_price: Mapped[float] = mapped_column(nullable=True)
    event_timestamp: Mapped[datetime] = mapped_column(primary_key=True)

class PaymentTokens(Base):
    __tablename__ = "payment_tokens"
    collection_slug: Mapped[str] = mapped_column(ForeignKey("collection.opensea_slug"), primary_key=True)
    contract_address: Mapped[str] = mapped_column(primary_key = True)
    chain: Mapped[str] = mapped_column(default = "ethereum", primary_key = True)
    symbol: Mapped[str] = mapped_column(nullable=True)
    decimals: Mapped[int]

class Contract(Base):
    __tablename__ = "contract"
    collection_slug: Mapped[str] = mapped_column(ForeignKey("collection.opensea_slug"))
    contract_address: Mapped[str] = mapped_column(primary_key = True)
    chain: Mapped[str] = mapped_column(default = "ehtereum")
    def __repr__(self) -> str:
        return f"Contract(collection={self.collection_id!r}, contract_address={self.contract_address!r}, chain={self.chain!r})"

class Fee(Base):
    __tablename__ = "fee"
    collection_slug: Mapped[str] = mapped_column(ForeignKey("collection.opensea_slug"), primary_key = True)
    fee: Mapped[float]
    recipient: Mapped[str]

class Nft(Base):
    __tablename__ = "nft"
    opensea_slug: Mapped[str] = mapped_column(ForeignKey("collection.opensea_slug"))
    token_id: Mapped[str] = mapped_column(primary_key=True)
    contract_address: Mapped[str] = mapped_column(primary_key=True)
    token_standard: Mapped[str]
    name: Mapped[str]
    descp: Mapped[str]
    image_url: Mapped[str]
    metadata_url: Mapped[str]
    opensea_url: Mapped[str]
    updated_at: Mapped[datetime]
    traits = mapped_column(JSONB)
    is_nsfw: Mapped[bool]
    is_disabled: Mapped[bool]
    sales: Mapped[List["NftSale"]] = relationship(
        back_populates = "nft"
    )
    transfers: Mapped[List["NftTransfer"]] = relationship(
        back_populates = "nft"
    )
    listings: Mapped[List["NftListing"]] = relationship(
        back_populates = "nft"
    )
    
    def __repr__(self) -> str:
        return f"Nft(id={self.id!r}, email_address={self.chain!r})"

class NftSale(Base):
    __tablename__ = "nft_sale"
    transaction_hash: Mapped[str] = mapped_column(primary_key = True)
    token_id: Mapped[str]
    contract_address: Mapped[str]
    buyer: Mapped[str]
    seller: Mapped[str]
    collection_slug: Mapped[str]
    price_val: Mapped[str]
    price_currnecy: Mapped[str]
    price_symbol: Mapped[str]
    event_timestamp: Mapped[str] = mapped_column(default = datetime.now)
    nft: Mapped["Nft"] = relationship(
        back_populates = "sales"
    )

class NftTransfer(Base):
    __tablename__ = "nft_transfer"
    transaction_hash: Mapped[str] = mapped_column(primary_key = True)
    token_id: Mapped[str]
    contract_address: Mapped[str]
    buyer: Mapped[str]
    seller: Mapped[str]
    collection_slug: Mapped[str]
    event_timestamp: Mapped[str] = mapped_column(default = datetime.now)
    nft: Mapped["Nft"] = relationship(
        back_populates = "transfers"
    )

class NftListing(Base):
    __tablename__ = "nft_listing"
    transaction_hash: Mapped[str] = mapped_column(primary_key = True)
    token_id: Mapped[str]
    contract_address: Mapped[str]
    seller: Mapped[str]
    collection_slug: Mapped[str]
    price_val: Mapped[str]
    price_currnecy: Mapped[str]
    price_symbol: Mapped[str]
    start_date: Mapped[datetime]
    expiration_date: Mapped[Optional[datetime]]
    event_timestamp: Mapped[str] = mapped_column(default = datetime.now)
    nft: Mapped["Nft"] = relationship(
        back_populates = "listings"
    )

class NftOwnership(Base):
    __tablename__ = "nft_ownership"
    buyer: Mapped[str]
    seller: Mapped[str]
    token_id: Mapped[str]
    contract_address: Mapped[str]
    transaction_hash: Mapped[str] = mapped_column(primary_key = True)
    buy_time: Mapped[datetime]
    sell_time: Mapped[datetime]

class Erc20Transfer(Base):
    __tablename__ = "erc20_transfers"
    buyer: Mapped[str]
    seller: Mapped[str]
    contract_address: Mapped[str]
    price: Mapped[float]
    symbol: Mapped[str]
    decimals: Mapped[int]
    transaction_hash: Mapped[str] = mapped_column(primary_key = True)

class TokenPrice(Base):
    __tablename__ = "token_price"
    contract_address: Mapped[str] = mapped_column(primary_key=True)
    eth_price: Mapped[float]
    usdt_price: Mapped[float]
    usdt_conversion_price: Mapped[Optional[float]]
    eth_conversion_price: Mapped[Optional[float]]
    event_timestamp: Mapped[datetime] = mapped_column(primary_key=True)

def get_metadata():
    return Base.metadata