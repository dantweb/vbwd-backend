"""Currency service implementation."""
from decimal import Decimal
from typing import List, Optional
from src.repositories.currency_repository import CurrencyRepository
from src.models.currency import Currency


class CurrencyService:
    """
    Currency management service.

    Handles currency conversion and exchange rate management.
    """

    def __init__(self, currency_repo: CurrencyRepository):
        """Initialize CurrencyService.

        Args:
            currency_repo: Repository for currency data access
        """
        self._currency_repo = currency_repo

    def get_default_currency(self) -> Currency:
        """Get the default (base) currency.

        Returns:
            Default currency

        Raises:
            ValueError: If no default currency is configured
        """
        currency = self._currency_repo.find_default()
        if not currency:
            raise ValueError("No default currency configured")
        return currency

    def get_active_currencies(self) -> List[Currency]:
        """Get all active currencies.

        Returns:
            List of active currencies
        """
        return self._currency_repo.find_active()

    def get_currency_by_code(self, code: str) -> Optional[Currency]:
        """Get currency by ISO code.

        Args:
            code: ISO 4217 currency code (case-insensitive)

        Returns:
            Currency if found, None otherwise
        """
        return self._currency_repo.find_by_code(code.upper())

    def convert(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str,
    ) -> Decimal:
        """
        Convert amount between currencies.

        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code

        Returns:
            Converted amount

        Raises:
            ValueError: If currency codes are unknown
        """
        # Same currency, no conversion needed
        if from_currency == to_currency:
            return amount.quantize(Decimal("0.01"))

        source = self._currency_repo.find_by_code(from_currency)
        target = self._currency_repo.find_by_code(to_currency)

        if not source or not target:
            raise ValueError(f"Unknown currency: {from_currency} or {to_currency}")

        return source.convert_to(amount, target)

    def update_exchange_rate(self, code: str, rate: Decimal) -> Currency:
        """
        Update exchange rate for currency.

        Args:
            code: Currency code
            rate: New exchange rate relative to default

        Returns:
            Updated currency

        Raises:
            ValueError: If currency not found or is default currency
        """
        currency = self._currency_repo.find_by_code(code)
        if not currency:
            raise ValueError(f"Currency not found: {code}")

        if currency.is_default:
            raise ValueError("Cannot change exchange rate of default currency")

        currency.exchange_rate = rate
        return self._currency_repo.update(currency)
