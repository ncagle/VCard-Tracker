# -*- coding: utf-8 -*-
"""
src.vcard_tracker.models.base.py - VCard-Tracker
Created by NCagle
2025-02-03
      _
   __(.)<
~~~⋱___)~~~

<Description>
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Optional


class Element(Enum):
    FIRE = auto()
    WATER = auto()
    GRASS = auto()
    ELECTRIC = auto()
    PLATINUM = auto()

class CardType(Enum):
    CHARACTER = auto()
    SUPPORT = auto()
    GUARDIAN = auto()
    SHIELD = auto()

class Acquisition(Enum):
    PULLED = auto()
    TRADED = auto()
    GIFTED = auto()

@dataclass
class BaseCard:
    """
    Base class for all cards containing common attributes

    Arguments:
        name (str): Card name
        card_type (CardType): Type of card
        talent (str): Card talent description
        edition (str): Card edition
        card_number (str): Unique card number
        illustrator (str): Card artist name

        # Optional attributes with defaults
        is_holo (bool): Whether card is holographic
        is_promo (bool): Whether card is a promo version
        is_misprint (bool): Whether card has printing errors
        acquisition (Optional[Acquisition]): How card was acquired
        date_acquired (Optional[datetime]): When card was acquired
        notes (str): Additional notes about the card
    """
    # Required attributes
    name: str
    card_type: CardType
    talent: str
    edition: str
    card_number: str
    illustrator: str

    # Optional attributes with defaults
    is_holo: bool = False
    is_promo: bool = False
    is_misprint: bool = False

    # Collection attributes
    acquisition: Optional[Acquisition] = None
    date_acquired: Optional[datetime] = None
    notes: str = ""


    @property
    def is_playable(self) -> bool:
        """
        Whether the card can be used in gameplay.
        Box toppers are not playable.

        Returns:
            bool: True if card can be used in gameplay
        """
        return True
