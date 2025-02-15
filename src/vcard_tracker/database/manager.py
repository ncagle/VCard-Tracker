# -*- coding: utf-8 -*-
"""
src.vcard_tracker.database.manager.py - VCard-Tracker
Created by NCagle
2025-02-03
      _
   __(.)<
~~~⋱___)~~~

<Description>

Example Usage:
# Get all character cards
character_cards = db.get_cards_by_type(CardType.CHARACTER)

# Update collection status
db.update_collection_status(
    card_number="CH001",
    is_collected=True,
    is_holo=True,
    acquisition="PULLED",
    notes="First pack!"
)
"""

# Standard library imports
import json
import os
import re
import shutil
from datetime import datetime as dt
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

# SQLAlchemy imports
from sqlalchemy import (
    create_engine,
    func,
    select,
    and_,
    or_,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Enum
)
from sqlalchemy.orm import (
    Session,
    joinedload,
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship
)

# Application-specific imports
# This import block includes all necessary imports for:
# - Basic database operations
# - Card querying operations
# - Collection analysis operations
# - Collection management operations
# - Filter/Search operations
# - Import/Export operations
# - Data validation operations
from vcard_tracker.models.base import (
    Element,
    CardType,
    Acquisition
)
from vcard_tracker.database.schema import (
    Base,
    Card,
    CharacterDetails,
    SupportDetails,
    ElementalDetails,
    CollectionStatus
)


class DatabaseManager:
    """
    Handles database operations for the card tracker

    Card Querying
        - Basic Card Queries
            - Get by card number
            - Get by card type
            - Get by element
            - Get by card art illustrator
        - Character-Specific Queries
            - Get by character name
            - Get all variants of a character
            - Get by power level
            - Include/exclude box toppers
        - Collection Queries
            - Get cards in collection
            - Update status of card in collection
            - Error handling for non-existent cards

    Collection Analysis
        - Get collection progress statistics
        - Find missing cards from collection
        - Check for complete character sets
        - View recent card acquisitions

    Collection Management
        - Update multiple cards at once
        - Add notes to card
        - Update card condition flags
        - Record card trades

    Data Validation
        - Validate card number format
        - Check for duplicate entries
        - Verify data and database integrity

    Filter/Search
        - Search cards with text and filters
        - Apply complex multi-criteria filters

    Import/Export
        - Export collection to file
        - Import collection from file
        - Create database backups

    Arguments:
        db_path (str): Path to SQLite database file

    Notes:
        Creates database and tables if they don't exist
    """
    def __init__(self, db_path: Union[os.PathLike, str] = "data/database.sqlite"):
        """
        Initialize the database manager.
        
        Arguments:
            db_path: Path to SQLite database file. Can be either a file path or SQLite URL.
        """
        # If it's a SQLite URL, extract the file path
        if isinstance(db_path, str) and db_path.startswith("sqlite:///"):
            db_path = db_path.replace("sqlite:///", "")

        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(f"sqlite:///{db_path}", echo=True)
        Base.metadata.create_all(self.engine)


    """
    ╔══════════════════════════╗
    ║ Card Querying Operations ║
    ╚══════════════════════════╝
    """
    # ~~~~~ Basic Card Queries ~~~~~
    # Get by card number
    def get_card_by_number(
        self,
        card_number: str
    ) -> Optional[Card]:
        """
        Retrieves a single card using its unique card number identifier
        Returns None if no card is found with the given number
        Most precise lookup method since card numbers are unique

        Arguments:
            card_number (str): Unique card number

        Returns:
            Card: Card object if found, None otherwise
        """
        with Session(self.engine) as session:
            return session.scalar(
                select(Card)
                .options(
                    joinedload(Card.character_details),
                    joinedload(Card.support_details),
                    joinedload(Card.elemental_details),
                    joinedload(Card.collection_status)
                )
                .where(Card.card_number == card_number)
            )


    # Get by card type
    def get_cards_by_type(
        self,
        card_type: CardType
    ) -> List[Card]:
        """
        Retrieves all cards of a specified type (Character, Support, Guardian, Shield)
        Returns an empty list if no cards found of that type
        Basic filtering method that serves as foundation for more complex queries

        Arguments:
            card_type (CardType): Type of cards to retrieve

        Returns:
            List[Card]: List of matching cards
        """
        with Session(self.engine) as session:
            return list(
                session.scalars(
                    select(Card)
                    .options(
                        joinedload(Card.character_details),
                        joinedload(Card.support_details),
                        joinedload(Card.elemental_details),
                        joinedload(Card.collection_status)
                    )
                    .where(Card.card_type == card_type)
                )
            )


    # Get by element
    def get_cards_by_element(
        self,
        element: Element,
        include_support: bool = False
    ) -> List[Card]:
        """
        Retrieve all cards of a specific element
        Option to include/exclude support cards (which don't have elements)
        Handles both character and guardian/shield cards appropriately

        Arguments:
            element (Element): Element to filter by
            include_support (bool): Whether to include support cards that don't have elements

        Returns:
            List[Card]: List of cards with the specified element

        Notes:
            By default excludes support cards since they don't have elements.
            Set include_support=True to include them in results.
        """
        with Session(self.engine) as session:
            # Build base query
            stmt = (
                select(Card)
                .options(
                    joinedload(Card.character_details),
                    joinedload(Card.support_details),
                    joinedload(Card.elemental_details),
                    joinedload(Card.collection_status)
                )
                .where(
                    or_(
                        # Character cards
                        and_(
                            Card.card_type == CardType.CHARACTER,
                            Card.character_details.has(element=element)
                        ),
                        # Guardian/Shield cards
                        and_(
                            Card.card_type.in_([CardType.GUARDIAN, CardType.SHIELD]),
                            Card.elemental_details.has(element=element)
                        )
                    )
                )
            )

            # Include support cards if requested
            if include_support:
                stmt = stmt.where(
                    or_(
                        Card.card_type == CardType.SUPPORT,
                        Card.card_type != CardType.SUPPORT
                    )
                )
            else:
                stmt = stmt.where(Card.card_type != CardType.SUPPORT)

            return list(session.scalars(stmt))


    # Get by card art illustrator
    def get_cards_by_illustrator(
        self,
        illustrator: str,
        exact_match: bool = True
    ) -> List[Card]:
        """
        Retrieve all cards by a specific illustrator
        Supports exact or partial matching
        Case-insensitive when using partial matching

        Arguments:
            illustrator (str): Illustrator name to search for
            exact_match (bool): Whether to require exact name match

        Returns:
            List[Card]: List of cards by the specified illustrator

        Notes:
            With exact_match=False, performs case-insensitive partial matching
        """
        with Session(self.engine) as session:
            if exact_match:
                stmt = select(Card).where(Card.illustrator == illustrator)
            else:
                stmt = select(Card).where(
                    Card.illustrator.ilike(f"%{illustrator}%")
                )

            stmt = stmt.options(
                joinedload(Card.character_details),
                joinedload(Card.support_details),
                joinedload(Card.elemental_details),
                joinedload(Card.collection_status)
            )

            return list(session.scalars(stmt))


    # ~~~~~ Character-Specific Queries ~~~~~
    # Get by character name
    def get_cards_by_character_name(
        self,
        name: str,
        exact_match: bool = True
    ) -> List[Card]:
        """
        Retrieve all cards for a specific character
        Supports exact or partial matching
        Case-insensitive when using partial matching

        Arguments:
            name (str): Character name to search for
            exact_match (bool): Whether to require exact name match

        Returns:
            List[Card]: List of cards matching the character name

        Notes:
            With exact_match=False, performs case-insensitive partial matching
        """
        with Session(self.engine) as session:
            if exact_match:
                stmt = select(Card).where(Card.name == name)
            else:
                stmt = select(Card).where(
                    Card.name.ilike(f"%{name}%")
                )

            stmt = stmt.options(
                joinedload(Card.character_details),
                joinedload(Card.support_details),
                joinedload(Card.elemental_details),
                joinedload(Card.collection_status)
            )

            return list(session.scalars(stmt))


    # Get all variants of a character
    def get_character_variants(
        self,
        character_name: str,
        include_box_topper: bool = True
    ) -> List[Card]:
        """
        Retrieve all variants of a specific character card
        Option to include/exclude box topper variants
        Only returns character cards (not support/guardian/shield)

        Arguments:
            character_name (str): Name of character to get variants for
            include_box_topper (bool): Whether to include box topper variant

        Returns:
            List[Card]: List of all variants for the character

        Notes:
            Returns all variants (Mascott, Level 8/9/10) for a character.
            Box topper included by default but can be excluded.
        """
        with Session(self.engine) as session:
            stmt = (
                select(Card)
                .options(
                    joinedload(Card.character_details),
                    joinedload(Card.collection_status)
                )
                .where(
                    and_(
                        Card.name == character_name,
                        Card.card_type == CardType.CHARACTER
                    )
                )
            )

            if not include_box_topper:
                stmt = stmt.join(Card.character_details).where(
                    CharacterDetails.is_box_topper == False
                )

            return list(session.scalars(stmt))


    # Get by power level
    def get_cards_by_power_level(
        self,
        power_level: int,
        include_non_character: bool = False
    ) -> List[Card]:
        """
        Retrieve character cards of a specific power level
        Option to include non-character cards in results
        Handles power level filtering properly for character cards

        Arguments:
            power_level (int): Power level to filter by (1 for mascot, 8-10 for regular)
            include_non_character (bool): Whether to include non-character cards

        Returns:
            List[Card]: List of cards with specified power level

        Notes:
            By default only returns character cards since other types
            don't have power levels. Set include_non_character=True
            to include other card types in results.
        """
        with Session(self.engine) as session:
            stmt = (
                select(Card)
                .options(
                    joinedload(Card.character_details),
                    joinedload(Card.collection_status)
                )
            )

            if include_non_character:
                stmt = stmt.where(
                    or_(
                        and_(
                            Card.card_type == CardType.CHARACTER,
                            Card.character_details.has(power_level=power_level)
                        ),
                        Card.card_type != CardType.CHARACTER
                    )
                )
            else:
                stmt = stmt.where(
                    and_(
                        Card.card_type == CardType.CHARACTER,
                        Card.character_details.has(power_level=power_level)
                    )
                )

            return list(session.scalars(stmt))


    # ~~~~~ Collection Queries ~~~~~
    # Get cards in collection
    def get_collected_cards(self) -> List[Card]:
        """
        Returns all cards marked as collected in the database
        Joins Card and CollectionStatus tables to check collection status
        Returns only cards where is_collected = True in CollectionStatus

        Returns:
            List[Card]: List of collected cards
        """
        with Session(self.engine) as session:
            return list(
                session.scalars(
                    select(Card)
                    .options(
                        joinedload(Card.character_details),
                        joinedload(Card.support_details),
                        joinedload(Card.elemental_details),
                        joinedload(Card.collection_status)
                    )
                    .join(Card.collection_status)
                    .where(CollectionStatus.is_collected == True)
                )
            )


    # Update status of card in collection
    def update_collection_status(
        self,
        card_number: str, 
        is_collected: bool,
        is_holo: bool = False,
        acquisition: Optional[Acquisition] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Updates multiple collection attributes at once
        (collected status, holo status, acquisition method, notes)
        Creates new CollectionStatus record if one doesn't exist for the card
        Returns boolean indicating whether update was successful

        Arguments:
            card_number (str): Card number to update
            is_collected (bool): Whether card is collected
            is_holo (bool): Whether card is holographic
            acquisition (Acquisition): How card was acquired (enum value)
            notes (str): Additional notes

        Returns:
            bool: True if update successful, False otherwise
        """
        with Session(self.engine) as session:
            card = session.scalar(
                select(Card)
                .options(joinedload(Card.collection_status))
                .where(Card.card_number == card_number)
            )
            if not card:
                return False

            if not card.collection_status:
                card.collection_status = CollectionStatus()

            card.collection_status.is_collected = is_collected
            card.collection_status.is_holo = is_holo
            if acquisition is not None:  # Only update if explicitly provided
                card.collection_status.acquisition = acquisition
            if notes:
                card.collection_status.notes = notes

            session.commit()
            return True


    """
    ╔════════════════════════════════╗
    ║ Collection Analysis Operations ║
    ╚════════════════════════════════╝
    """
    # Get collection progress statistics
    def get_collection_stats(self) -> dict:
        """
        Get statistics about the card collection
        Calculates overall completion percentage
        Breaks down collected cards by type
        Tracks holo and secret rare counts

        Returns:
            dict: Dictionary containing collection statistics:
                - total_collected: int
                - total_cards: int
                - completion_percentage: float
                - collected_by_type: dict[CardType, int]
                - total_holos: int
                - total_secret_rares: int
        """
        with Session(self.engine) as session:
            # Get total cards and collected cards
            total_cards = session.scalar(select(func.count()).select_from(Card))
            total_collected = session.scalar(
                select(func.count())
                .select_from(Card)
                .join(Card.collection_status)
                .where(CollectionStatus.is_collected == True)
            )

            # Get counts by card type
            collected_by_type = {}
            for card_type in CardType:
                collected_by_type[card_type] = session.scalar(
                    select(func.count())
                    .select_from(Card)
                    .join(Card.collection_status)
                    .where(
                        and_(
                            Card.card_type == card_type,
                            CollectionStatus.is_collected == True
                        )
                    )
                )

            # Get holo and secret rare counts
            total_holos = session.scalar(
                select(func.count())
                .select_from(Card)
                .join(Card.collection_status)
                .where(
                    and_(
                        CollectionStatus.is_collected == True,
                        CollectionStatus.is_holo == True
                    )
                )
            )

            total_secret_rares = session.scalar(
                select(func.count())
                .select_from(Card)
                .join(Card.collection_status)
                .join(Card.support_details)
                .where(
                    and_(
                        CollectionStatus.is_collected == True,
                        SupportDetails.is_secret_rare == True
                    )
                )
            )

            return {
                "total_collected": total_collected,
                "total_cards": total_cards,
                "completion_percentage": (total_collected / total_cards * 100) if total_cards else 0,
                "collected_by_type": collected_by_type,
                "total_holos": total_holos,
                "total_secret_rares": total_secret_rares
            }


    # Find missing cards from collection
    def get_missing_cards(self) -> List[Card]:
        """
        Get list of uncollected cards
        Handles both NULL and False collection status

        Returns:
            List[Card]: List of cards not marked as collected
        """
        with Session(self.engine) as session:
            return list(
                session.scalars(
                    select(Card)
                    .outerjoin(Card.collection_status)
                    .where(
                        or_(
                            CollectionStatus.is_collected.is_(None),
                            CollectionStatus.is_collected == False
                        )
                    )
                )
            )


    # Check for complete character sets
    def get_complete_sets(self) -> List[str]:
        """
        Get list of character names where all variants are collected
        Takes into account the specific variants needed for completion

        Returns:
            List[str]: Names of characters with complete collections

        Notes:
            A complete set means having all variants for a character:
            - Regular and Holo Mascott
            - Regular and Holo Level 8
            - Regular and Holo Level 9
            - Holo Level 10
            - Box Topper
        """
        with Session(self.engine) as session:
            # Get all character names
            character_names = session.scalars(
                select(Card.name)
                .join(Card.character_details)
                .distinct()
            ).all()

            complete_sets = []

            for name in character_names:
                # Get all variants for this character
                variants = session.scalars(
                    select(Card)
                    .join(Card.character_details)
                    .where(Card.name == name)
                ).all()

                # Check if all variants are collected
                all_collected = all(
                    variant.collection_status and variant.collection_status.is_collected
                    for variant in variants
                )

                if all_collected:
                    complete_sets.append(name)

            return complete_sets


    # View recent card acquisitions
    def get_recent_acquisitions(
        self,
        limit: int = 10
    ) -> List[Card]:
        """
        Get recently acquired cards
        Allows limiting the number of results

        Arguments:
            limit (int): Maximum number of cards to return

        Returns:
            List[Card]: List of recently acquired cards, sorted by acquisition date
        """
        with Session(self.engine) as session:
            return list(
                session.scalars(
                    select(Card)
                    .join(Card.collection_status)
                    .where(CollectionStatus.is_collected == True)
                    .order_by(CollectionStatus.date_acquired.desc())
                    .limit(limit)
                )
            )


    """
    ╔══════════════════════════════════╗
    ║ Collection Management Operations ║
    ╚══════════════════════════════════╝
    """
    # Update multiple cards at once
    def bulk_update_collection(
        self,
        card_numbers: List[str],
        is_collected: bool
    ) -> bool:
        """
        Update collection status for multiple cards at once
        Sets acquisition date for newly collected cards
        Uses transaction rollback for error handling

        Arguments:
            card_numbers (List[str]): List of card numbers to update
            is_collected (bool): Whether cards are collected

        Returns:
            bool: True if all updates successful, False if any failed
        """
        with Session(self.engine) as session:
            try:
                # Get all cards in one query
                cards = session.scalars(
                    select(Card).where(Card.card_number.in_(card_numbers))
                ).all()

                for card in cards:
                    if not card.collection_status:
                        card.collection_status = CollectionStatus()

                    card.collection_status.is_collected = is_collected
                    if is_collected and not card.collection_status.date_acquired:
                        card.collection_status.date_acquired = dt.now()

                session.commit()
                return True
            except Exception as e:
                session.rollback()
                print(f"Error in bulk update: {e}")
                return False


    # Add notes to card
    def add_card_note(
        self,
        card_number: str,
        note: str
    ) -> bool:
        """
        Add a note to a card's collection status
        Timestamps all notes
        Appends new notes to existing ones
        Maintains note history

        Arguments:
            card_number (str): Card number to update
            note (str): Note to add to the card

        Returns:
            bool: True if update successful, False otherwise

        Notes:
            If the card already has notes, the new note is appended with a timestamp
        """
        with Session(self.engine) as session:
            try:
                card = session.scalar(
                    select(Card).where(Card.card_number == card_number)
                )
                if not card:
                    return False

                if not card.collection_status:
                    card.collection_status = CollectionStatus()

                timestamp = dt.now().strftime("%Y-%m-%d %H:%M")
                if card.collection_status.notes:
                    card.collection_status.notes += f"\n[{timestamp}] {note}"
                else:
                    card.collection_status.notes = f"[{timestamp}] {note}"

                session.commit()
                return True
            except Exception as e:
                session.rollback()
                print(f"Error adding note: {e}")
                return False


    # Update card condition flags
    def update_card_condition(
        self,
        card_number: str,
        is_misprint: bool
    ) -> bool:
        """
        Update card condition flags
        Simple interface for updating misprint status
        Creates collection status if needed

        Arguments:
            card_number (str): Card number to update
            is_misprint (bool): Whether card is a misprint

        Returns:
            bool: True if update successful, False otherwise
        """
        with Session(self.engine) as session:
            try:
                card = session.scalar(
                    select(Card).where(Card.card_number == card_number)
                )
                if not card:
                    return False

                if not card.collection_status:
                    card.collection_status = CollectionStatus()

                card.collection_status.is_misprint = is_misprint

                session.commit()
                return True
            except Exception as e:
                session.rollback()
                print(f"Error updating condition: {e}")
                return False


    # Record card trades
    def record_trade(
        self,
        acquired_card: str,
        traded_card: str,
        trade_date: Optional[dt] = None
    ) -> bool:
        """
        Record a card trade
        Records both sides of the trade
        Timestamps the transaction
        Adds cross-referenced notes to both cards
        Updates collection status appropriately

        Arguments:
            acquired_card (str): Card number of card received
            traded_card (str): Card number of card traded away
            trade_date (dt): Date of trade, defaults to current time

        Returns:
            bool: True if trade recorded successfully, False otherwise
        """
        if trade_date is None:
            trade_date = dt.now()

        with Session(self.engine) as session:
            try:
                # Get both cards in a single query
                acquired, traded = session.scalars(
                    select(Card).where(
                        Card.card_number.in_([acquired_card, traded_card])
                    )
                ).all()

                if not acquired or not traded:
                    return False

                # Initialize collection status if needed
                if not acquired.collection_status:
                    acquired.collection_status = CollectionStatus()
                if not traded.collection_status:
                    traded.collection_status = CollectionStatus()

                # Update acquired card
                acquired.collection_status.is_collected = True
                acquired.collection_status.acquisition = Acquisition.TRADED
                acquired.collection_status.date_acquired = trade_date
                acquired.collection_status.notes = (
                    f"[{trade_date.strftime('%Y-%m-%d %H:%M')}] "
                    f"Acquired in trade for {traded.name} ({traded.card_number})"
                )

                # Update traded card
                traded.collection_status.is_collected = False
                traded.collection_status.notes = (
                    f"[{trade_date.strftime('%Y-%m-%d %H:%M')}] "
                    f"Traded for {acquired.name} ({acquired.card_number})"
                )

                session.commit()
                return True
            except Exception as e:
                session.rollback()
                print(f"Error recording trade: {e}")
                return False


    """
    ╔════════════════════════════╗
    ║ Data Validation Operations ║
    ╚════════════════════════════╝
    """
    # Validate card number format
    def validate_card_number(
        self,
        card_number: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates card number format and uniqueness using regex patterns for each card type
        Checks for uniqueness in the database
        Returns validation status and detailed error message if invalid

        Arguments:
            card_number (str): Card number to validate

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
                - is_valid: Whether the card number is valid
                - error_message: Description of validation failure if any

        Notes:
            Validates:
            - Correct format per card type
            - Number exists in valid range
            - No duplicate numbers
        """
        if not card_number:
            return False, "Card number cannot be empty"

        # Define expected formats for different card types
        patterns = {
            "character": r"^CH-\d{3}[A-Z]$",    # CH-001A
            "support": r"^SP-\d{3}[A-Z]$",      # SP-001A
            "guardian": r"^GD-\d{3}$",          # GD-001
            "shield": r"^SH-\d{3}$",            # SH-001
            "promo": r"^PR-\d{4}$"              # PR-0001
        }

        # Check format
        valid_format = any(
            re.match(pattern, card_number)
            for pattern in patterns.values()
        )
        if not valid_format:
            return False, "Invalid card number format"

        # Check for duplicates
        with Session(self.engine) as session:
            existing = session.scalar(
                select(Card).where(Card.card_number == card_number)
            )
            if existing:
                return False, "Card number already exists"

        return True, None


    # Check for duplicate entries
    def get_duplicate_entries(self) -> Dict[str, List[Dict]]:
        """
        Finds multiple types of potential duplicates in the database
        Checks for duplicate card numbers, name inconsistencies, and element mismatches

        Returns:
            Returns detailed information about found duplicates for investigation
            Dict[str, List[Dict]]: Dictionary of duplicate types and their instances:
                - duplicate_numbers: Cards with same number
                - duplicate_names: Cards with same name (excluding variants)
                - mismatched_elements: Cards with conflicting elements

        Notes:
            Helps identify:
            - Accidentally duplicated card numbers
            - Name inconsistencies across variants
            - Element mismatches for same character
        """
        duplicates = {
            "duplicate_numbers": [],
            "duplicate_names": [],
            "mismatched_elements": []
        }

        with Session(self.engine) as session:
            # Check for duplicate card numbers
            number_count = (
                select(Card.card_number, func.count(Card.id).label("count"))
                .group_by(Card.card_number)
                .having(func.count(Card.id) > 1)
            )

            for number, count in session.execute(number_count):
                cards = session.scalars(
                    select(Card).where(Card.card_number == number)
                ).all()
                duplicates["duplicate_numbers"].append({
                    "card_number": number,
                    "count": count,
                    "cards": [
                        {"id": c.id, "name": c.name, "type": c.card_type.name}
                        for c in cards
                    ]
                })

            # Check for name inconsistencies across variants
            # (excluding intentional variants like mascott/levels)
            stmt = (
                select(Card.name, func.count(Card.id).label("count"))
                .where(Card.card_type == CardType.CHARACTER)
                .group_by(Card.name)
                .having(func.count(Card.id) > 8)  # More variants than expected
            )

            for name, count in session.execute(stmt):
                cards = session.scalars(
                    select(Card).where(Card.name == name)
                ).all()
                duplicates["duplicate_names"].append({
                    "name": name,
                    "count": count,
                    "cards": [
                        {"id": c.id, "number": c.card_number, "type": c.card_type.name}
                        for c in cards
                    ]
                })

            # Check for element mismatches
            characters = session.scalars(
                select(Card)
                .where(Card.card_type == CardType.CHARACTER)
                .join(Card.character_details)
            ).all()

            # Group by name and check elements
            by_name = {}
            for char in characters:
                if char.name not in by_name:
                    by_name[char.name] = set()
                by_name[char.name].add(char.character_details.element)

            # Record any with multiple elements
            for name, elements in by_name.items():
                if len(elements) > 1:
                    cards = session.scalars(
                        select(Card)
                        .where(Card.name == name)
                        .join(Card.character_details)
                    ).all()
                    duplicates["mismatched_elements"].append({
                        "name": name,
                        "elements": [e.name for e in elements],
                        "cards": [
                            {
                                "id": c.id,
                                "number": c.card_number,
                                "element": c.character_details.element.name
                            }
                            for c in cards
                        ]
                    })

        return duplicates


    # Verify data and database integrity
    def verify_database_integrity(self) -> Dict[str, List[Dict]]:
        """
        Perform comprehensive database integrity check
            - Missing type-specific details
            - Invalid element assignments
            - Collection status issues
            - Game rule constraint violations

        Returns:
            Returns detailed report of all found issues
            Dict[str, List[Dict]]: Dictionary of integrity issues found:
                - missing_details: Cards missing type-specific details
                - invalid_elements: Cards with invalid element assignments
                - collection_issues: Problems with collection status records
                - constraint_violations: Cards violating game rules

        Notes:
            Verifies:
            - All cards have appropriate type-specific details
            - Elements are assigned correctly per card type
            - Collection status records are valid
            - Game rule constraints are maintained
        """
        issues = {
            "missing_details": [],
            "invalid_elements": [],
            "collection_issues": [],
            "constraint_violations": []
        }

        with Session(self.engine) as session:
            # Check for missing type-specific details
            all_cards = session.scalars(select(Card)).all()
            for card in all_cards:
                details_missing = []

                if card.card_type == CardType.CHARACTER:
                    if not card.character_details:
                        details_missing.append("character_details")
                elif card.card_type == CardType.SUPPORT:
                    if not card.support_details:
                        details_missing.append("support_details")
                elif card.card_type in (CardType.GUARDIAN, CardType.SHIELD):
                    if not card.elemental_details:
                        details_missing.append("elemental_details")

                if details_missing:
                    issues["missing_details"].append({
                        "id": card.id,
                        "number": card.card_number,
                        "name": card.name,
                        "type": card.card_type.name,
                        "missing": details_missing
                    })

            # Check for invalid element assignments
            # Characters must have valid element and strength/weakness
            character_cards = session.scalars(
                select(Card)
                .where(Card.card_type == CardType.CHARACTER)
                .join(Card.character_details)
            ).all()

            for card in character_cards:
                details = card.character_details
                if not details.element or not details.elemental_strength or not details.elemental_weakness:
                    issues["invalid_elements"].append({
                        "id": card.id,
                        "number": card.card_number,
                        "name": card.name,
                        "missing_elements": {
                            "main": not details.element,
                            "strength": not details.elemental_strength,
                            "weakness": not details.elemental_weakness
                        }
                    })

            # Guardian/Shield cards must have exactly one element
            elemental_cards = session.scalars(
                select(Card)
                .where(Card.card_type.in_([CardType.GUARDIAN, CardType.SHIELD]))
                .join(Card.elemental_details)
            ).all()

            element_counts = {e: 0 for e in Element}
            for card in elemental_cards:
                if card.elemental_details and card.elemental_details.element:
                    element_counts[card.elemental_details.element] += 1

            for element, count in element_counts.items():
                if count != 2:  # Should be exactly 1 guardian + 1 shield
                    issues["invalid_elements"].append({
                        "element": element.name,
                        "count": count,
                        "error": "Each element should have exactly one guardian and one shield card"
                    })

            # Check collection status issues
            collection_records = session.scalars(
                select(CollectionStatus)
            ).all()

            for status in collection_records:
                status_issues = []

                # Check for orphaned records
                if not status.card:
                    status_issues.append("No associated card")

                # Check for invalid dates
                if status.is_collected and not status.date_acquired:
                    status_issues.append("Missing acquisition date")

                # Check for invalid acquisition methods
                if status.is_collected and not status.acquisition:
                    status_issues.append("Missing acquisition method")

                if status_issues:
                    issues["collection_issues"].append({
                        "id": status.id,
                        "card_id": status.card_id,
                        "issues": status_issues
                    })

            # Check game rule constraint violations
            for card in character_cards:
                constraint_issues = []
                details = card.character_details

                # Power level constraints
                if details.power_level not in (8, 9, 10):
                    constraint_issues.append(
                        f"Invalid power level: {details.power_level}"
                    )

                # Level 10 must be holo
                if details.power_level == 10:
                    if card.collection_status and not card.collection_status.is_holo:
                        constraint_issues.append("Level 10 card must be holo")

                # Box topper cannot have power level
                if details.is_box_topper and details.power_level:
                    constraint_issues.append(
                        "Box topper should not have power level"
                    )

                if constraint_issues:
                    issues["constraint_violations"].append({
                        "id": card.id,
                        "number": card.card_number,
                        "name": card.name,
                        "issues": constraint_issues
                    })

        return issues


    """
    ╔══════════════════════════╗
    ║ Filter/Search Operations ║
    ╚══════════════════════════╝
    """
    # Search cards with text and filters
    def search_cards(
        self,
        query: str,
        card_type: Optional[CardType] = None,
        element: Optional[Element] = None,
        collected_only: bool = False
    ) -> List[Card]:
        """
        Search cards by name with optional filters
        Case-insensitive partial name matching
        Optional filters for card type and element
        Handles element filtering across different card types
        Option to only show collected cards

        Arguments:
            query (str): Search string for card name
            card_type (CardType): Optional filter by card type
            element (Element): Optional filter by element
            collected_only (bool): If True, only return collected cards

        Returns:
            List[Card]: List of matching cards

        Notes:
            Search is case-insensitive and matches partial names
        """
        with Session(self.engine) as session:
            # Start with base query
            stmt = select(Card).where(
                Card.name.ilike(f"%{query}%")
            )

            # Add type filter if specified
            if card_type:
                stmt = stmt.where(Card.card_type == card_type)

            # Add element filter if specified
            if element:
                # Need to handle different card types
                element_filter = or_(
                    # Character cards
                    and_(
                        Card.card_type == CardType.CHARACTER,
                        Card.character_details.has(element=element)
                    ),
                    # Guardian/Shield cards
                    and_(
                        Card.card_type.in_([CardType.GUARDIAN, CardType.SHIELD]),
                        Card.elemental_details.has(element=element)
                    )
                )
                stmt = stmt.where(element_filter)

            # Add collection filter if specified
            if collected_only:
                stmt = stmt.join(Card.collection_status).where(
                    CollectionStatus.is_collected == True
                )

            return list(session.scalars(stmt))


    # Apply complex multi-criteria filters
    def get_filtered_cards(
        self,
        card_types: Optional[List[CardType]] = None,
        elements: Optional[List[Element]] = None,
        power_levels: Optional[List[int]] = None,
        is_holo: Optional[bool] = None,
        is_collected: Optional[bool] = None,
        is_secret_rare: Optional[bool] = None,
        is_box_topper: Optional[bool] = None,
        is_mascott: Optional[bool] = None,
    ) -> List[Card]:
        """
        Get cards matching multiple filter criteria
        Comprehensive filtering system
        All filters are optional
        Handles card-type specific filters (e.g., power level only for character cards)
        Complex SQL query building with proper joins
        Maintains proper type relationships (e.g., secret rare only applies to support cards)

        Arguments:
            card_types (List[CardType]): Filter by card types
            elements (List[Element]): Filter by elements
            power_levels (List[int]): Filter by power levels (character cards only)
            is_holo (bool): Filter by holographic status
            is_collected (bool): Filter by collection status
            is_secret_rare (bool): Filter support cards by secret rare status
            is_box_topper (bool): Filter character cards by box topper status
            is_mascott (bool): Filter character cards by mascott status

        Returns:
            List[Card]: List of cards matching all specified criteria
        """
        with Session(self.engine) as session:
            # Start with base query
            stmt = select(Card)

            # Add type filter
            if card_types:
                stmt = stmt.where(Card.card_type.in_(card_types))

            # Add element filter
            if elements:
                element_filter = or_(
                    # Character cards
                    and_(
                        Card.card_type == CardType.CHARACTER,
                        Card.character_details.has(
                            CharacterDetails.element.in_(elements)
                        )
                    ),
                    # Guardian/Shield cards
                    and_(
                        Card.card_type.in_([CardType.GUARDIAN, CardType.SHIELD]),
                        Card.elemental_details.has(
                            ElementalDetails.element.in_(elements)
                        )
                    )
                )
                stmt = stmt.where(element_filter)

            # Add power level filter (character cards only)
            if power_levels:
                stmt = stmt.where(
                    or_(
                        Card.character_details.has(
                            CharacterDetails.power_level.in_(power_levels)
                        ),
                        Card.card_type != CardType.CHARACTER
                    )
                )

            # Add collection status filters
            if is_collected is not None or is_holo is not None:
                stmt = stmt.join(Card.collection_status)
                if is_collected is not None:
                    stmt = stmt.where(CollectionStatus.is_collected == is_collected)
                if is_holo is not None:
                    stmt = stmt.where(CollectionStatus.is_holo == is_holo)

            # Add secret rare filter (support cards only)
            if is_secret_rare is not None:
                stmt = stmt.where(
                    or_(
                        and_(
                            Card.card_type == CardType.SUPPORT,
                            Card.support_details.has(
                                SupportDetails.is_secret_rare == is_secret_rare
                            )
                        ),
                        Card.card_type != CardType.SUPPORT
                    )
                )

            # Add character card specific filters
            if is_box_topper is not None or is_mascott is not None:
                character_filters = []
                if is_box_topper is not None:
                    character_filters.append(
                        CharacterDetails.is_box_topper == is_box_topper
                    )
                if is_mascott is not None:
                    character_filters.append(
                        CharacterDetails.is_mascott == is_mascott
                    )

                stmt = stmt.where(
                    or_(
                        and_(
                            Card.card_type == CardType.CHARACTER,
                            Card.character_details.has(and_(*character_filters))
                        ),
                        Card.card_type != CardType.CHARACTER
                    )
                )

            return list(session.scalars(stmt))


    """
    ╔══════════════════════════╗
    ║ Import/Export Operations ║
    ╚══════════════════════════╝
    """
    # Export collection to file
    def export_collection(
        self,
        export_path: Union[str, Path],
        include_notes: bool = True
    ) -> bool:
        """
        Exports collected cards to JSON format with collection metadata
        Option to include/exclude collection notes
        Includes card identification, collection date, status flags, and acquisition info

        Arguments:
            export_path (Union[str, Path]): Path to save export file
            include_notes (bool): Whether to include collection notes

        Returns:
            bool: True if export successful, False otherwise

        Notes:
            Exports collection status for all collected cards including:
            - Card number
            - Collection date
            - Holo status
            - Misprint status
            - Acquisition method
            - Notes (optional)
        """
        try:
            with Session(self.engine) as session:
                # Get all collected cards with their status
                collected_cards = session.scalars(
                    select(Card)
                    .join(Card.collection_status)
                    .where(CollectionStatus.is_collected == True)
                ).all()

                # Build export data
                export_data = []
                for card in collected_cards:
                    status = card.collection_status
                    card_data = {
                        "card_number": card.card_number,
                        "name": card.name,
                        "date_acquired": status.date_acquired.isoformat() 
                            if status.date_acquired else None,
                        "is_holo": status.is_holo,
                        "is_misprint": status.is_misprint,
                        "acquisition": status.acquisition.name 
                            if status.acquisition else None,
                    }
                    if include_notes and status.notes:
                        card_data["notes"] = status.notes
                    export_data.append(card_data)

                # Save to file
                export_path = Path(export_path)
                with open(export_path, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "exported_at": dt.now().isoformat(),
                            "cards": export_data
                        },
                        f,
                        indent=2,
                        ensure_ascii=False
                    )
                return True

        except Exception as e:
            print(f"Export failed: {e}")
            return False


    # Import collection from file
    def import_collection(
        self,
        import_path: Union[str, Path],
        merge_strategy: str = "skip"
    ) -> Dict[str, int]:
        """
        Imports collection data from JSON file with flexible merge strategies
        Validates card numbers and data format before importing
        Returns detailed statistics about import results (imported/skipped/failed/updated)

        Arguments:
            import_path (Union[str, Path]): Path to import file
            merge_strategy (str): How to handle existing entries:
                - "skip": Skip if card already collected
                - "update": Update existing collection status
                - "replace": Replace all existing collection data

        Returns:
            Dict[str, int]: Import statistics:
                - imported: Number of cards imported
                - skipped: Number of cards skipped
                - failed: Number of cards that failed to import
                - updated: Number of cards updated

        Notes:
            Expected JSON format matches export_collection output.
            Verifies card numbers exist before importing.
        """
        stats = {"imported": 0, "skipped": 0, "failed": 0, "updated": 0}

        try:
            # Load import data
            import_path = Path(import_path)
            with open(import_path, "r", encoding="utf-8") as f:
                import_data = json.load(f)

            if "cards" not in import_data:
                raise ValueError("Invalid import file format")

            with Session(self.engine) as session:
                # Handle replace strategy
                if merge_strategy == "replace":
                    # Delete all existing collection status
                    session.query(CollectionStatus).delete()
                    session.commit()

                # Process each card
                for card_data in import_data["cards"]:
                    try:
                        card_number = card_data["card_number"]

                        # Get card
                        card = session.scalar(
                            select(Card).where(Card.card_number == card_number)
                        )
                        if not card:
                            stats["failed"] += 1
                            continue

                        # Check existing collection status
                        if card.collection_status and card.collection_status.is_collected:
                            if merge_strategy == "skip":
                                stats["skipped"] += 1
                                continue
                            elif merge_strategy == "update":
                                stats["updated"] += 1
                        else:
                            stats["imported"] += 1

                        # Create or update collection status
                        if not card.collection_status:
                            card.collection_status = CollectionStatus()

                        status = card.collection_status
                        status.is_collected = True
                        status.is_holo = card_data.get("is_holo", False)
                        status.is_misprint = card_data.get("is_misprint", False)

                        if "date_acquired" in card_data and card_data["date_acquired"]:
                            status.date_acquired = dt.fromisoformat(
                                card_data["date_acquired"]
                            )

                        if "acquisition" in card_data and card_data["acquisition"]:
                            status.acquisition = Acquisition[card_data["acquisition"]]

                        if "notes" in card_data:
                            status.notes = card_data["notes"]

                    except Exception as e:
                        print(f"Failed to import card {card_data.get('card_number')}: {e}")
                        stats["failed"] += 1
                        continue

                session.commit()
                return stats

        except Exception as e:
            print(f"Import failed: {e}")
            return stats


    # Create database backups
    def backup_database(
        self,
        backup_dir: Union[str, Path],
        include_images: bool = True
    ) -> bool:
        """
        Creates complete backup including database file, images (optional), and collection export
        Uses timestamped backup directories for organization
        Option to include/exclude card image backups

        Arguments:
            backup_dir (Union[str, Path]): Directory to store backup
            include_images (bool): Whether to backup card images

        Returns:
            bool: True if backup successful, False otherwise

        Notes:
            Creates timestamped copies of:
            - SQLite database file
            - Card images directory (optional)
            - Collection export JSON
        """
        try:
            backup_dir = Path(backup_dir)
            timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = backup_dir / f"backup_{timestamp}"
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Backup database file
            db_backup = backup_dir / "database.sqlite"
            shutil.copy2(self.engine.url.database, db_backup)

            # Backup card images
            if include_images:
                image_dir = Path("data/card_images")
                if image_dir.exists():
                    image_backup = backup_dir / "card_images"
                    shutil.copytree(image_dir, image_backup)

            # Export collection data
            collection_backup = backup_dir / "collection.json"
            self.export_collection(collection_backup)

            return True

        except Exception as e:
            print(f"Backup failed: {e}")
            return False
