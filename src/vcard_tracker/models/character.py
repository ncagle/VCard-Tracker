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
from vcard_tracker.models.base import BaseCard, Element

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
