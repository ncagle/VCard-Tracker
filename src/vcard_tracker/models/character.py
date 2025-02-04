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
        power_level (Optional[int]): Character power level (8-10), null for box toppers
        element (Optional[Element]): Character's element, null for box toppers
        age (Optional[str]): Character age, null for box toppers
        height (Optional[str]): Character height, null for box toppers
        weight (Optional[str]): Character weight, null for box toppers
        elemental_strength (Optional[Element]): Strong against this element, null for box toppers
        elemental_weakness (Optional[Element]): Weak against this element, null for box toppers
        is_box_topper (bool): Whether this is a box topper variant
        is_mascott (bool): Whether this is a mascott card

    Notes:
        Age, height, and weight are stored as strings to match card text exactly
        Box toppers (is_box_topper=True) should have null values for all gameplay attributes
        Regular character cards must have values for all gameplay attributes

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
    power_level: Optional[int]
    element: Optional[Element]
    age: Optional[str]
    height: Optional[str]
    weight: Optional[str]
    elemental_strength: Optional[Element]
    elemental_weakness: Optional[Element]
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
