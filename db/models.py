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
    opensea_slug: Mapped[str] = mapped_column(unique=True)
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
        back_populates="collection_id", cascade="all, delete-orphan"
    )
    contracts: Mapped[List["Contract"]] = relationship(
        back_populates="collection_id", cascade="all, delete-orphan"
    )
    nfts: Mapped[List["Nft"]] = relationship(
        back_populates="collection_id", cascade="all, delete-orphan"
    )
    def __repr__(self) -> str:
        return f"Collection(id={self.id!r}, name={self.name!r}, slug={self.opensea_slug!r})"

class Contract(Base):
    __tablename__ = "contract"
    collection_slu: Mapped[str] = mapped_column(ForeignKey("collection.collection"))
    contract_address: Mapped[str] = mapped_column(unique = True)
    chain: Mapped[str]
    def __repr__(self) -> str:
        return f"Contract(collection={self.collection_id!r}, contract_address={self.contract_address!r}, chain={self.chain!r})"

class Fee(Base):
    __tablename__ = "fee"
    collection_slug: Mapped[str] = mapped_column(ForeignKey("collection.opensea_slug"))
    fee: Mapped[float]
    recipient: Mapped[str]

class Nft(Base):
    __tablename__ = "nft"
    opensea_slug: Mapped[str] = mapped_column(ForeignKey("collection.opensea_slug"))
    token_id: Mapped[str]
    contract_address: Mapped[str]
    token_standard: Mapped[str]
    name: Mapped[str]
    descp: Mapped[str]
    image_url: Mapped[str]
    metadata_url: Mapped[str]
    opensea_url: Mapped[str]
    updated_at: Mapped[datetime]
    traits: Mapped[JSONB]
    is_nsfw: Mapped[bool]
    is_disabled: Mapped[bool]
    
    def __repr__(self) -> str:
        return f"Nft(id={self.id!r}, email_address={self.chain!r})"

class NftSale(Base):
    token_id: Mapped[str]
    contract_address: Mapped[str]
    buyer: Mapped[str]
    selle: Mapped[str]
    token_id: Mapped[str]
    token_id: Mapped[str]
    token_id: Mapped[str]
    token_id: Mapped[str]
    token_id: Mapped[str]
def get_metadata():
    return Base.metadata