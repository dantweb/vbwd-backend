"""Tax service implementation."""
from decimal import Decimal
from typing import Optional
from src.repositories.tax_repository import TaxRepository
from src.models.tax import Tax


class TaxService:
    """
    Tax calculation service.

    Handles VAT and regional tax calculations.
    """

    def __init__(self, tax_repo: TaxRepository):
        """Initialize TaxService.

        Args:
            tax_repo: Repository for tax data access
        """
        self._tax_repo = tax_repo

    def get_applicable_tax(
        self,
        country_code: str,
        region_code: Optional[str] = None,
    ) -> Optional[Tax]:
        """
        Get applicable tax for location.

        Args:
            country_code: ISO country code
            region_code: Optional state/region code

        Returns:
            Applicable Tax or None
        """
        taxes = self._tax_repo.find_by_country(country_code)

        # Filter by region if specified
        if region_code:
            regional = [t for t in taxes if t.region_code == region_code]
            if regional:
                return regional[0]

        # Return country-level tax
        country_taxes = [t for t in taxes if not t.region_code]
        return country_taxes[0] if country_taxes else None

    def calculate_tax(
        self,
        net_amount: Decimal,
        tax_code: str,
    ) -> Decimal:
        """
        Calculate tax amount.

        Args:
            net_amount: Amount before tax
            tax_code: Tax code to apply

        Returns:
            Tax amount (returns 0.00 if tax not found)
        """
        tax = self._tax_repo.find_by_code(tax_code)
        if not tax:
            return Decimal("0.00")
        return tax.calculate(net_amount)

    def calculate_total_with_tax(
        self,
        net_amount: Decimal,
        tax_code: str,
    ) -> Decimal:
        """
        Calculate gross amount including tax.

        Args:
            net_amount: Amount before tax
            tax_code: Tax code to apply

        Returns:
            Gross amount (net + tax)
        """
        tax = self._tax_repo.find_by_code(tax_code)
        if not tax:
            return net_amount
        return tax.calculate_gross(net_amount)

    def get_tax_breakdown(
        self,
        net_amount: Decimal,
        country_code: str,
        region_code: Optional[str] = None,
    ) -> dict:
        """
        Get detailed tax breakdown for an amount.

        Args:
            net_amount: Amount before tax
            country_code: ISO country code
            region_code: Optional state/region code

        Returns:
            Dictionary with net, tax, gross, and tax details
        """
        tax = self.get_applicable_tax(country_code, region_code)

        if not tax:
            return {
                "net_amount": net_amount,
                "tax_amount": Decimal("0.00"),
                "gross_amount": net_amount,
                "tax_code": None,
                "tax_rate": Decimal("0.00"),
            }

        tax_amount = tax.calculate(net_amount)

        return {
            "net_amount": net_amount,
            "tax_amount": tax_amount,
            "gross_amount": net_amount + tax_amount,
            "tax_code": tax.code,
            "tax_rate": tax.rate,
            "tax_name": tax.name,
        }
