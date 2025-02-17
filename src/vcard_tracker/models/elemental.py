# -*- coding: utf-8 -*-
"""
src.vcard_tracker.models.elemental.py - VCard-Tracker
Created by NCagle
2025-02-03
      _
   __(.)<
~~~⋱___)~~~

<Description>
"""

from dataclasses import dataclass
from typing import Optional
from vcard_tracker.models.base import BaseCard, Element, CardType


@dataclass
class ElementalCard(BaseCard):
    """
    Base class for Guardian and Shield cards

    Arguments:
        element (Element): Card's element
    """
    element: Optional[Element] = None


@dataclass
class GuardianCard(ElementalCard):
    """
    Guardian card specific attributes
    Inherits all attributes from ElementalCard
    
    Notes:
        There is exactly one Guardian card per element
    """
    def __post_init__(self):
        """Set card type to GUARDIAN after initialization"""
        self.card_type = CardType.GUARDIAN
        if self.element is None:
            raise ValueError("Guardian cards must have an element")


@dataclass
class ShieldCard(ElementalCard):
    """
    Shield card specific attributes
    Inherits all attributes from ElementalCard
    
    Notes:
        There is exactly one Shield card per element
    """
    def __post_init__(self):
        """Set card type to SHIELD after initialization"""
        self.card_type = CardType.SHIELD
        if self.element is None:
            raise ValueError("Shield cards must have an element")
