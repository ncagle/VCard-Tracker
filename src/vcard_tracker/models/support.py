# -*- coding: utf-8 -*-
"""
src.vcard_tracker.models.support.py - VCard-Tracker
Created by NCagle
2025-02-03
      _
   __(.)<
~~~⋱___)~~~

<Description>
"""

from dataclasses import dataclass
from vcard_tracker.models.base import BaseCard, CardType


@dataclass
class SupportCard(BaseCard):
    """
    Support character card specific attributes

    Arguments:
        is_secret_rare (bool): Whether this is the secret rare variant
    """
    is_secret_rare: bool = False

    def __post_init__(self):
        """Ensure card type is set to SUPPORT"""
        self.card_type = CardType.SUPPORT
