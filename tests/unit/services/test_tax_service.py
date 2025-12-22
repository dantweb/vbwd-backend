"""Tests for TaxService."""
import pytest
from unittest.mock import Mock
from decimal import Decimal
from uuid import uuid4


class TestTaxServiceGetApplicable:
    """Test cases for getting applicable taxes."""

    @pytest.fixture
    def mock_tax_repo(self):
        """Mock TaxRepository."""
        return Mock()

    @pytest.fixture
    def tax_service(self, mock_tax_repo):
        """Create TaxService with mocked dependencies."""
        from src.services.tax_service import TaxService
        return TaxService(tax_repo=mock_tax_repo)

    def test_get_applicable_tax_for_country(self, tax_service, mock_tax_repo):
        """get_applicable_tax should return tax for country."""
        from src.models.tax import Tax

        vat_de = Tax()
        vat_de.id = uuid4()
        vat_de.code = "VAT_DE"
        vat_de.rate = Decimal("19.0")
        vat_de.country_code = "DE"
        vat_de.region_code = None

        mock_tax_repo.find_by_country.return_value = [vat_de]

        result = tax_service.get_applicable_tax("DE")

        assert result is not None
        assert result.code == "VAT_DE"
        assert result.rate == Decimal("19.0")
        mock_tax_repo.find_by_country.assert_called_once_with("DE")

    def test_get_applicable_tax_returns_none_if_not_found(self, tax_service, mock_tax_repo):
        """get_applicable_tax should return None if no tax configured."""
        mock_tax_repo.find_by_country.return_value = []

        result = tax_service.get_applicable_tax("XX")

        assert result is None
        mock_tax_repo.find_by_country.assert_called_once_with("XX")

    def test_get_applicable_tax_prefers_regional_tax(self, tax_service, mock_tax_repo):
        """get_applicable_tax should prefer regional tax over country tax."""
        from src.models.tax import Tax

        country_tax = Tax()
        country_tax.code = "VAT_US"
        country_tax.country_code = "US"
        country_tax.region_code = None
        country_tax.rate = Decimal("0.0")

        regional_tax = Tax()
        regional_tax.code = "SALES_TAX_CA"
        regional_tax.country_code = "US"
        regional_tax.region_code = "CA"
        regional_tax.rate = Decimal("7.25")

        mock_tax_repo.find_by_country.return_value = [country_tax, regional_tax]

        result = tax_service.get_applicable_tax("US", region_code="CA")

        assert result is not None
        assert result.code == "SALES_TAX_CA"
        assert result.rate == Decimal("7.25")


class TestTaxServiceCalculate:
    """Test cases for tax calculations."""

    @pytest.fixture
    def mock_tax_repo(self):
        """Mock TaxRepository."""
        return Mock()

    @pytest.fixture
    def tax_service(self, mock_tax_repo):
        """Create TaxService with mocked dependencies."""
        from src.services.tax_service import TaxService
        return TaxService(tax_repo=mock_tax_repo)

    def test_calculate_tax_for_amount(self, tax_service, mock_tax_repo):
        """calculate_tax should compute tax amount."""
        from src.models.tax import Tax

        vat = Tax()
        vat.code = "VAT_DE"
        vat.rate = Decimal("19.0")

        mock_tax_repo.find_by_code.return_value = vat

        result = tax_service.calculate_tax(Decimal("100.00"), "VAT_DE")

        assert result == Decimal("19.00")
        mock_tax_repo.find_by_code.assert_called_once_with("VAT_DE")

    def test_calculate_tax_returns_zero_if_tax_not_found(self, tax_service, mock_tax_repo):
        """calculate_tax should return zero if tax not found."""
        mock_tax_repo.find_by_code.return_value = None

        result = tax_service.calculate_tax(Decimal("100.00"), "INVALID_TAX")

        assert result == Decimal("0.00")

    def test_calculate_total_with_tax(self, tax_service, mock_tax_repo):
        """calculate_total_with_tax should return gross amount."""
        from src.models.tax import Tax

        vat = Tax()
        vat.code = "VAT_DE"
        vat.rate = Decimal("19.0")

        mock_tax_repo.find_by_code.return_value = vat

        result = tax_service.calculate_total_with_tax(Decimal("100.00"), "VAT_DE")

        assert result == Decimal("119.00")

    def test_calculate_total_with_tax_returns_net_if_tax_not_found(self, tax_service, mock_tax_repo):
        """calculate_total_with_tax should return net if tax not found."""
        mock_tax_repo.find_by_code.return_value = None

        result = tax_service.calculate_total_with_tax(Decimal("100.00"), "INVALID_TAX")

        assert result == Decimal("100.00")


class TestTaxServiceGetBreakdown:
    """Test cases for tax breakdown."""

    @pytest.fixture
    def mock_tax_repo(self):
        """Mock TaxRepository."""
        return Mock()

    @pytest.fixture
    def tax_service(self, mock_tax_repo):
        """Create TaxService with mocked dependencies."""
        from src.services.tax_service import TaxService
        return TaxService(tax_repo=mock_tax_repo)

    def test_get_tax_breakdown_with_tax(self, tax_service, mock_tax_repo):
        """get_tax_breakdown should return detailed breakdown."""
        from src.models.tax import Tax

        vat_de = Tax()
        vat_de.code = "VAT_DE"
        vat_de.name = "German VAT"
        vat_de.rate = Decimal("19.0")
        vat_de.country_code = "DE"
        vat_de.region_code = None

        mock_tax_repo.find_by_country.return_value = [vat_de]

        result = tax_service.get_tax_breakdown(Decimal("100.00"), "DE")

        assert result["net_amount"] == Decimal("100.00")
        assert result["tax_amount"] == Decimal("19.00")
        assert result["gross_amount"] == Decimal("119.00")
        assert result["tax_code"] == "VAT_DE"
        assert result["tax_rate"] == Decimal("19.0")
        assert result["tax_name"] == "German VAT"

    def test_get_tax_breakdown_without_tax(self, tax_service, mock_tax_repo):
        """get_tax_breakdown should handle no tax case."""
        mock_tax_repo.find_by_country.return_value = []

        result = tax_service.get_tax_breakdown(Decimal("100.00"), "XX")

        assert result["net_amount"] == Decimal("100.00")
        assert result["tax_amount"] == Decimal("0.00")
        assert result["gross_amount"] == Decimal("100.00")
        assert result["tax_code"] is None
        assert result["tax_rate"] == Decimal("0.00")
