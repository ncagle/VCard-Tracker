# -*- coding: utf-8 -*-
"""
tests.__init__.py - VCard-Tracker
Created by NCagle
2025-02-03
      _
   __(.)<
~~~⋱___)~~~

Pytest configuration and shared fixtures.

This module contains all shared fixtures and configuration for the test suite.
It automatically gets loaded by pytest without needing to import it explicitly.

Each fixture has a specific scope:
    - session: Created once for the entire test run
    - function: Created fresh for each test function


Basic card creation for each type
Validation rules (especially mascot power levels)
Box topper null attributes
Character card variants
Database operations with the new card formats
"""

import json
from pathlib import Path
from typing import Dict, Generator, Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy_utils import database_exists, create_database, drop_database

from vcard_tracker.database.schema import Base
from vcard_tracker.models.base import Element, CardType, Acquisition
from vcard_tracker.database.manager import DatabaseManager


"""
╔═══════════════════╗
║ Database Fixtures ║
╚═══════════════════╝
"""
@pytest.fixture(scope="session")
def test_db_url() -> str:
    """
    Create a test database URL

    Returns:
        str: SQLite database URL for testing
    """
    return "sqlite:///./test_database.sqlite"


@pytest.fixture(scope="session")
def engine(test_db_url: str):
    """
    Sets up and tears down the test database engine

    Arguments:
        test_db_url (str): Database URL from test_db_url fixture

    Returns:
        Engine: SQLAlchemy engine instance
    """
    engine = create_engine(test_db_url, echo=False)

    # Create database and tables
    if not database_exists(engine.url):
        create_database(engine.url)
    Base.metadata.create_all(engine)

    yield engine

    # Cleanup after all tests
    Base.metadata.drop_all(engine)
    if database_exists(engine.url):
        drop_database(engine.url)


@pytest.fixture(scope="function")
def db_session(engine) -> Generator[Session, None, None]:
    """
    Create a new database session in an isolated session for each test

    Arguments:
        engine: SQLAlchemy engine from engine fixture

    Yields:
        Session: SQLAlchemy session

    Notes:
        - Creates a new session for each test function
        - Handles rollback and cleanup after each test
    """
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    # Rollback and close after each test
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def db_manager(test_db_url: str) -> DatabaseManager:
    """
    Create a DatabaseManager instance for testing.

    Arguments:
        test_db_url (str): Database URL from test_db_url fixture

    Returns:
        DatabaseManager: Instance configured for testing

    Notes:
        Creates a new manager for each test to ensure isolation
    """
    return DatabaseManager(test_db_url)


"""
╔═══════════════╗
║ Data Fixtures ║
╚═══════════════╝
"""
@pytest.fixture(scope="session")
def sample_cards() -> Dict[str, Any]:
    """
    Load sample card data from JSON file

    Returns:
        Dict[str, Any]: Sample card data for testing

    Notes:
        - Loads from tests/data/sample_cards.json
        - Creates empty dict if file doesn't exist
    """
    json_path = Path("tests/data/sample_cards.json")
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


@pytest.fixture(scope="function")
def populated_db(db_manager: DatabaseManager, sample_cards: Dict[str, Any]) -> DatabaseManager:
    """
    Create a DatabaseManager instance with sample data loaded

    Arguments:
        db_manager (DatabaseManager): Clean database manager instance
        sample_cards (Dict[str, Any]): Sample card data

    Returns:
        DatabaseManager: Database manager with sample data loaded

    Notes:
        - Loads all sample cards into the database
        - Handles different card types appropriately
        - Returns manager ready for testing
    """
    # Implementation will be added when we create sample data
    return db_manager


"""
╔══════════════════╗
║ Helper Functions ║
╚══════════════════╝
"""
# Helper functions for test data generation
def create_test_character(
    name: str = "Test Character",
    power_level: int = 8,
    element: Element = Element.FIRE,
    is_holo: bool = False,
    is_box_topper: bool = False,
    is_mascott: bool = False
) -> Dict[str, Any]:
    """
    Create a test character card data dictionary.

    Arguments:
        name (str): Character name
        power_level (int): Power level (8-10)
        element (Element): Character's element
        is_holo (bool): Whether card is holographic
        is_box_topper (bool): Whether card is a box topper
        is_mascott (bool): Whether card is a mascott card

    Returns:
        Dict[str, Any]: Character card data for testing
    """
    if is_box_topper:
        # Box topper has no gameplay attributes
        return {
            "name": name,
            "card_type": CardType.CHARACTER,
            "talent": f"Test talent for {name}",
            "card_number": "001",
            "illustrator": "Test Artist",
            "is_box_topper": True,
            "is_mascott": False,
            "is_holo": True  # Box toppers are always holo
        }
    else:
        # Regular character card with all attributes
        return {
            "name": name,
            "card_type": CardType.CHARACTER,
            "talent": f"Test talent for {name}",
            "card_number": "001",
            "illustrator": "Test Artist",
            "power_level": power_level,
            "element": element,
            "age": "???",  # Changed to string
            "height": "170.0 cm",  # Changed to string with unit
            "weight": "Unknown",  # Changed to string with unit
            "elemental_strength": Element.GRASS,
            "elemental_weakness": Element.WATER,
            "is_box_topper": is_box_topper,
            "is_mascott": is_mascott,
            "is_holo": is_holo
        }


def create_test_support(
    name: str = "Test Support",
    is_holo: bool = False,
    is_secret_rare: bool = False
) -> Dict[str, Any]:
    """
    Create a test support card data dictionary

    Arguments:
        name (str): Support character name
        is_holo (bool): Whether card is holographic
        is_secret_rare (bool): Whether card is secret rare variant

    Returns:
        Dict[str, Any]: Support card data for testing
    """
    return {
        "name": name,
        "card_type": CardType.SUPPORT,
        "talent": f"Test talent for {name}",
        "card_number": f"SP-001",  # Will need proper numbering system
        "illustrator": "Test Artist",
        "is_holo": is_holo,
        "is_secret_rare": is_secret_rare
    }


def create_test_elemental(
    name: str = "Test Guardian",
    card_type: CardType = CardType.GUARDIAN,
    element: Element = Element.FIRE,
    is_holo: bool = False
) -> Dict[str, Any]:
    """
    Create a test guardian/shield card data dictionary

    Arguments:
        name (str): Card name
        card_type (CardType): Either GUARDIAN or SHIELD
        element (Element): Card's element
        is_holo (bool): Whether card is holographic

    Returns:
        Dict[str, Any]: Elemental card data for testing
    """
    prefix = "GD" if card_type == CardType.GUARDIAN else "SH"
    return {
        "name": name,
        "card_type": card_type,
        "talent": f"Test talent for {name}",
        "card_number": f"{prefix}-001",  # Will need proper numbering system
        "illustrator": "Test Artist",
        "element": element,
        "is_holo": is_holo
    }
