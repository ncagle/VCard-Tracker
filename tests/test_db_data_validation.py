# -*- coding: utf-8 -*-
"""
tests.test_db_data_validation.py - VCard-Tracker
Created by NCagle
2025-02-15
      _
   __(.)<
~~~⋱___)~~~

╔═══════════════════════╗
║ Data Validation Tests ║
╚═══════════════════════╝
Tests for data validation database operations.

This module contains tests for the DatabaseManager methods that validate
card number format, check for duplicate entries, and verify data integrity.

✅
❌ Data Validation
    - Validate card number format and uniqueness
    - Check for duplicate entries (card numbers, names, and element mismatches)
    - Verify data and database integrity

"""
from typing import Dict, List
from datetime import datetime as dt

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from vcard_tracker.models.base import Element, CardType
from vcard_tracker.database.schema import (
    Card,
    CharacterDetails,
    CollectionStatus,
    ElementalDetails
)


def test_validate_card_number_valid_formats(populated_db):
    """
    Test card number validation with valid formats for each card type.

    Arguments:
        populated_db: Fixture providing DatabaseManager with sample data

    Notes:
        Tests valid formats:
        - Character cards: CH-001A
        - Support cards: SP-001A
        - Guardian cards: GD-001
        - Shield cards: SH-001
        - Promo cards: PR-0001
    """
    # Test valid formats for each card type
    valid_numbers = [
        "CH-001A",  # Character
        "SP-001A",  # Support
        "GD-001",   # Guardian
        "SH-001",   # Shield
        "PR-0001"   # Promo
    ]

    # Clear any existing cards with these numbers
    with Session(populated_db.engine) as session:
        for number in valid_numbers:
            card = session.scalar(
                select(Card).where(Card.card_number == number)
            )
            if card:
                session.delete(card)
        session.commit()

    # Test each format
    for number in valid_numbers:
        valid, error = populated_db.validate_card_number(number)
        assert valid is True
        assert error is None


def test_validate_card_number_invalid_formats(populated_db):
    """
    Test card number validation with invalid formats.

    Arguments:
        populated_db: Fixture providing DatabaseManager with sample data

    Notes:
        Tests invalid formats:
        - Missing prefix
        - Wrong prefix
        - Invalid number format
        - Missing letter suffix where required
        - Extra characters
    """
    invalid_numbers = [
        "001A",        # Missing prefix
        "XX-001A",     # Wrong prefix
        "CH-A001",     # Wrong number format
        "CH-001",      # Missing letter for character card
        "GD-001A",     # Extra letter for guardian card
        "PR-001",      # Wrong promo format
        "CH-0001A",    # Too many digits
        "CH001A",      # Missing hyphen
        "",            # Empty string
        None,          # None value
    ]

    for number in invalid_numbers:
        valid, error = populated_db.validate_card_number(number)
        assert valid is False
        assert error is not None
        assert "Invalid card number format" in error


def test_validate_card_number_duplicates(populated_db):
    """
    Test card number validation for duplicate numbers.

    Arguments:
        populated_db: Fixture providing DatabaseManager with sample data

    Notes:
        Verifies that:
        - Existing card numbers are rejected
        - Error message indicates duplicate
    """
    # Get an existing card number
    with Session(populated_db.engine) as session:
        existing_number = session.scalar(
            select(Card.card_number)
        )

    # Try to validate the existing number
    valid, error = populated_db.validate_card_number(existing_number)
    assert valid is False
    assert error is not None
    assert "already exists" in error


def test_get_duplicate_entries_clean_db(populated_db):
    """
    Test duplicate detection on a clean database.

    Arguments:
        populated_db: Fixture providing DatabaseManager with sample data

    Notes:
        Verifies that a clean database returns empty duplicate lists.
    """
    duplicates = populated_db.get_duplicate_entries()

    # Verify structure and empty results
    assert isinstance(duplicates, dict)
    assert "duplicate_numbers" in duplicates
    assert "duplicate_names" in duplicates
    assert "mismatched_elements" in duplicates

    assert len(duplicates["duplicate_numbers"]) == 0
    assert len(duplicates["duplicate_names"]) == 0
    assert len(duplicates["mismatched_elements"]) == 0


def test_get_duplicate_entries_duplicate_numbers(populated_db):
    """
    Test detection of duplicate card numbers.

    Arguments:
        populated_db: Fixture providing DatabaseManager with sample data

    Notes:
        Creates test cards with duplicate numbers and verifies detection.
    """
    # Create a duplicate card
    with Session(populated_db.engine) as session:
        # Get an existing card to duplicate
        original = session.scalar(select(Card))

        # Create duplicate with same number
        duplicate = Card(
            name=original.name,
            card_type=original.card_type,
            talent=original.talent,
            edition=original.edition,
            card_number=original.card_number,  # Duplicate number
            illustrator=original.illustrator
        )
        session.add(duplicate)
        session.commit()

        # Check for duplicates
        duplicates = populated_db.get_duplicate_entries()
        assert len(duplicates["duplicate_numbers"]) > 0

        # Verify duplicate info
        dup_info = duplicates["duplicate_numbers"][0]
        assert dup_info["card_number"] == original.card_number
        assert dup_info["count"] == 2
        assert len(dup_info["cards"]) == 2


def test_get_duplicate_entries_name_inconsistencies(populated_db):
    """
    Test detection of name inconsistencies across variants.

    Arguments:
        populated_db: Fixture providing DatabaseManager with sample data

    Notes:
        Creates character variants with inconsistent names and verifies detection.
    """
    # Create character variants with inconsistent names
    with Session(populated_db.engine) as session:
        # Base character
        base_card = Card(
            name="Test Character",
            card_type=CardType.CHARACTER,
            talent="Test talent",
            edition="Test",
            card_number="CH-TEST1",
            illustrator="Test Artist"
        )
        base_card.character_details = CharacterDetails(
            power_level=8,
            element=Element.FIRE,
            age=25,
            height=170.0,
            weight=70.0,
            elemental_strength=Element.GRASS,
            elemental_weakness=Element.WATER
        )
        session.add(base_card)

        # Variant with slightly different name
        variant = Card(
            name="Test Character ",  # Extra space
            card_type=CardType.CHARACTER,
            talent="Test talent",
            edition="Test",
            card_number="CH-TEST2",
            illustrator="Test Artist"
        )
        variant.character_details = CharacterDetails(
            power_level=9,
            element=Element.FIRE,
            age=25,
            height=170.0,
            weight=70.0,
            elemental_strength=Element.GRASS,
            elemental_weakness=Element.WATER
        )
        session.add(variant)
        session.commit()

        # Check for duplicates
        duplicates = populated_db.get_duplicate_entries()
        assert len(duplicates["duplicate_names"]) > 0

        # Verify duplicate info
        dup_info = duplicates["duplicate_names"][0]
        assert "Test Character" in dup_info["name"]
        assert len(dup_info["cards"]) >= 2


def test_get_duplicate_entries_element_mismatches(populated_db):
    """
    Test detection of element mismatches for the same character.

    Arguments:
        populated_db: Fixture providing DatabaseManager with sample data

    Notes:
        Creates character variants with mismatched elements and verifies detection.
    """
    # Create character variants with different elements
    with Session(populated_db.engine) as session:
        # First variant
        card1 = Card(
            name="Element Test",
            card_type=CardType.CHARACTER,
            talent="Test talent",
            edition="Test",
            card_number="CH-ELEM1",
            illustrator="Test Artist"
        )
        card1.character_details = CharacterDetails(
            power_level=8,
            element=Element.FIRE,
            age=25,
            height=170.0,
            weight=70.0,
            elemental_strength=Element.GRASS,
            elemental_weakness=Element.WATER
        )
        session.add(card1)

        # Second variant with different element
        card2 = Card(
            name="Element Test",
            card_type=CardType.CHARACTER,
            talent="Test talent",
            edition="Test",
            card_number="CH-ELEM2",
            illustrator="Test Artist"
        )
        card2.character_details = CharacterDetails(
            power_level=9,
            element=Element.WATER,  # Different element
            age=25,
            height=170.0,
            weight=70.0,
            elemental_strength=Element.GRASS,
            elemental_weakness=Element.FIRE
        )
        session.add(card2)
        session.commit()

        # Check for mismatches
        duplicates = populated_db.get_duplicate_entries()
        assert len(duplicates["mismatched_elements"]) > 0

        # Verify mismatch info
        mismatch = duplicates["mismatched_elements"][0]
        assert mismatch["name"] == "Element Test"
        assert len(mismatch["elements"]) == 2
        assert "FIRE" in mismatch["elements"]
        assert "WATER" in mismatch["elements"]


def test_verify_database_integrity_clean_db(populated_db):
    """
    Test database integrity verification on a clean database.

    Arguments:
        populated_db: Fixture providing DatabaseManager with sample data

    Notes:
        Verifies that a properly structured database reports no issues.
    """
    issues = populated_db.verify_database_integrity()

    # Verify structure
    assert isinstance(issues, dict)
    assert "missing_details" in issues
    assert "invalid_elements" in issues
    assert "collection_issues" in issues
    assert "constraint_violations" in issues

    # A clean database should have no issues
    assert len(issues["missing_details"]) == 0
    assert len(issues["invalid_elements"]) == 0
    assert len(issues["collection_issues"]) == 0
    assert len(issues["constraint_violations"]) == 0


def test_verify_database_integrity_missing_details(populated_db):
    """
    Test detection of missing type-specific details.

    Arguments:
        populated_db: Fixture providing DatabaseManager with sample data

    Notes:
        Creates cards missing required details and verifies detection.
    """
    # Create cards missing required details
    with Session(populated_db.engine) as session:
        # Character card without character details
        card1 = Card(
            name="Missing Details",
            card_type=CardType.CHARACTER,
            talent="Test talent",
            edition="Test",
            card_number="CH-MISS1",
            illustrator="Test Artist"
        )
        session.add(card1)

        # Support card without support details
        card2 = Card(
            name="Missing Support",
            card_type=CardType.SUPPORT,
            talent="Test talent",
            edition="Test",
            card_number="SP-MISS1",
            illustrator="Test Artist"
        )
        session.add(card2)
        session.commit()

        # Check integrity
        issues = populated_db.verify_database_integrity()
        assert len(issues["missing_details"]) > 0

        # Verify issue info
        missing = issues["missing_details"]
        assert any(m["type"] == "CHARACTER" for m in missing)
        assert any(m["type"] == "SUPPORT" for m in missing)


def test_verify_database_integrity_invalid_elements(populated_db):
    """
    Test detection of invalid element assignments.

    Arguments:
        populated_db: Fixture providing DatabaseManager with sample data

    Notes:
        Creates cards with invalid element configurations and verifies detection.
    """
    with Session(populated_db.engine) as session:
        # Character missing elemental strength/weakness
        card = Card(
            name="Invalid Elements",
            card_type=CardType.CHARACTER,
            talent="Test talent",
            edition="Test",
            card_number="CH-ELEM1",
            illustrator="Test Artist"
        )
        card.character_details = CharacterDetails(
            power_level=8,
            element=Element.FIRE,
            age=25,
            height=170.0,
            weight=70.0,
            # Missing elemental_strength and elemental_weakness
        )
        session.add(card)
        session.commit()

        # Check integrity
        issues = populated_db.verify_database_integrity()
        assert len(issues["invalid_elements"]) > 0

        # Verify issue info
        invalid = issues["invalid_elements"]
        assert any("missing_elements" in item for item in invalid)


def test_verify_database_integrity_collection_issues(populated_db):
    """
    Test detection of collection status issues.

    Arguments:
        populated_db: Fixture providing DatabaseManager with sample data

    Notes:
        Creates invalid collection status records and verifies detection.
    """
    with Session(populated_db.engine) as session:
        # Create card with invalid collection status
        card = session.scalar(select(Card))

        # Create invalid collection status
        status = CollectionStatus(
            is_collected=True,
            # Missing required date_acquired for collected card
            card_id=card.id
        )
        session.add(status)
        session.commit()

        # Check integrity
        issues = populated_db.verify_database_integrity()
        assert len(issues["collection_issues"]) > 0

        # Verify issue info
        collection = issues["collection_issues"]
        assert any("Missing acquisition date" in item["issues"]
                  for item in collection)


def test_verify_database_integrity_constraint_violations(populated_db):
    """
    Test detection of game rule constraint violations.

    Arguments:
        populated_db: Fixture providing DatabaseManager with sample data

    Notes:
        Creates cards violating game rules and verifies detection:
        - Level 10 cards must be holo
        - Box toppers cannot have power level
        - Character power levels must be 1 (mascot) or 8-10
        - Promo cards must be holo
    """
    with Session(populated_db.engine) as session:
        # Create level 10 card without holo
        card1 = Card(
            name="Invalid Level 10",
            card_type=CardType.CHARACTER,
            talent="Test talent",
            edition="Test",
            card_number="CH-LVL10",
            illustrator="Test Artist"
        )
        card1.character_details = CharacterDetails(
            power_level=10,  # Level 10
            element=Element.FIRE,
            age=25,
            height=170.0,
            weight=70.0,
            elemental_strength=Element.GRASS,
            elemental_weakness=Element.WATER
        )
        card1.collection_status = CollectionStatus(
            is_holo=False  # Invalid - Level 10 must be holo
        )
        session.add(card1)

        # Create box topper with power level
        card2 = Card(
            name="Invalid Box Topper",
            card_type=CardType.CHARACTER,
            talent="Test talent",
            edition="Test",
            card_number="CH-BOX1",
            illustrator="Test Artist"
        )
        card2.character_details = CharacterDetails(
            power_level=8,  # Invalid - Box toppers shouldn't have power level
            element=Element.WATER,
            age=25,
            height=170.0,
            weight=70.0,
            elemental_strength=Element.GRASS,
            elemental_weakness=Element.FIRE,
            is_box_topper=True
        )
        session.add(card2)

        # Create character with invalid power level
        card3 = Card(
            name="Invalid Power Level",
            card_type=CardType.CHARACTER,
            talent="Test talent",
            edition="Test",
            card_number="CH-PWR1",
            illustrator="Test Artist"
        )
        card3.character_details = CharacterDetails(
            power_level=5,  # Invalid - Must be 1 or 8-10
            element=Element.GRASS,
            age=25,
            height=170.0,
            weight=70.0,
            elemental_strength=Element.FIRE,
            elemental_weakness=Element.WATER
        )
        session.add(card3)

        session.commit()

        # Check integrity
        issues = populated_db.verify_database_integrity()
        assert len(issues["constraint_violations"]) > 0

        # Verify specific violations
        violations = issues["constraint_violations"]

        # Check for level 10 holo violation
        level_10_violation = next(
            (v for v in violations if "CH-LVL10" in v["number"]),
            None
        )
        assert level_10_violation is not None
        assert any("must be holo" in issue
                  for issue in level_10_violation["issues"])

        # Check for box topper violation
        box_topper_violation = next(
            (v for v in violations if "CH-BOX1" in v["number"]),
            None
        )
        assert box_topper_violation is not None
        assert any("should not have power level" in issue
                  for issue in box_topper_violation["issues"])

        # Check for invalid power level violation
        power_level_violation = next(
            (v for v in violations if "CH-PWR1" in v["number"]),
            None
        )
        assert power_level_violation is not None
        assert any("Invalid power level" in issue
                  for issue in power_level_violation["issues"])


def test_verify_database_integrity_orphaned_records(populated_db):
    """
    Test detection of orphaned collection status records.

    Arguments:
        populated_db: Fixture providing DatabaseManager with sample data

    Notes:
        Creates orphaned collection status records and verifies detection.
    """
    with Session(populated_db.engine) as session:
        # Create orphaned collection status
        orphaned = CollectionStatus(
            card_id=999999,  # Non-existent card ID
            is_collected=True,
            date_acquired=dt.now()
        )
        session.add(orphaned)
        session.commit()

        # Check integrity
        issues = populated_db.verify_database_integrity()
        assert len(issues["collection_issues"]) > 0

        # Verify orphaned record detection
        collection = issues["collection_issues"]
        assert any("No associated card" in item["issues"]
                  for item in collection)


def test_verify_database_integrity_element_counts(populated_db):
    """
    Test verification of element counts for guardian/shield cards.

    Arguments:
        populated_db: Fixture providing DatabaseManager with sample data

    Notes:
        Verifies that:
        - Each element has exactly one guardian card
        - Each element has exactly one shield card
    """
    with Session(populated_db.engine) as session:
        # Create extra guardian for an element
        extra_guardian = Card(
            name="Extra Fire Guardian",
            card_type=CardType.GUARDIAN,
            talent="Test talent",
            edition="Test",
            card_number="GD-EXTRA",
            illustrator="Test Artist"
        )
        extra_guardian.elemental_details = ElementalDetails(
            element=Element.FIRE  # Adding extra guardian for FIRE
        )
        session.add(extra_guardian)
        session.commit()

        # Check integrity
        issues = populated_db.verify_database_integrity()
        assert len(issues["invalid_elements"]) > 0

        # Verify element count issue
        invalid = issues["invalid_elements"]
        assert any(
            item["element"] == "FIRE" and
            "exactly one guardian" in item["error"]
            for item in invalid
        )


def test_verify_database_integrity_multiple_issues(populated_db):
    """
    Test detection of multiple integrity issues in the same card.

    Arguments:
        populated_db: Fixture providing DatabaseManager with sample data

    Notes:
        Creates a card with multiple rule violations and verifies all are detected.
    """
    with Session(populated_db.engine) as session:
        # Create card with multiple issues
        problem_card = Card(
            name="Multiple Issues",
            card_type=CardType.CHARACTER,
            talent="Test talent",
            edition="Test",
            card_number="CH-MULTI",
            illustrator="Test Artist"
        )
        problem_card.character_details = CharacterDetails(
            power_level=10,  # Level 10
            element=None,    # Missing element
            age=25,
            height=170.0,
            weight=70.0,
            # Missing elemental strengths/weaknesses
        )
        problem_card.collection_status = CollectionStatus(
            is_collected=True,
            is_holo=False,  # Invalid for level 10
            # Missing acquisition date
        )
        session.add(problem_card)
        session.commit()

        # Check integrity
        issues = populated_db.verify_database_integrity()

        # Card should appear in multiple issue categories
        card_number = "CH-MULTI"

        # Check for element issues
        assert any(
            item["number"] == card_number
            for item in issues["invalid_elements"]
        )

        # Check for constraint violations
        assert any(
            item["number"] == card_number
            for item in issues["constraint_violations"]
        )

        # Card should have multiple specific issues
        violations = next(
            v["issues"] for v in issues["constraint_violations"]
            if v["number"] == card_number
        )
        assert len(violations) > 1  # Should have multiple issues
