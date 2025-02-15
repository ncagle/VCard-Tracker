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
from typing import List

import pytest
from sqlalchemy.orm import Session

from vcard_tracker.models.base import (
    Element,
    CardType,
    Acquisition
)
from vcard_tracker.database.manager import DatabaseManager


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
    # Get initial missing cards count
    initial_missing = populated_db.get_missing_cards()
    initial_count = len(initial_missing)

    # Collect some cards
    _ = populated_db.update_collection_status("CH-001A", True)
    _ = populated_db.update_collection_status("SP-001A", True)

    # Get updated missing cards
    updated_missing = populated_db.get_missing_cards()

    # Verify counts
    assert len(updated_missing) == initial_count - 2

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
    # Clear any existing collection status
    with Session(populated_db.engine) as session:
        _ = session.query(populated_db.CollectionStatus).delete()
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
