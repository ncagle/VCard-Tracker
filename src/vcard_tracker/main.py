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
    PROMO = auto()

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
        is_holo (bool): Whether card is holographic
        is_promo (bool): Whether card is a promo version
        is_misprint (bool): Whether card has printing errors
    """
    name: str
    card_type: CardType
    talent: str
    edition: str
    card_number: str
    illustrator: str
    is_holo: bool = False
    is_promo: bool = False
    is_misprint: bool = False
    
    # Collection attributes
    acquisition: Optional[Acquisition] = None
    date_acquired: Optional[datetime] = None
    notes: str = ""

@dataclass
class CharacterCard(BaseCard):
    """
    Character card specific attributes

    Arguments:
        power_level (int): Character power level (8-10)
        element (Element): Character's element
        age (int): Character age
        height (float): Character height
        weight (float): Character weight
        elemental_strength (Element): Strong against this element
        elemental_weakness (Element): Weak against this element
        is_box_topper (bool): Whether this is a box topper variant
        is_mascott (bool): Whether this is a mascott card
    """
    power_level: int
    element: Element
    age: int
    height: float
    weight: float
    elemental_strength: Element
    elemental_weakness: Element
    is_box_topper: bool = False
    is_mascott: bool = False

@dataclass
class SupportCard(BaseCard):
    """
    Support character card specific attributes

    Arguments:
        is_secret_rare (bool): Whether this is the secret rare variant
    """
    is_secret_rare: bool = False

@dataclass
class ElementalCard(BaseCard):
    """
    Base class for Guardian and Shield cards

    Arguments:
        element (Element): Card's element
    """
    element: Element
