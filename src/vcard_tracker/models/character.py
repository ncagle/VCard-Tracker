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
