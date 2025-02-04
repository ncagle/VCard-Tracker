# -*- coding: utf-8 -*-
"""
tests.__init__.py - VCard-Tracker
Created by NCagle
2025-02-03
      _
   __(.)<
~~~⋱___)~~~

Tests for card model creation and validation.
"""
import pytest
from vcard_tracker.models.base import Element, CardType, BaseCard
from vcard_tracker.models.character import CharacterCard
from vcard_tracker.models.support import SupportCard
from vcard_tracker.models.elemental import GuardianCard, ShieldCard


def test_create_base_card():
    """Test creation of base card with minimal attributes"""
    card = BaseCard(
        name="Test Card",
        card_type=CardType.CHARACTER,
        talent="Test talent",
        edition="First",
        card_number="001",
        illustrator="Test Artist"
    )
    assert card.name == "Test Card"
    assert card.card_type == CardType.CHARACTER
    assert card.talent == "Test talent"
    assert card.edition == "First"
    assert card.card_number == "001"
    assert card.illustrator == "Test Artist"
    assert not card.is_holo
    assert not card.is_promo
    assert not card.is_misprint


def test_create_character_card_level_8():
    """Test creation of a regular level 8 character card"""
    card = CharacterCard(
        name="FREAM",
        card_type=CardType.CHARACTER,
        talent="Delayed Reaction: If you lose this round, your next Power Level card gets +1 power.",
        edition="First",
        card_number="106",
        illustrator="Louriii",
        power_level=8,
        element=Element.PLATINUM,
        age="Lava Lamp",
        height="Lava Lamp",
        weight="Lava Lamp",
        elemental_strength=Element.ELECTRIC,
        elemental_weakness=Element.GRASS
    )

    assert card.name == "FREAM"
    assert card.power_level == 8
    assert card.element == Element.PLATINUM
    assert card.age == "Lava Lamp"
    assert not card.is_box_topper
    assert not card.is_mascott
    assert card.is_playable


def test_create_mascot_card():
    """Test creation of a mascot character card"""
    card = CharacterCard(
        name="SPIKE",
        card_type=CardType.CHARACTER,
        talent="+1 to your Power Level card.",
        edition="First",
        card_number="162",
        illustrator="Louriii",
        power_level=1,
        element=Element.PLATINUM,
        age="Spaghet",
        height="Smol",
        weight="Sandwich",
        elemental_strength=Element.ELECTRIC,
        elemental_weakness=Element.GRASS,
        is_mascott=True
    )

    assert card.name == "SPIKE"
    assert card.power_level == 1
    assert card.is_mascott
    assert card.is_playable


def test_create_box_topper():
    """Test creation of a box topper card"""
    card = CharacterCard(
        name="FREAM",
        card_type=CardType.CHARACTER,
        talent=None,
        edition="First",
        card_number="BT-001",
        illustrator="Louriii",
        power_level=None,
        element=None,
        age=None,
        height=None,
        weight=None,
        elemental_strength=None,
        elemental_weakness=None,
        is_box_topper=True,
        is_holo=True
    )

    assert card.name == "FREAM"
    assert card.is_box_topper
    assert card.power_level is None
    assert card.element is None
    assert not card.is_playable
    assert card.is_holo


def test_create_support_card():
    """Test creation of a regular support card"""
    card = SupportCard(
        name="Healing Mage",
        card_type=CardType.SUPPORT,
        talent="Restore 30 HP",
        edition="First",
        card_number="201",
        illustrator="John Doe"
    )

    assert card.name == "Healing Mage"
    assert not card.is_secret_rare
    assert card.is_playable


def test_create_guardian_card():
    """Test creation of a guardian card"""
    card = GuardianCard(
        name="Fire Guardian",
        card_type=CardType.GUARDIAN,
        talent="Fire protection",
        edition="First",
        card_number="301",
        illustrator="Mark Wilson",
        element=Element.FIRE
    )

    assert card.name == "Fire Guardian"
    assert card.element == Element.FIRE
    assert card.card_type == CardType.GUARDIAN
    assert card.is_playable


def test_create_shield_card():
    """Test creation of a shield card"""
    card = ShieldCard(
        name="Water Shield",
        card_type=CardType.SHIELD,
        talent="Water defense",
        edition="First",
        card_number="402",
        illustrator="Emma Brown",
        element=Element.WATER
    )

    assert card.name == "Water Shield"
    assert card.element == Element.WATER
    assert card.card_type == CardType.SHIELD
    assert card.is_playable


def test_invalid_mascot_power_level():
    """Test that mascot cards must have power level 1"""
    with pytest.raises(ValueError, match="Mascot cards must have power level 1"):
        CharacterCard(
            name="Invalid Mascot",
            card_type=CardType.CHARACTER,
            talent="Test",
            edition="First",
            card_number="TEST-001",
            illustrator="Test Artist",
            power_level=8,  # Invalid power level for mascot
            element=Element.FIRE,
            age="???",
            height="???",
            weight="???",
            elemental_strength=Element.GRASS,
            elemental_weakness=Element.WATER,
            is_mascott=True
        )


def test_invalid_box_topper_with_stats():
    """Test that box toppers cannot have gameplay attributes"""
    with pytest.raises(ValueError, match="Box topper cards cannot have gameplay attributes"):
        CharacterCard(
            name="Invalid Box Topper",
            card_type=CardType.CHARACTER,
            talent=None,
            edition="First",
            card_number="BT-002",
            illustrator="Test Artist",
            power_level=8,  # Should be None for box topper
            element=Element.FIRE,  # Should be None for box topper
            age="25",  # Should be None for box topper
            height="180cm",  # Should be None for box topper
            weight="75kg",  # Should be None for box topper
            elemental_strength=Element.GRASS,  # Should be None for box topper
            elemental_weakness=Element.WATER,  # Should be None for box topper
            is_box_topper=True
        )


def test_create_misprint_character_card():
    """Test creation of a misprint character card"""
    card = CharacterCard(
        name="Misprint FREAM",
        card_type=CardType.CHARACTER,
        talent="Professional Streamer",
        edition="First",
        card_number="69420",
        illustrator="Louriii",
        power_level=8,
        element=Element.PLATINUM,
        age="69",
        height="6ft 9in",
        weight="BEANS",
        elemental_strength=Element.ELECTRIC,
        elemental_weakness=Element.GRASS,
        is_misprint=True
    )

    assert card.name == "FREAM"
    assert card.power_level == 8
    assert card.element == Element.PLATINUM
    assert card.age == "69"
    assert not card.is_box_topper
    assert not card.is_mascott
    assert card.is_playable
    assert card.is_misprint
