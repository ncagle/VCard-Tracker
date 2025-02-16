# -*- coding: utf-8 -*-
"""
tests.test_db_collection_analysis.py - VCard-Tracker
Created by NCagle
2025-02-15
      _
   __(.)<
~~~⋱___)~~~

╔═══════════════════════════╗
║ Collection Analysis Tests ║
╚═══════════════════════════╝
Tests for collection analysis database operations.

This module contains tests for the DatabaseManager methods that analyze
collection status, completion, and recent acquisitions.

❌ Collection Analysis
    - Get collection progress statistics
    - Find missing cards from collection
    - Check for complete character sets
    - View recent card acquisitions
    - Edge cases for collection stats (e.g., empty/full collection, misprints)

"""
from datetime import (
    datetime as dt,
    timedelta
)
from typing import List, Tuple
from pathlib import Path
import os

import pytest
from sqlalchemy.orm import Session

from vcard_tracker.models.base import (
    Element,
    CardType,
    Acquisition
)
from vcard_tracker.database.schema import Card, CollectionStatus
from vcard_tracker.database.manager import DatabaseManager


EXPORT_DEBUG_INFO = False
if EXPORT_DEBUG_INFO: os.makedirs("tests/debug", exist_ok=True)


# DEBUG: Helper function to deduplicate cards for testing
def deduplicate_cards(session: Session, card_numbers: List[str]) -> None:
    """Remove duplicate cards with the same card number."""
    for card_number in card_numbers:
        duplicates = session.query(Card)\
            .filter_by(card_number=card_number)\
            .all()
        if len(duplicates) > 1:
            for card in duplicates[1:]:
                session.delete(card)
    session.commit()


@pytest.mark.database
def test_get_collection_stats(db_session: Session, populated_db: DatabaseManager):
    """
    Test collection statistics calculation.

    Verifies that get_collection_stats correctly calculates:
        - Total collected cards
        - Total available cards
        - Completion percentage
        - Cards collected by type
        - Total holos and secret rares
    """
    # First collect some cards
    _ = populated_db.update_collection_status("CH-001A", True, is_holo=False)  # Regular
    _ = populated_db.update_collection_status("CH-001B", True, is_holo=True)   # Holo
    _ = populated_db.update_collection_status("SP-001C", True, is_holo=True)   # Secret rare
    # test_card_numbers = ["106", "107", "SP-003"]  # Cards we'll test with
    # First clear any existing collection status
    with Session(populated_db.engine) as session:
        # deduplicate_cards(session, test_card_numbers)  # DEBUG: Deduplicate cards
        _ = session.query(CollectionStatus).delete()
        session.commit()


    stats = populated_db.get_collection_stats()

    # Verify basic counts
    assert stats["total_collected"] == 3
    assert stats["total_cards"] > 0
    assert 0 <= stats["completion_percentage"] <= 100

    # Verify type breakdowns
    assert stats["collected_by_type"][CardType.CHARACTER] == 2
    assert stats["collected_by_type"][CardType.SUPPORT] == 1

    # Verify special card counts
    assert stats["total_holos"] == 2
    assert stats["total_secret_rares"] == 1


@pytest.mark.database
def test_get_missing_cards(db_session: Session, populated_db: DatabaseManager):
    """
    Test retrieval of uncollected cards.

    Verifies that get_missing_cards correctly:
        - Returns all uncollected cards
        - Handles both NULL and False collection status
        - Updates when cards are collected
    """
    # Debug collection status before updating missing cards
    def _create_missing_cards_debug_before():
        with Session(populated_db.engine) as session:
            # Check what cards we have
            all_cards = session.query(Card).all()

            # Check collection status
            collected = session.query(Card)\
                .join(CollectionStatus)\
                .filter(CollectionStatus.is_collected == True)\
                .all()

            # Check specific card
            card_001 = session.query(Card)\
                .filter_by(card_number="SH-001")\
                .first()
            card_001_status = session.query(CollectionStatus)\
                .filter_by(card_id=card_001.id if card_001 else None)\
                .first() if card_001 else None

            with open("tests/debug/missing_cards_debug.txt", "w", encoding="utf-8") as f:
                _ = f.write(f"Total cards in database: {len(all_cards)}\n")
                _ = f.write("Card numbers in database:\n")
                for card in all_cards:
                    _ = f.write(f"  {card.card_number}: {card.name}\n")

                _ = f.write(f"\nTotal collected cards: {len(collected)}\n")
                _ = f.write("Collected card numbers:\n")
                for card in collected:
                    _ = f.write(f"  {card.card_number}: {card.name}\n")

                _ = f.write("\nCard SH-001 details:\n")
                if card_001:
                    _ = f.write("  Found in database: Yes\n")
                    _ = f.write(f"  Name: {card_001.name}\n")
                    _ = f.write(f"  Has collection status: {card_001_status is not None}\n")
                    if card_001_status:
                        _ = f.write(f"  Is collected: {card_001_status.is_collected}\n")
                else:
                    _ = f.write("  Not found in database\n")


    # Debug collection status after updating missing cards
    def _create_missing_cards_debug_after(updated_missing: List[Card]):
        with open("tests/debug/missing_cards_debug.txt", "a", encoding="utf-8") as f:
            _ = f.write(f"\nMissing cards count: {len(updated_missing)}\n")
            _ = f.write("Missing card numbers:\n")
            for card in updated_missing:
                _ = f.write(f"  {card.card_number}: {card.name}\n")


    # test_card_numbers = ["106", "SH-001"]  # Cards we'll test with
    # First clear any existing collection status
    with Session(populated_db.engine) as session:
        # deduplicate_cards(session, test_card_numbers)  # DEBUG: Deduplicate cards
        _ = session.query(CollectionStatus).delete()
        session.commit()

    # Initial check - all cards should be missing
    initial_missing = populated_db.get_missing_cards()
    initial_count = len(initial_missing)

    # Collect some cards
    _ = populated_db.update_collection_status("CH-001A", True)
    _ = populated_db.update_collection_status("SP-001A", True)

    if EXPORT_DEBUG_INFO:
        _create_missing_cards_debug_before()

    # Get updated missing cards
    updated_missing = populated_db.get_missing_cards()

    # Verify counts
    assert len(updated_missing) == initial_count - 2
    if EXPORT_DEBUG_INFO:
        _create_missing_cards_debug_after(updated_missing)

    # Verify collected cards aren't in missing list
    missing_numbers = [card.card_number for card in updated_missing]
    assert "CH-001A" not in missing_numbers
    assert "SP-001A" not in missing_numbers


@pytest.mark.database
def test_get_complete_sets(db_session: Session, populated_db: DatabaseManager):
    """
    Test identification of completed character sets.

    Verifies that get_complete_sets correctly:
        - Identifies when all variants of a character are collected
        - Handles different card variants (mascot, levels, box topper)
        - Updates when sets become complete
    """
    # Debug card sets information and write info to file
    def _create_sets_debug(fream_cards: List[Card], collected_cards: List[Card], complete_sets: List[str]):
        with open("tests/debug/sets_debug.txt", "w", encoding="utf-8") as f:
            _ = f.write(f"Total FREAM cards: {len(fream_cards)}\n")
            _ = f.write("FREAM cards in database:\n")
            for card in fream_cards:
                collected_status = bool(card.collection_status
                                        and card.collection_status.is_collected)
                _ = f.write(f"  {card.card_number}: {card.name} (collected: {collected_status})\n")
            _ = f.write(f"\nCollected FREAM cards: {len(collected_cards)}\n")
            _ = f.write("Collected cards:\n")
            for card in collected_cards:
                _ = f.write(f"  {card.card_number}: {card.name}\n")
            _ = f.write(f"\nComplete sets found: {complete_sets}\n")


    # Debug query information and write info to file
    def _create_query_debug(session: Session, fream_cards: List[Card],):
        with open("tests/debug/query_debug.txt", "w", encoding="utf-8") as f:
            _ = f.write("SQL Query:\n")
            sql_query = session.query(Card)\
                .filter(Card.name == "FREAM")
            _ = f.write(str(sql_query))

            # Check if we're getting duplicate rows from the query
            distinct_card_numbers = session.query(Card.card_number)\
                .filter(Card.name == "FREAM")\
                .distinct()\
                .all()
            _ = f.write(f"\n\nDistinct card numbers: {len(distinct_card_numbers)}")
            _ = f.write("\nCard numbers:\n")
            for num in distinct_card_numbers:
                _ = f.write(f"  {num[0]}\n")

            all_count = session.query(Card)\
                .filter(Card.name == "FREAM")\
                .count()
            _ = f.write(f"\nTotal rows returned: {all_count}")

            # Check the joins
            _ = f.write("\n\nJoined tables info:")
            for card in fream_cards:
                _ = f.write(f"\nCard {card.card_number}:")
                _ = f.write(f"\n  Collection Status: {card.collection_status}")
                if hasattr(card, "character_details"):
                    _ = f.write(f"\n  Character Details: {card.character_details}")

            # Check collection status query
            collection_count = session.query(CollectionStatus)\
                .join(Card)\
                .filter(Card.name == "FREAM")\
                .count()
            _ = f.write(f"\n\nCollection status records: {collection_count}")


    # test_card_numbers = ["106", "107", "108", "BT-001"]  # Cards we'll test with - FREAM variants
    # First clear any existing collection status
    with Session(populated_db.engine) as session:
        # deduplicate_cards(session, test_card_numbers)  # DEBUG: Deduplicate cards
        _ = session.query(CollectionStatus).delete()
        session.commit()

    # Initially should have no complete sets
    initial_complete = populated_db.get_complete_sets()
    assert len(initial_complete) == 0

    # Collect all variants of Flame Knight
    variants = [
        "CH-001A",  # Regular Level 8
        "CH-001B",  # Holo Level 8
        "CH-001C",  # Regular Mascot
        "CH-001D",  # Level 10 (Holo)
        "CH-001E",  # Box Topper
    ]

    for card_number in variants:
        _ = populated_db.update_collection_status(card_number, True)

    # Check complete sets
    complete_sets = populated_db.get_complete_sets()
    assert "Flame Knight" in complete_sets

    if EXPORT_DEBUG_INFO:
        with Session(populated_db.engine) as session:
            # Debug print to see what's happening
            fream_cards = session.query(Card)\
                .filter(Card.name == "FREAM")\
                .all()
            collected_cards = [c for c in fream_cards if c.collection_status
                               and c.collection_status.is_collected]

            # Debug card sets information and write info to file
            _create_sets_debug(fream_cards, collected_cards, complete_sets)
            # Debug query information and write info to file
            _create_query_debug(session, fream_cards)

    assert len(complete_sets) == 1

    # Verify partial sets aren't included
    _ = populated_db.update_collection_status("CH-002A", True)  # Just one Event Knight variant
    complete_sets = populated_db.get_complete_sets()
    assert "Event Knight" not in complete_sets


@pytest.mark.database
def test_get_recent_acquisitions(db_session: Session, populated_db: DatabaseManager):
    """
    Test retrieval of recently acquired cards.

    Verifies that get_recent_acquisitions correctly:
        - Returns cards in correct chronological order
        - Respects the limit parameter
        - Only includes collected cards
    """
    # Add cards with different acquisition dates
    dates = [
        dt.now() - timedelta(days=5),
        dt.now() - timedelta(days=3),
        dt.now() - timedelta(days=1)
    ]
    # test_card_numbers = ["106", "SP-001", "GD-002"]  # Cards we'll test with
    # First clear any existing collection status
    with Session(populated_db.engine) as session:
        # deduplicate_cards(session, test_card_numbers)  # DEBUG: Deduplicate cards
        _ = session.query(CollectionStatus).delete()
        session.commit()

    cards = [
        ("CH-001A", dates[0]),
        ("SP-001A", dates[1]),
        ("GD-001", dates[2])
    ]

    for card_number, date in cards:
        _ = populated_db.update_collection_status(
            card_number,
            is_collected=True,
            acquisition=Acquisition.PULLED,
            notes=f"Test acquisition on {date}"
        )
        # Update the acquisition date directly since it's usually auto-set
        with Session(populated_db.engine) as session:
            card = session.query(populated_db.Card).filter_by(card_number=card_number).first()
            card.collection_status.date_acquired = date
            session.commit()

    # Test with default limit
    recent = populated_db.get_recent_acquisitions()
    assert len(recent) == 3
    assert recent[0].card_number == "GD-001"  # Most recent first

    # Test with custom limit
    recent = populated_db.get_recent_acquisitions(limit=2)
    assert len(recent) == 2
    assert recent[0].card_number == "GD-001"
    assert recent[1].card_number == "SP-001A"


@pytest.mark.database
def test_collection_stats_edge_cases(db_session: Session, populated_db: DatabaseManager):
    """
    Test collection statistics calculation with edge cases.

    Verifies proper handling of:
        - Empty collection
        - All cards collected
        - Mixed holo/non-holo status
        - Promo cards
        - Misprints
    """
    # Manually override collection status for testing purposes
    def _manual_override_collection_status():
        # BUG: Updating the collection status is overwriting existing information,
        # such as the is_holo and is_promo flags
        # Since `update_collection_status()` overwrites the existing status,
        # the is_promo flag has to be set after collection
        # FIXED: Updated `update_collection_status()` to preserve existing attributes
        # unless otherwise specified
        with Session(populated_db.engine) as session:
            for card_number in ["PR-069", "PR-002"]:
                card = session.query(Card)\
                    .filter_by(card_number=card_number)\
                    .first()
                if not card.collection_status:
                    card.collection_status = CollectionStatus()
                card.collection_status.is_promo = True
                card.collection_status.is_holo = True
            session.commit()


    def _create_promo_debug(promo_cards: List[Card]):
        with open("tests/debug/promo_debug.txt", "w", encoding="utf-8") as f:
            _ = f.write(f"Found {len(promo_cards)} promo cards\n\n")
            for card in promo_cards:
                _ = f.write(f"Card {card.card_number}:\n")
                _ = f.write(f"  Name: {card.name}\n")
                _ = f.write(f"  Type: {card.card_type}\n")
                if card.collection_status:
                    _ = f.write("  Collection Status:\n")
                    _ = f.write(f"    is_promo: {card.collection_status.is_promo}\n")
                    _ = f.write(f"    is_holo: {card.collection_status.is_holo}\n")
                    _ = f.write(f"    is_collected: {card.collection_status.is_collected}\n")
                else:
                    _ = f.write("  No collection status found\n")
                _ = f.write("\n")


    # Clear any existing collection status
    with Session(populated_db.engine) as session:
        # unique_card_numbers = session.query(Card.card_number).distinct()  # DEBUG: Deduplicate cards
        # deduplicate_cards(session, unique_card_numbers)  # All cards  # DEBUG: Deduplicate cards
        _ = session.query(CollectionStatus).delete()
        session.commit()

    # Verify empty collection stats
    stats = populated_db.get_collection_stats()
    assert stats["total_collected"] == 0
    assert stats["completion_percentage"] == 0
    assert all(count == 0 for count in stats["collected_by_type"].values())

    # Collect everything
    all_cards = populated_db.get_cards_by_type(CardType.CHARACTER)
    for card in all_cards:
        _ = populated_db.update_collection_status(
            card.card_number,
            is_collected=True,
            is_holo=False
        )

    stats = populated_db.get_collection_stats()
    assert stats["total_collected"] == len(all_cards)

    # Test misprint tracking
    # First mark the card as collected
    _ = populated_db.update_collection_status(
        "CH-999",  # Misprint card from sample data
        is_collected=True
    )

    # Then update its condition
    _ = populated_db.update_card_condition(
        "CH-999",
        is_misprint=True
    )

    # Verify misprint is tracked correctly
    with Session(populated_db.engine) as session:
        misprint_card = session.query(populated_db.Card)\
            .filter_by(card_number="CH-999")\
            .first()
        assert misprint_card.collection_status.is_collected
        assert misprint_card.collection_status.is_misprint

    # Verify misprint is counted correctly
    stats = populated_db.get_collection_stats()
    assert "CH-999" in [card.card_number for card in populated_db.get_collected_cards()]

    # DEBUG: Manually override collection status for testing purposes
    # _manual_override_collection_status()

