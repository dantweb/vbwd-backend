"""Tests for CurrencyService."""
import pytest
from unittest.mock import Mock
from decimal import Decimal
from uuid import uuid4


class TestCurrencyServiceGetDefault:
    """Test cases for get_default_currency."""

    @pytest.fixture
    def mock_currency_repo(self):
        """Mock CurrencyRepository."""
        return Mock()

    @pytest.fixture
    def currency_service(self, mock_currency_repo):
        """Create CurrencyService with mocked dependencies."""
        from src.services.currency_service import CurrencyService
        return CurrencyService(currency_repo=mock_currency_repo)

    def test_get_default_currency_returns_default(self, currency_service, mock_currency_repo):
        """get_default_currency should return the default currency."""
        from src.models.currency import Currency

        default_currency = Currency()
        default_currency.id = uuid4()
        default_currency.code = "EUR"
        default_currency.name = "Euro"
        default_currency.symbol = "€"
        default_currency.exchange_rate = Decimal("1.0")
        default_currency.is_default = True

        mock_currency_repo.find_default.return_value = default_currency

        result = currency_service.get_default_currency()

        assert result.code == "EUR"
        assert result.is_default is True
        mock_currency_repo.find_default.assert_called_once()

    def test_get_default_currency_raises_if_none(self, currency_service, mock_currency_repo):
        """get_default_currency should raise if no default currency."""
        mock_currency_repo.find_default.return_value = None

        with pytest.raises(ValueError, match="No default currency"):
            currency_service.get_default_currency()


class TestCurrencyServiceConvert:
    """Test cases for currency conversion."""

    @pytest.fixture
    def mock_currency_repo(self):
        """Mock CurrencyRepository."""
        return Mock()

    @pytest.fixture
    def currency_service(self, mock_currency_repo):
        """Create CurrencyService with mocked dependencies."""
        from src.services.currency_service import CurrencyService
        return CurrencyService(currency_repo=mock_currency_repo)

    def test_convert_amount_between_currencies(self, currency_service, mock_currency_repo):
        """convert should convert amount between currencies."""
        from src.models.currency import Currency

        eur = Currency()
        eur.code = "EUR"
        eur.exchange_rate = Decimal("1.0")
        eur.decimal_places = 2

        usd = Currency()
        usd.code = "USD"
        usd.exchange_rate = Decimal("1.08")
        usd.decimal_places = 2

        mock_currency_repo.find_by_code.side_effect = lambda c: eur if c == "EUR" else usd

        result = currency_service.convert(Decimal("100"), "EUR", "USD")

        assert result == Decimal("108.00")
        assert mock_currency_repo.find_by_code.call_count == 2

    def test_convert_same_currency_returns_same_amount(self, currency_service, mock_currency_repo):
        """convert should return same amount for same currency."""
        result = currency_service.convert(Decimal("100"), "EUR", "EUR")

        assert result == Decimal("100.00")
        # Should not call repository for same currency
        mock_currency_repo.find_by_code.assert_not_called()

    def test_convert_raises_for_unknown_currency(self, currency_service, mock_currency_repo):
        """convert should raise for unknown currency."""
        mock_currency_repo.find_by_code.return_value = None

        with pytest.raises(ValueError, match="Unknown currency"):
            currency_service.convert(Decimal("100"), "EUR", "XXX")


class TestCurrencyServiceGetActive:
    """Test cases for get_active_currencies."""

    @pytest.fixture
    def mock_currency_repo(self):
        """Mock CurrencyRepository."""
        return Mock()

    @pytest.fixture
    def currency_service(self, mock_currency_repo):
        """Create CurrencyService with mocked dependencies."""
        from src.services.currency_service import CurrencyService
        return CurrencyService(currency_repo=mock_currency_repo)

    def test_get_active_currencies_returns_list(self, currency_service, mock_currency_repo):
        """get_active_currencies should return active currencies."""
        from src.models.currency import Currency

        eur = Currency()
        eur.code = "EUR"
        eur.is_active = True

        usd = Currency()
        usd.code = "USD"
        usd.is_active = True

        currencies = [eur, usd]
        mock_currency_repo.find_active.return_value = currencies

        result = currency_service.get_active_currencies()

        assert len(result) == 2
        assert result[0].code == "EUR"
        assert result[1].code == "USD"
        mock_currency_repo.find_active.assert_called_once()


class TestCurrencyServiceGetByCode:
    """Test cases for get_currency_by_code."""

    @pytest.fixture
    def mock_currency_repo(self):
        """Mock CurrencyRepository."""
        return Mock()

    @pytest.fixture
    def currency_service(self, mock_currency_repo):
        """Create CurrencyService with mocked dependencies."""
        from src.services.currency_service import CurrencyService
        return CurrencyService(currency_repo=mock_currency_repo)

    def test_get_currency_by_code_returns_currency(self, currency_service, mock_currency_repo):
        """get_currency_by_code should return currency."""
        from src.models.currency import Currency

        usd = Currency()
        usd.code = "USD"
        usd.name = "US Dollar"
        mock_currency_repo.find_by_code.return_value = usd

        result = currency_service.get_currency_by_code("USD")

        assert result is not None
        assert result.code == "USD"
        mock_currency_repo.find_by_code.assert_called_once_with("USD")

    def test_get_currency_by_code_uppercases_code(self, currency_service, mock_currency_repo):
        """get_currency_by_code should uppercase the code."""
        from src.models.currency import Currency

        usd = Currency()
        usd.code = "USD"
        mock_currency_repo.find_by_code.return_value = usd

        result = currency_service.get_currency_by_code("usd")

        assert result is not None
        mock_currency_repo.find_by_code.assert_called_once_with("USD")
