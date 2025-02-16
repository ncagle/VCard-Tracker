# -*- coding: utf-8 -*-
"""
tests.test_db_collection_management.py - VCard-Tracker
Created by NCagle
2025-02-15
      _
   __(.)<
~~~⋱___)~~~

╔═════════════════════════════╗
║ Collection Management Tests ║
╚═════════════════════════════╝
Tests for collection management database operations.

This module contains tests for the DatabaseManager methods that manage
bulk updates to collection status, notes, condition flags, trades.

❌ Collection Management
    - Update multiple cards at once
        - Successful bulk updates with multiple cards
        - Handling of invalid card numbers
        - Transaction rollback on failure
    - Add notes to card
        - Adding notes to cards without existing notes
        - Appending notes to existing notes
        - Timestamp formatting
        - Invalid card handling
    - Update card condition flags
        - Updating cards with/without existing status
        - Preserving other collection attributes
        - Invalid card handling
    - Record card trades
        - Successful trade recording
        - Cross-referenced notes
        - Status updates for both cards
        - Handling invalid cards
        - Special handling for promo cards
"""
from datetime import datetime as dt
import pytest
from sqlalchemy.orm import Session

from vcard_tracker.models.base import Acquisition, CardType
from vcard_tracker.database.schema import Card, CollectionStatus


def test_bulk_update_collection_success(populated_db):
    """
    Test successful bulk update of collection status.

    Arguments:
        populated_db: Fixture providing DatabaseManager with sample data

    Verifies that:
        - Multiple cards can be marked as collected
        - Acquisition date is set for newly collected cards
        - Existing collection status is preserved
        - Returns True on success
    """
    # Get some test card numbers
    with Session(populated_db.engine) as session:
        card_numbers = [
            card.card_number for card in session.query(Card).limit(3)
        ]

    # Perform bulk update
    result = populated_db.bulk_update_collection(card_numbers, True)
    assert result is True

    # Verify updates
    with Session(populated_db.engine) as session:
        for number in card_numbers:
            card = session.query(Card)\
                .filter(Card.card_number == number)\
                .first()

            assert card.collection_status is not None
            assert card.collection_status.is_collected is True
            assert card.collection_status.date_acquired is not None


def test_bulk_update_collection_invalid_cards(populated_db):
    """
    Test bulk update with invalid card numbers.

    Arguments:
        populated_db: Fixture providing DatabaseManager with sample data

    Verifies that:
        - Returns False when invalid card numbers provided
        - No changes are made to database
        - Transaction is properly rolled back
    """
    # Mix of valid and invalid card numbers
    card_numbers = ["INVALID-001", "NOT-A-CARD", "FAKE-999"]

    # Perform bulk update
    result = populated_db.bulk_update_collection(card_numbers, True)
    assert result is False

    # Verify no changes were made
    with Session(populated_db.engine) as session:
        for number in card_numbers:
            card = session.query(Card)\
                .filter(Card.card_number == number)\
                .first()

            assert card is None


def test_add_card_note_new(populated_db):
    """
    Test adding a note to a card without existing notes.

    Arguments:
        populated_db: Fixture providing DatabaseManager with sample data

    Verifies that:
        - Note is added with timestamp
        - Collection status is created if needed
        - Returns True on success
    """
    # Get a test card number
    with Session(populated_db.engine) as session:
        card = session.query(Card).first()
        card_number = card.card_number

    # Add note
    note = "Test note for card"
    result = populated_db.add_card_note(card_number, note)
    assert result is True

    # Verify note was added
    with Session(populated_db.engine) as session:
        card = session.query(Card)\
            .filter(Card.card_number == card_number)\
            .first()

        assert card.collection_status is not None
        assert note in card.collection_status.notes
        assert "[" in card.collection_status.notes  # Has timestamp


def test_add_card_note_append(populated_db):
    """
    Test appending a note to a card with existing notes.

    Arguments:
        populated_db: Fixture providing DatabaseManager with sample data

    Verifies that:
        - New note is appended to existing notes
        - Each note has its own timestamp
        - Original notes are preserved
    """
    # Get a test card and add initial note
    with Session(populated_db.engine) as session:
        card = session.query(Card).first()
        card_number = card.card_number

    # Add first note
    first_note = "First test note"
    populated_db.add_card_note(card_number, first_note)

    # Add second note
    second_note = "Second test note"
    result = populated_db.add_card_note(card_number, second_note)
    assert result is True

    # Verify both notes exist
    with Session(populated_db.engine) as session:
        card = session.query(Card)\
            .filter(Card.card_number == card_number)\
            .first()

        assert first_note in card.collection_status.notes
        assert second_note in card.collection_status.notes
        assert card.collection_status.notes.count("[") == 2  # Two timestamps


def test_add_card_note_invalid_card(populated_db):
    """
    Test adding a note to a non-existent card.

    Arguments:
        populated_db: Fixture providing DatabaseManager with sample data

    Verifies that:
        - Returns False for invalid card number
        - No database changes are made
    """
    result = populated_db.add_card_note("INVALID-001", "Test note")
    assert result is False


def test_update_card_condition_new(populated_db):
    """
    Test updating condition for card without existing status.

    Arguments:
        populated_db: Fixture providing DatabaseManager with sample data

    Verifies that:
        - Collection status is created
        - Misprint flag is set correctly
        - Returns True on success
    """
    # Get a test card number
    with Session(populated_db.engine) as session:
        card = session.query(Card).first()
        card_number = card.card_number

    # Update condition
    result = populated_db.update_card_condition(card_number, True)
    assert result is True

    # Verify condition was updated
    with Session(populated_db.engine) as session:
        card = session.query(Card)\
            .filter(Card.card_number == card_number)\
            .first()

        assert card.collection_status is not None
        assert card.collection_status.is_misprint is True


def test_update_card_condition_existing(populated_db):
    """
    Test updating condition for card with existing status.

    Arguments:
        populated_db: Fixture providing DatabaseManager with sample data

    Verifies that:
        - Existing collection status is preserved
        - Misprint flag is updated
        - Other status flags remain unchanged
    """
    # Get a test card and set initial collection status
    with Session(populated_db.engine) as session:
        card = session.query(Card).first()
        card_number = card.card_number
        if not card.collection_status:
            card.collection_status = CollectionStatus(
                is_collected=True,
                acquisition=Acquisition.PULLED
            )
        session.commit()

    # Update condition
    result = populated_db.update_card_condition(card_number, True)
    assert result is True

    # Verify updates
    with Session(populated_db.engine) as session:
        card = session.query(Card)\
            .filter(Card.card_number == card_number)\
            .first()

        assert card.collection_status.is_misprint is True
        assert card.collection_status.is_collected is True  # Preserved
        assert card.collection_status.acquisition == Acquisition.PULLED  # Preserved


def test_record_trade_success(populated_db):
    """
    Test successful recording of a card trade.

    Arguments:
        populated_db: Fixture providing DatabaseManager with sample data

    Verifies that:
        - Acquired card is marked as collected
        - Traded card is marked as not collected
        - Cross-referenced notes are added to both cards
        - Acquisition method and date are set for acquired card
    """
    # Get two test cards
    with Session(populated_db.engine) as session:
        cards = session.query(Card).limit(2).all()
        acquired_number = cards[0].card_number
        traded_number = cards[1].card_number

    # Record trade
    trade_date = dt.now()
    result = populated_db.record_trade(acquired_number, traded_number, trade_date)
    assert result is True

    # Verify trade was recorded
    with Session(populated_db.engine) as session:
        # Check acquired card
        acquired = session.query(Card)\
            .filter(Card.card_number == acquired_number)\
            .first()

        assert acquired.collection_status.is_collected is True
        assert acquired.collection_status.acquisition == Acquisition.TRADED
        assert acquired.collection_status.date_acquired == trade_date
        assert traded_number in acquired.collection_status.notes

        # Check traded card
        traded = session.query(Card)\
            .filter(Card.card_number == traded_number)\
            .first()

        assert traded.collection_status.is_collected is False
        assert acquired_number in traded.collection_status.notes


def test_record_trade_invalid_cards(populated_db):
    """
    Test trade recording with invalid card numbers.

    Arguments:
        populated_db: Fixture providing DatabaseManager with sample data

    Verifies that:
        - Returns False for invalid card numbers
        - No database changes are made
        - Transaction is properly rolled back
    """
    # Get one valid card number
    with Session(populated_db.engine) as session:
        valid_card = session.query(Card).first()
        valid_number = valid_card.card_number

    # Try trade with invalid card
    result = populated_db.record_trade(valid_number, "INVALID-001")
    assert result is False

    # Verify no changes were made
    with Session(populated_db.engine) as session:
        card = session.query(Card)\
            .filter(Card.card_number == valid_number)\
            .first()

        # Original status should be unchanged
        if card.collection_status:
            assert "INVALID-001" not in card.collection_status.notes


def test_record_trade_promo_card(populated_db):
    """
    Test trading with promo cards.

    Arguments:
        populated_db: Fixture providing DatabaseManager with sample data

    Verifies that:
        - Promo card status is preserved
        - Holo status is preserved for promo cards
        - Trade is recorded successfully
    """
    # Get a promo card and regular card
    with Session(populated_db.engine) as session:
        promo = session.query(Card)\
            .filter(Card.card_number.like("PR-%"))\
            .first()

        regular = session.query(Card)\
            .filter(Card.card_type == CardType.CHARACTER)\
            .first()

        promo_number = promo.card_number
        regular_number = regular.card_number

    # Record trade
    result = populated_db.record_trade(promo_number, regular_number)
    assert result is True

    # Verify promo status preserved
    with Session(populated_db.engine) as session:
        promo = session.query(Card)\
            .filter(Card.card_number == promo_number)\
            .first()

        assert promo.collection_status.is_promo is True
        assert promo.collection_status.is_holo is True  # Promos always holo
