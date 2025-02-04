# -*- coding: utf-8 -*-
"""
tests.test_models.py - VCard-Tracker
Created by NCagle
2025-02-03
      _
   __(.)<
~~~⋱___)~~~

Tests for card model creation and validation.

✅ Basic card creation for each type
    - Character cards (normal, holo, level variations)
    - Support cards
    - Guardian cards
    - Shield cards

✅ Validation rules
    - Mascot power level = 1
    - Regular character power levels 8-10
    - Level 10 must be holo
    - Box toppers must have null attributes

✅ Box topper null attributes
    - Verification that gameplay stats are null
    - Error when trying to set attributes

✅ Character card variants
    - Level progression (8→9→10)
    - Regular vs holo variants
    - Special text values
    - Promo cards
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

    assert card.name == "Misprint FREAM"
    assert card.power_level == 8
    assert card.element == Element.PLATINUM
    assert card.age == "69"
    assert not card.is_box_topper
    assert not card.is_mascott
    assert card.is_playable
    assert card.is_misprint


"""
Tests for character card variations and relationships
"""
def test_character_level_progression():
    """Test character level progression from 8 to 10"""
    # Level 8 card
    level_8 = CharacterCard(
        name="FREAM",
        card_type=CardType.CHARACTER,
        talent="Delayed Reaction: If you lose this round, your next Power Level card gets +1 power.",
        edition="Base",
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
    assert level_8.power_level == 8
    assert not level_8.is_holo

    # Level 9 holo card
    level_9 = CharacterCard(
        name="FREAM",
        card_type=CardType.CHARACTER,
        talent="LAVA LAMP",
        edition="Base",
        card_number="107",
        illustrator="Louriii",
        power_level=9,
        element=Element.PLATINUM,
        age="Lava Lamp",
        height="Lava Lamp",
        weight="Lava Lamp",
        elemental_strength=Element.ELECTRIC,
        elemental_weakness=Element.GRASS,
        is_holo=True
    )
    assert level_9.power_level == 9
    assert level_9.is_holo

    # Level 10 card (must be holo)
    level_10 = CharacterCard(
        name="FREAM",
        card_type=CardType.CHARACTER,
        talent="AhhAAhhAHhAHAhhAHHAHHAHhAAHAHAaa",
        edition="Base",
        card_number="108",
        illustrator="Louriii",
        power_level=10,
        element=Element.PLATINUM,
        age="(¬_¬)",
        height="Tall for their height",
        weight="Rude!",
        elemental_strength=Element.ELECTRIC,
        elemental_weakness=Element.GRASS,
        is_holo=True
    )
    assert level_10.power_level == 10
    assert level_10.is_holo


def test_invalid_level_10_non_holo():
    """Test that level 10 cards must be holographic"""
    with pytest.raises(ValueError, match="Level 10 cards must be holographic"):
        CharacterCard(
            name="FREAM",
            card_type=CardType.CHARACTER,
            talent="Test",
            edition="Base",
            card_number="TEST-001",
            illustrator="Louriii",
            power_level=10,
            element=Element.PLATINUM,
            age="Test",
            height="Test",
            weight="Test",
            elemental_strength=Element.ELECTRIC,
            elemental_weakness=Element.GRASS,
            is_holo=False  # This should raise an error for level 10
        )


def test_character_holo_variants():
    """Test regular and holo variants of the same character card"""
    # Regular version
    regular = CharacterCard(
        name="FREAM",
        card_type=CardType.CHARACTER,
        talent="Delayed Reaction: If you lose this round, your next Power Level card gets +1 power.",
        edition="Base",
        card_number="106",
        illustrator="Louriii",
        power_level=8,
        element=Element.PLATINUM,
        age="Lava Lamp",
        height="Lava Lamp",
        weight="Lava Lamp",
        elemental_strength=Element.ELECTRIC,
        elemental_weakness=Element.GRASS,
        is_holo=False
    )

    # Holo version - same card but holographic
    holo = CharacterCard(
        name="FREAM",
        card_type=CardType.CHARACTER,
        talent="Delayed Reaction: If you lose this round, your next Power Level card gets +1 power.",
        edition="Base",
        card_number="107",
        illustrator="Louriii",
        power_level=8,
        element=Element.PLATINUM,
        age="Lava Lamp",
        height="Lava Lamp",
        weight="Lava Lamp",
        elemental_strength=Element.ELECTRIC,
        elemental_weakness=Element.GRASS,
        is_holo=True
    )

    # Check that gameplay attributes are identical
    assert regular.power_level == holo.power_level
    assert regular.element == holo.element
    assert regular.elemental_strength == holo.elemental_strength
    assert regular.elemental_weakness == holo.elemental_weakness


def test_promo_character():
    """Test creating a promotional character card"""
    promo = CharacterCard(
        name="FREAM",
        card_type=CardType.CHARACTER,
        talent="Special Event Talent",
        edition="Event 2024",
        card_number="PR-001",
        illustrator="Louriii",
        power_level=8,
        element=Element.PLATINUM,
        age="Lava Lamp",
        height="Lava Lamp",
        weight="Lava Lamp",
        elemental_strength=Element.ELECTRIC,
        elemental_weakness=Element.GRASS,
        is_promo=True,
        is_holo=True  # Promos are always holo
    )
    
    assert promo.is_promo
    assert promo.is_holo  # Verify promo is holographic


def test_special_text_values():
    """Test characters with special/unusual text values"""
    card = CharacterCard(
        name="FREAM",
        card_type=CardType.CHARACTER,
        talent="AhhAAhhAHhAHAhhAHHAHHAHhAAHAHAaa",
        edition="Base",
        card_number="108",
        illustrator="Louriii",
        power_level=10,
        element=Element.PLATINUM,
        age="(¬_¬)",
        height="Tall for their height",
        weight="Rude!",
        elemental_strength=Element.ELECTRIC,
        elemental_weakness=Element.GRASS,
        is_holo=True
    )
    
    # Verify special text values are preserved
    assert card.age == "(¬_¬)"
    assert card.height == "Tall for their height"
    assert card.weight == "Rude!"


def test_mascot_variant():
    """Test mascot card variant"""
    mascot = CharacterCard(
        name="SPIKE",
        card_type=CardType.CHARACTER,
        talent="+1 to your Power Level card. +2 to your Platinum type Power Level Card. +3 to your Fream VTuber Power Level card.",
        edition="Base",
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
    
    assert mascot.power_level == 1
    assert mascot.is_mascott
    assert mascot.is_playable


def test_invalid_power_levels():
    """Test invalid power level combinations"""
    # Test power level 2-7 (invalid for any character card)
    with pytest.raises(ValueError, match="Regular character cards must have power level 8, 9, or 10"):
        CharacterCard(
            name="Invalid Card",
            card_type=CardType.CHARACTER,
            talent="Test",
            edition="Base",
            card_number="TEST-001",
            illustrator="Test Artist",
            power_level=5,  # Invalid power level
            element=Element.PLATINUM,
            age="Test",
            height="Test",
            weight="Test",
            elemental_strength=Element.ELECTRIC,
            elemental_weakness=Element.GRASS
        )
    
    # Test power level > 10
    with pytest.raises(ValueError, match="Regular character cards must have power level 8, 9, or 10"):
        CharacterCard(
            name="Invalid Card",
            card_type=CardType.CHARACTER,
            talent="Test",
            edition="Base",
            card_number="TEST-002",
            illustrator="Test Artist",
            power_level=11,  # Invalid power level
            element=Element.PLATINUM,
            age="Test",
            height="Test",
            weight="Test",
            elemental_strength=Element.ELECTRIC,
            elemental_weakness=Element.GRASS
        )
