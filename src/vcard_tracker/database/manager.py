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

from pathlib import Path
from typing import Optional, List

from sqlalchemy import create_engine, select, func, and_, or_
from sqlalchemy.orm import Session

from vcard_tracker.database.schema import Base, Card, CollectionStatus, SupportDetails, CharacterDetails, ElementalDetails
from vcard_tracker.models.base import CardType, Element


class DatabaseManager:
    """
    Handles database operations for the card tracker

    Arguments:
        db_path (str): Path to SQLite database file

    Notes:
        Creates database and tables if they don't exist
    """
    def __init__(self, db_path: Union[os.PathLike, str] = "data/database.sqlite"):
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(f"sqlite:///{db_path}", echo=True)
        Base.metadata.create_all(self.engine)


    """
    ╔══════════════════════════╗
    ║ Card Querying Operations ║
    ╚══════════════════════════╝
    """
    def get_card_by_number(self, card_number: str) -> Optional[Card]:
        """
        Retrieve a card by its card number

        Arguments:
            card_number (str): Unique card number

        Returns:
            Card: Card object if found, None otherwise
        """
        with Session(self.engine) as session:
            return session.scalar(
                select(Card).where(Card.card_number == card_number)
            )


    def get_cards_by_type(self, card_type: CardType) -> List[Card]:
        """
        Retrieve all cards of a specific type

        Arguments:
            card_type (CardType): Type of cards to retrieve

        Returns:
            List[Card]: List of matching cards
        """
        with Session(self.engine) as session:
            return list(
                session.scalars(
                    select(Card).where(Card.card_type == card_type)
                )
            )


    def get_cards_by_element(
        self, 
        element: Element,
        include_support: bool = False
    ) -> List[Card]:
        """
        Retrieve all cards of a specific element

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
            stmt = select(Card).where(
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


    def get_cards_by_character_name(
        self, 
        name: str,
        exact_match: bool = True
    ) -> List[Card]:
        """
        Retrieve all cards for a specific character

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
                stmt = select(Card).where(Card.name.ilike(f"%{name}%"))

            return list(session.scalars(stmt))


    def get_character_variants(
        self, 
        character_name: str,
        include_box_topper: bool = True
    ) -> List[Card]:
        """
        Retrieve all variants of a specific character card

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
            stmt = select(Card).where(
                and_(
                    Card.name == character_name,
                    Card.card_type == CardType.CHARACTER
                )
            )

            if not include_box_topper:
                stmt = stmt.join(Card.character_details).where(
                    CharacterDetails.is_box_topper == False
                )

            return list(session.scalars(stmt))


    def get_cards_by_power_level(
        self, 
        power_level: int,
        include_non_character: bool = False
    ) -> List[Card]:
        """
        Retrieve character cards of a specific power level

        Arguments:
            power_level (int): Power level to filter by (8-10)
            include_non_character (bool): Whether to include non-character cards

        Returns:
            List[Card]: List of cards with specified power level

        Notes:
            By default only returns character cards since other types
            don't have power levels. Set include_non_character=True
            to include other card types in results.
        """
        with Session(self.engine) as session:
            stmt = select(Card)

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


    def get_cards_by_illustrator(
        self, 
        illustrator: str,
        exact_match: bool = True
    ) -> List[Card]:
        """
        Retrieve all cards by a specific illustrator

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

            return list(session.scalars(stmt))


    def get_collected_cards(self) -> List[Card]:
        """
        Retrieve all collected cards

        Returns:
            List[Card]: List of collected cards
        """
        with Session(self.engine) as session:
            return list(
                session.scalars(
                    select(Card)
                    .join(Card.collection_status)
                    .where(CollectionStatus.is_collected == True)
                )
            )


    def update_collection_status(
        self, 
        card_number: str, 
        is_collected: bool,
        is_holo: bool = False,
        acquisition: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Update collection status for a card

        Arguments:
            card_number (str): Card number to update
            is_collected (bool): Whether card is collected
            is_holo (bool): Whether card is holographic
            acquisition (str): How card was acquired
            notes (str): Additional notes

        Returns:
            bool: True if update successful, False otherwise
        """
        with Session(self.engine) as session:
            card = session.scalar(
                select(Card).where(Card.card_number == card_number)
            )
            if not card:
                return False

            if not card.collection_status:
                card.collection_status = CollectionStatus()

            card.collection_status.is_collected = is_collected
            card.collection_status.is_holo = is_holo
            if acquisition:
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
    def get_collection_stats(self) -> dict:
        """
        Get statistics about the card collection

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


    def get_missing_cards(self) -> List[Card]:
        """
        Get list of uncollected cards

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


    def get_complete_sets(self) -> List[str]:
        """
        Get list of character names where all variants are collected

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


    def get_recent_acquisitions(self, limit: int = 10) -> List[Card]:
        """
        Get recently acquired cards

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
    def bulk_update_collection(self, card_numbers: List[str], is_collected: bool) -> bool:
        """
        Update collection status for multiple cards at once

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
                        card.collection_status.date_acquired = datetime.now()

                session.commit()
                return True
            except Exception as e:
                session.rollback()
                print(f"Error in bulk update: {e}")
                return False


    def add_card_note(self, card_number: str, note: str) -> bool:
        """
        Add a note to a card's collection status

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

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
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


    def update_card_condition(self, card_number: str, is_misprint: bool) -> bool:
        """
        Update card condition flags

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


    def record_trade(
        self, 
        acquired_card: str, 
        traded_card: str, 
        trade_date: Optional[datetime] = None
    ) -> bool:
        """
        Record a card trade

        Arguments:
            acquired_card (str): Card number of card received
            traded_card (str): Card number of card traded away
            trade_date (datetime): Date of trade, defaults to current time

        Returns:
            bool: True if trade recorded successfully, False otherwise
        """
        if trade_date is None:
            trade_date = datetime.now()

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
    ╔══════════════════════════╗
    ║ Filter/Search Operations ║
    ╚══════════════════════════╝
    """
    def search_cards(
        self, 
        query: str,
        card_type: Optional[CardType] = None,
        element: Optional[Element] = None,
        collected_only: bool = False
    ) -> List[Card]:
        """
        Search cards by name with optional filters

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
    def export_collection(self, filepath: str) -> bool:
        """Export collection data to JSON/CSV"""


    def import_collection(self, filepath: str) -> bool:
        """Import collection data from JSON/CSV"""


    def backup_database(self, backup_path: Optional[str] = None) -> bool:
        """Create a backup of the database"""


    """
    ╔════════════════════════════╗
    ║ Data Validation Operations ║
    ╚════════════════════════════╝
    """
    def validate_card_number(self, card_number: str) -> bool:
        """Check if a card number is valid"""


    def get_duplicate_entries(self) -> List[tuple[str, int]]:
        """Find any duplicate card entries"""


    def verify_database_integrity(self) -> dict:
        """Check for data consistency issues"""

    