# -*- coding: utf-8 -*-
"""
tests.test_database.py - VCard-Tracker
Created by NCagle
2025-02-03
      _
   __(.)<
~~~⋱___)~~~

Tests for database operations, focusing on card querying functionality.

✅ Card querying (by type, element, level, etc.)
    ✅ Basic Card Queries
        ✅ Get by card number
        ✅ Get by card type
        ✅ Get by element
    - Character-Specific Queries
        ✅ Get by character name
        - Get all variants
        ✅ Get by power level
        - Include/exclude box toppers
    - Collection Management
        ✅ Get collected cards
        - Update collection status
        ✅ Error handling for non-existent cards

❌ Collection tracking
    - asdf

❌ Import/export functionality
    - asdf

❌ Data validation across multiple cards
    - asdf
"""
import pytest
from sqlalchemy.orm import Session

from vcard_tracker.models.base import (
    Element,
    CardType,
    Acquisition
)
from vcard_tracker.database.manager import DatabaseManager


@pytest.mark.database
def test_get_card_by_number(db_session: Session, populated_db: DatabaseManager):
    """Test retrieving a single card by its number"""
    # Get a card we know exists
    card = populated_db.get_card_by_number("106")  # FREAM level 8
    assert card is not None
    assert card.name == "FREAM"
    assert card.character_details is not None  # Check if it has character details
    assert card.character_details.power_level == 8


    # Try to get a non-existent card
    card = populated_db.get_card_by_number("999999")
    assert card is None


@pytest.mark.database
def test_get_cards_by_type(db_session: Session, populated_db: DatabaseManager):
    """Test retrieving cards by their type"""
    # Get all character cards
    character_cards = populated_db.get_cards_by_type(CardType.CHARACTER)
    assert len(character_cards) > 0
    assert all(card.card_type == CardType.CHARACTER for card in character_cards)

    # Get all support cards
    support_cards = populated_db.get_cards_by_type(CardType.SUPPORT)
    assert len(support_cards) > 0
    assert all(card.card_type == CardType.SUPPORT for card in support_cards)

    # Get all guardian cards
    guardian_cards = populated_db.get_cards_by_type(CardType.GUARDIAN)
    assert len(guardian_cards) > 0
    assert all(card.card_type == CardType.GUARDIAN for card in guardian_cards)


@pytest.mark.database
def test_get_cards_by_element(db_session: Session, populated_db: DatabaseManager):
    """Test retrieving cards by their element"""
    # Get all platinum element cards
    platinum_cards = populated_db.get_cards_by_element(Element.PLATINUM)
    assert len(platinum_cards) > 0
    for card in platinum_cards:
        if card.card_type == CardType.CHARACTER:
            assert card.character_details is not None  # Check if it has character details
            assert card.character_details.element == Element.PLATINUM
        elif card.card_type in (CardType.GUARDIAN, CardType.SHIELD):
            assert card.elemental_details.element == Element.PLATINUM

    # Test with include_support flag
    all_cards = populated_db.get_cards_by_element(Element.PLATINUM, include_support=True)
    assert len(all_cards) >= len(platinum_cards)


@pytest.mark.database
def test_get_cards_by_character_name(db_session: Session, populated_db: DatabaseManager):
    """Test retrieving all cards for a specific character"""
    # Exact match
    fream_cards = populated_db.get_cards_by_character_name("FREAM", exact_match=True)
    assert len(fream_cards) > 0
    assert all(card.name == "FREAM" for card in fream_cards)

    # Partial match
    cards = populated_db.get_cards_by_character_name("FRE", exact_match=False)
    assert len(cards) > 0
    assert any("FRE" in card.name for card in cards)


@pytest.mark.database
def test_get_character_variants(db_session: Session, populated_db: DatabaseManager):
    """Test retrieving all variants of a character"""
    # Get all FREAM variants
    variants = populated_db.get_character_variants("FREAM", include_box_topper=True)
    assert len(variants) > 0
    assert all(card.character_details is not None for card in variants)  # Check if it has character details

    # Check for each variant type
    has_level_8 = False
    has_level_9 = False
    has_level_10 = False
    has_box_topper = False

    for card in variants:
        if not card.character_details:
            continue
        if card.character_details.power_level == 8:
            has_level_8 = True
        elif card.character_details.power_level == 9:
            has_level_9 = True
        elif card.character_details.power_level == 10:
            has_level_10 = True
        if card.character_details.is_box_topper:
            has_box_topper = True

    assert has_level_8, "Missing level 8 variant"
    assert has_level_9, "Missing level 9 variant"
    assert has_level_10, "Missing level 10 variant"
    assert has_box_topper, "Missing box topper variant"

    # Test without box topper
    variants = populated_db.get_character_variants("FREAM", include_box_topper=False)
    assert not any(card.character_details.is_box_topper for card in variants if card.character_details)


@pytest.mark.database
def test_get_cards_by_power_level(db_session: Session, populated_db: DatabaseManager):
    """Test retrieving character cards by power level"""
    # Get all level 8 cards
    level_8_cards = populated_db.get_cards_by_power_level(8)
    assert len(level_8_cards) > 0
    assert all(card.card_type == CardType.CHARACTER for card in level_8_cards)
    assert all(card.character_details is not None for card in level_8_cards)  # Check if it has character details
    assert all(card.character_details.power_level == 8 for card in level_8_cards)

    # Get level 1 (mascot) cards
    mascot_cards = populated_db.get_cards_by_power_level(1)
    assert len(mascot_cards) > 0
    assert all(card.character_details.is_mascott for card in mascot_cards)

    # Test with include_non_character flag
    all_cards = populated_db.get_cards_by_power_level(8, include_non_character=True)
    assert len(all_cards) >= len(level_8_cards)


@pytest.mark.database
def test_get_cards_by_illustrator(db_session: Session, populated_db: DatabaseManager):
    """Test retrieving cards by illustrator"""
    # Exact match
    cards = populated_db.get_cards_by_illustrator("Louriii", exact_match=True)
    assert len(cards) > 0
    assert all(card.illustrator == "Louriii" for card in cards)

    # Partial match
    cards = populated_db.get_cards_by_illustrator("Lou", exact_match=False)
    assert len(cards) > 0
    assert any("Lou" in card.illustrator for card in cards)


@pytest.mark.database
def test_get_collected_cards(db_session: Session, populated_db: DatabaseManager):
    """Test retrieving all collected cards"""
    # First, mark some cards as collected
    populated_db.update_collection_status("106", True)  # FREAM level 8
    populated_db.update_collection_status("107", True)  # FREAM level 9

    # Get collected cards
    collected = populated_db.get_collected_cards()
    assert len(collected) == 2
    assert all(card.collection_status.is_collected for card in collected)


@pytest.mark.database
def test_update_collection_status(db_session: Session, populated_db: DatabaseManager):
    """Test updating a card's collection status"""
    # Update with full details
    success = populated_db.update_collection_status(
        card_number="106",
        is_collected=True,
        is_holo=False,
        acquisition=Acquisition.PULLED,  # Use enum instead of string
        notes="First pack!"
    )
    assert success

    # Verify the update
    card = populated_db.get_card_by_number("106")
    assert card.collection_status.is_collected
    assert not card.collection_status.is_holo
    assert card.collection_status.acquisition == Acquisition.PULLED  # Compare with enum
    assert card.collection_status.notes == "First pack!"

    # Test updating non-existent card
    success = populated_db.update_collection_status("999999", True)
    assert not success
