"""Repository for PaymentMethod model."""
from typing import Optional, List, Tuple
from uuid import UUID
from decimal import Decimal
from src.repositories.base import BaseRepository
from src.models.payment_method import PaymentMethod, PaymentMethodTranslation


class PaymentMethodRepository(BaseRepository[PaymentMethod]):
    """Repository for PaymentMethod CRUD operations."""

    def __init__(self, session):
        """Initialize repository with session."""
        super().__init__(session=session, model=PaymentMethod)

    def find_by_code(self, code: str) -> Optional[PaymentMethod]:
        """
        Find payment method by code.

        Args:
            code: The unique payment method code

        Returns:
            PaymentMethod if found, None otherwise
        """
        return (
            self._session.query(PaymentMethod)
            .filter(PaymentMethod.code == code)
            .first()
        )

    def find_active(self) -> List[PaymentMethod]:
        """
        Find all active payment methods ordered by position.

        Returns:
            List of active payment methods
        """
        return (
            self._session.query(PaymentMethod)
            .filter(PaymentMethod.is_active == True)
            .order_by(PaymentMethod.position)
            .all()
        )

    def find_all_ordered(self) -> List[PaymentMethod]:
        """
        Find all payment methods ordered by position.

        Returns:
            List of all payment methods
        """
        return self._session.query(PaymentMethod).order_by(PaymentMethod.position).all()

    def find_available(
        self,
        amount: Optional[Decimal] = None,
        currency_code: Optional[str] = None,
        country_code: Optional[str] = None,
    ) -> List[PaymentMethod]:
        """
        Find available payment methods for given criteria.

        Args:
            amount: Order amount (optional)
            currency_code: Currency code (optional)
            country_code: Country code (optional)

        Returns:
            List of available payment methods
        """
        query = (
            self._session.query(PaymentMethod)
            .filter(PaymentMethod.is_active == True)
            .order_by(PaymentMethod.position)
        )

        methods = query.all()

        # Filter in Python for complex JSON field checks
        return [
            m for m in methods if m.is_available(amount, currency_code, country_code)
        ]

    def find_default(self) -> Optional[PaymentMethod]:
        """
        Find the default payment method.

        Returns:
            The default payment method if exists
        """
        return (
            self._session.query(PaymentMethod)
            .filter(PaymentMethod.is_default == True)
            .first()
        )

    def set_default(self, method_id: UUID) -> Optional[PaymentMethod]:
        """
        Set a payment method as default, clearing others.

        Args:
            method_id: The ID of the method to set as default

        Returns:
            The updated payment method
        """
        # Clear existing default
        self._session.query(PaymentMethod).filter(
            PaymentMethod.is_default == True
        ).update({"is_default": False})

        # Set new default
        method = self.find_by_id(method_id)
        if method:
            method.is_default = True
            self._session.commit()
            self._session.refresh(method)

        return method

    def update_positions(self, positions: List[dict]) -> List[PaymentMethod]:
        """
        Update positions for multiple payment methods.

        Args:
            positions: List of {id, position} dicts

        Returns:
            List of updated payment methods
        """
        updated = []
        for item in positions:
            method = self.find_by_id(item["id"])
            if method:
                method.position = item["position"]
                updated.append(method)

        self._session.commit()
        return updated

    def code_exists(self, code: str, exclude_id: Optional[UUID] = None) -> bool:
        """
        Check if a code already exists.

        Args:
            code: The code to check
            exclude_id: Optional ID to exclude from check (for updates)

        Returns:
            True if code exists
        """
        query = self._session.query(PaymentMethod).filter(PaymentMethod.code == code)

        if exclude_id:
            query = query.filter(PaymentMethod.id != exclude_id)

        return query.first() is not None


class PaymentMethodTranslationRepository(BaseRepository[PaymentMethodTranslation]):
    """Repository for PaymentMethodTranslation CRUD operations."""

    def __init__(self, session):
        """Initialize repository with session."""
        super().__init__(session=session, model=PaymentMethodTranslation)

    def find_by_method_and_locale(
        self, payment_method_id: UUID, locale: str
    ) -> Optional[PaymentMethodTranslation]:
        """
        Find translation by payment method ID and locale.

        Args:
            payment_method_id: The payment method ID
            locale: The locale code

        Returns:
            Translation if found, None otherwise
        """
        return (
            self._session.query(PaymentMethodTranslation)
            .filter(
                PaymentMethodTranslation.payment_method_id == payment_method_id,
                PaymentMethodTranslation.locale == locale,
            )
            .first()
        )

    def find_by_method(self, payment_method_id: UUID) -> List[PaymentMethodTranslation]:
        """
        Find all translations for a payment method.

        Args:
            payment_method_id: The payment method ID

        Returns:
            List of translations
        """
        return (
            self._session.query(PaymentMethodTranslation)
            .filter(PaymentMethodTranslation.payment_method_id == payment_method_id)
            .all()
        )

    def upsert(
        self,
        payment_method_id: UUID,
        locale: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        short_description: Optional[str] = None,
        instructions: Optional[str] = None,
    ) -> PaymentMethodTranslation:
        """
        Create or update a translation.

        Args:
            payment_method_id: The payment method ID
            locale: The locale code
            name: Translated name
            description: Translated description
            short_description: Translated short description
            instructions: Translated instructions

        Returns:
            The created or updated translation
        """
        translation = self.find_by_method_and_locale(payment_method_id, locale)

        if translation:
            # Update existing
            if name is not None:
                translation.name = name
            if description is not None:
                translation.description = description
            if short_description is not None:
                translation.short_description = short_description
            if instructions is not None:
                translation.instructions = instructions
        else:
            # Create new
            translation = PaymentMethodTranslation(
                payment_method_id=payment_method_id,
                locale=locale,
                name=name,
                description=description,
                short_description=short_description,
                instructions=instructions,
            )
            self._session.add(translation)

        self._session.commit()
        self._session.refresh(translation)
        return translation
