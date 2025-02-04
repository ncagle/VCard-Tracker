# -*- coding: utf-8 -*-
"""
src.vcard_tracker.models.character.py - VCard-Tracker
Created by NCagle
2025-02-03
      _
   __(.)<
~~~⋱___)~~~

<Description>
"""

from dataclasses import dataclass
from typing import Optional
from vcard_tracker.models.base import BaseCard, Element


@dataclass
class CharacterCard(BaseCard):
    """
    Character card specific attributes

    Arguments:
        # Required base attributes first (inherited from BaseCard)
        # BaseCard attributes automatically included
        name (str): Card name
        card_type (CardType): Type of card
        talent (str): Card talent description
        edition (str): Card edition
        card_number (str): Unique card number
        illustrator (str): Card artist name
        
        # Character-specific attributes
        # Even though they are technically options, they need default values of `None` for the dataclass
        power_level (Optional[int]): Character power level (8-10, 1 for mascot, None for box topper)
        element (Optional[Element]): Character's element
        age (Optional[str]): Character age as shown on card
        height (Optional[str]): Character height as shown on card
        weight (Optional[str]): Character weight as shown on card
        elemental_strength (Optional[Element]): Strong against this element
        elemental_weakness (Optional[Element]): Weak against this element

        # Optional attributes with defaults
        is_box_topper (bool): Whether this is a box topper variant
        is_mascott (bool): Whether this is a mascott card
        is_holo (bool): Whether card is holographic
        is_promo (bool): Whether card is a promo version
        is_misprint (bool): Whether card has printing errors

    Notes:
        Age, height, and weight are stored as strings to match card text exactly
        Box toppers (is_box_topper=True) should have null values for all gameplay attributes
        Regular character cards must have values for all gameplay attributes
        Mascot cards must have power_level=1
        Regular character cards must have power levels 8-10

    Usage:
    # Correct
    box_topper = CharacterCard(
        name="FREAM",
        card_type=CardType.CHARACTER,
        talent="",
        edition="First",
        card_number="106",
        illustrator="Louriii",
        is_box_topper=True,
        # All gameplay attributes left as None
    )

    # Incorrect - This would raise a ValueError
    invalid_box_topper = CharacterCard(
        name="FREAM",
        card_type=CardType.CHARACTER,
        talent="",
        edition="First",
        card_number="106",
        illustrator="Louriii",
        is_box_topper=True,
        power_level=8  # Can't have gameplay attributes!
    )
    """
    # Required character-specific attributes
    power_level: Optional[int] = None
    element: Optional[Element] = None
    age: Optional[str] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    elemental_strength: Optional[Element] = None
    elemental_weakness: Optional[Element] = None

    # Optional attributes with defaults
    is_box_topper: bool = False
    is_mascott: bool = False


    def __post_init__(self):
        """
        Validate card attributes after initialization.
        Box toppers should have null gameplay attributes.
        Regular character cards must have non-null gameplay attributes.
        """
        if self.is_box_topper:
            if any([
                self.power_level is not None,
                self.age is not None,
                self.height is not None,
                self.weight is not None,
                self.elemental_strength is not None,
                self.elemental_weakness is not None
            ]):
                raise ValueError("Box topper cards cannot have gameplay attributes")
        else:
            if any([
                self.power_level is None,
                self.element is None,
                self.age is None,
                self.height is None,
                self.weight is None,
                self.elemental_strength is None,
                self.elemental_weakness is None
            ]):
                raise ValueError("Regular character cards must have all gameplay attributes")

            # Validate power level based on card type
            if self.is_mascott and self.power_level != 1:
                raise ValueError("Mascot cards must have power level 1")
            elif not self.is_mascott and self.power_level not in (8, 9, 10):
                raise ValueError("Regular character cards must have power level 8, 9, or 10")

    @property
    def is_playable(self) -> bool:
        """
        Whether the card can be used in gameplay.
        Box toppers are not playable.

        Returns:
            bool: True if card can be used in gameplay
        """
        return not self.is_box_topper
