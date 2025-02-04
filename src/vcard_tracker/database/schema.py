# -*- coding: utf-8 -*-
"""
src.vcard_tracker.database.schema.py - VCard-Tracker
Created by NCagle
2025-02-03
      _
   __(.)<
~~~⋱___)~~~

<Description>
"""

from datetime import datetime as dt
from typing import Optional
from sqlalchemy import (
    create_engine,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Enum
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship
)

# Application-specific imports
from vcard_tracker.models.base import (
    Element,
    CardType,
    Acquisition
)


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


class Card(Base):
    """Base table for all cards"""
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    card_type: Mapped[CardType] = mapped_column(Enum(CardType))
    talent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    edition: Mapped[str] = mapped_column(String(50))
    card_number: Mapped[str] = mapped_column(String(20))  #, unique=True)
    illustrator: Mapped[str] = mapped_column(String(100))
    image_path: Mapped[str] = mapped_column(String(255))

    # Type-specific relationships
    character_details: Mapped[Optional["CharacterDetails"]] = relationship(back_populates="card")
    support_details: Mapped[Optional["SupportDetails"]] = relationship(back_populates="card")
    elemental_details: Mapped[Optional["ElementalDetails"]] = relationship(back_populates="card")

    # Collection status
    collection_status: Mapped[Optional["CollectionStatus"]] = relationship(back_populates="card")


class CharacterDetails(Base):
    """Details specific to character cards"""
    __tablename__ = "character_details"

    id: Mapped[int] = mapped_column(primary_key=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id"))

    # Gameplay attributes
    power_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    element: Mapped[Optional[Element]] = mapped_column(Enum(Element), nullable=True)
    age: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    height: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    weight: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    elemental_strength: Mapped[Optional[Element]] = mapped_column(Enum(Element), nullable=True)
    elemental_weakness: Mapped[Optional[Element]] = mapped_column(Enum(Element), nullable=True)

    # Box topper and mascott flags
    is_box_topper: Mapped[bool] = mapped_column(Boolean, default=False)
    is_mascott: Mapped[bool] = mapped_column(Boolean, default=False)

    card: Mapped["Card"] = relationship(back_populates="character_details")


class SupportDetails(Base):
    """Details specific to support character cards"""
    __tablename__ = "support_details"

    id: Mapped[int] = mapped_column(primary_key=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id"))
    is_secret_rare: Mapped[bool] = mapped_column(Boolean, default=False)

    card: Mapped["Card"] = relationship(back_populates="support_details")


class ElementalDetails(Base):
    """Details specific to guardian and shield cards"""
    __tablename__ = "elemental_details"

    id: Mapped[int] = mapped_column(primary_key=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id"))
    element: Mapped[Element] = mapped_column(Enum(Element))

    card: Mapped["Card"] = relationship(back_populates="elemental_details")


class CollectionStatus(Base):
    """Tracks collection status and details for each card"""
    __tablename__ = "collection_status"

    id: Mapped[int] = mapped_column(primary_key=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id"))
    is_collected: Mapped[bool] = mapped_column(Boolean, default=False)
    is_holo: Mapped[bool] = mapped_column(Boolean, default=False)
    is_promo: Mapped[bool] = mapped_column(Boolean, default=False)
    is_misprint: Mapped[bool] = mapped_column(Boolean, default=False)
    acquisition: Mapped[Optional[Acquisition]] = mapped_column(Enum(Acquisition))
    date_acquired: Mapped[Optional[dt]] = mapped_column(DateTime)
    notes: Mapped[Optional[str]] = mapped_column(String(1000))

    card: Mapped["Card"] = relationship(back_populates="collection_status")
