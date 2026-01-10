"""Tests for TarifPlanService."""
import pytest
from unittest.mock import Mock
from decimal import Decimal
from uuid import uuid4


class TestTarifPlanServiceGetActive:
    """Test cases for getting active plans."""

    @pytest.fixture
    def mock_plan_repo(self):
        """Mock TarifPlanRepository."""
        return Mock()

    @pytest.fixture
    def tarif_plan_service(self, mock_plan_repo):
        """Create TarifPlanService with mocked dependencies."""
        from src.services.tarif_plan_service import TarifPlanService

        return TarifPlanService(tarif_plan_repo=mock_plan_repo)

    def test_get_active_plans_returns_active_only(
        self, tarif_plan_service, mock_plan_repo
    ):
        """get_active_plans should return only active plans."""
        from src.models.tarif_plan import TarifPlan
        from src.models.enums import BillingPeriod

        plan1 = TarifPlan()
        plan1.id = uuid4()
        plan1.name = "Basic"
        plan1.slug = "basic"
        plan1.is_active = True
        plan1.price_float = 9.99
        plan1.billing_period = BillingPeriod.MONTHLY

        plan2 = TarifPlan()
        plan2.id = uuid4()
        plan2.name = "Pro"
        plan2.slug = "pro"
        plan2.is_active = True
        plan2.price_float = 29.99
        plan2.billing_period = BillingPeriod.MONTHLY

        plans = [plan1, plan2]
        mock_plan_repo.find_active.return_value = plans

        result = tarif_plan_service.get_active_plans()

        assert len(result) == 2
        assert result[0].name == "Basic"
        assert result[1].name == "Pro"
        mock_plan_repo.find_active.assert_called_once()


class TestTarifPlanServiceGetBySlug:
    """Test cases for getting plan by slug."""

    @pytest.fixture
    def mock_plan_repo(self):
        """Mock TarifPlanRepository."""
        return Mock()

    @pytest.fixture
    def tarif_plan_service(self, mock_plan_repo):
        """Create TarifPlanService with mocked dependencies."""
        from src.services.tarif_plan_service import TarifPlanService

        return TarifPlanService(tarif_plan_repo=mock_plan_repo)

    def test_get_plan_by_slug_returns_plan(self, tarif_plan_service, mock_plan_repo):
        """get_plan_by_slug should return plan if found."""
        from src.models.tarif_plan import TarifPlan

        plan = TarifPlan()
        plan.id = uuid4()
        plan.slug = "pro"
        plan.name = "Pro Plan"

        mock_plan_repo.find_by_slug.return_value = plan

        result = tarif_plan_service.get_plan_by_slug("pro")

        assert result is not None
        assert result.slug == "pro"
        mock_plan_repo.find_by_slug.assert_called_once_with("pro")

    def test_get_plan_by_slug_returns_none_if_not_found(
        self, tarif_plan_service, mock_plan_repo
    ):
        """get_plan_by_slug should return None if not found."""
        mock_plan_repo.find_by_slug.return_value = None

        result = tarif_plan_service.get_plan_by_slug("nonexistent")

        assert result is None


class TestTarifPlanServiceGetById:
    """Test cases for getting plan by ID."""

    @pytest.fixture
    def mock_plan_repo(self):
        """Mock TarifPlanRepository."""
        return Mock()

    @pytest.fixture
    def tarif_plan_service(self, mock_plan_repo):
        """Create TarifPlanService with mocked dependencies."""
        from src.services.tarif_plan_service import TarifPlanService

        return TarifPlanService(tarif_plan_repo=mock_plan_repo)

    def test_get_plan_by_id_returns_plan(self, tarif_plan_service, mock_plan_repo):
        """get_plan_by_id should return plan if found."""
        from src.models.tarif_plan import TarifPlan

        plan_id = uuid4()
        plan = TarifPlan()
        plan.id = plan_id
        plan.name = "Pro Plan"

        mock_plan_repo.find_by_id.return_value = plan

        result = tarif_plan_service.get_plan_by_id(plan_id)

        assert result is not None
        assert result.id == plan_id
        mock_plan_repo.find_by_id.assert_called_once_with(plan_id)


class TestTarifPlanServiceGetWithPricing:
    """Test cases for getting plan with pricing details."""

    @pytest.fixture
    def mock_plan_repo(self):
        """Mock TarifPlanRepository."""
        return Mock()

    @pytest.fixture
    def mock_currency_service(self):
        """Mock CurrencyService."""
        return Mock()

    @pytest.fixture
    def mock_tax_service(self):
        """Mock TaxService."""
        return Mock()

    @pytest.fixture
    def tarif_plan_service(
        self, mock_plan_repo, mock_currency_service, mock_tax_service
    ):
        """Create TarifPlanService with mocked dependencies."""
        from src.services.tarif_plan_service import TarifPlanService

        return TarifPlanService(
            tarif_plan_repo=mock_plan_repo,
            currency_service=mock_currency_service,
            tax_service=mock_tax_service,
        )

    def test_get_plan_with_pricing_includes_currency(
        self, tarif_plan_service, mock_currency_service
    ):
        """get_plan_with_pricing should include currency information."""
        from src.models.tarif_plan import TarifPlan
        from src.models.currency import Currency
        from src.models.enums import BillingPeriod

        plan = TarifPlan()
        plan.id = uuid4()
        plan.name = "Pro Plan"
        plan.slug = "pro"
        plan.price_float = 29.99
        plan.billing_period = BillingPeriod.MONTHLY
        plan.is_active = True

        currency = Currency()
        currency.code = "USD"
        currency.symbol = "$"

        mock_currency_service.get_currency_by_code.return_value = currency

        result = tarif_plan_service.get_plan_with_pricing(plan, currency_code="USD")

        assert result["name"] == "Pro Plan"
        assert result["display_currency"] == "USD"
        assert "display_price" in result
        mock_currency_service.get_currency_by_code.assert_called_once_with("USD")

    def test_get_plan_with_pricing_includes_tax_breakdown(
        self, tarif_plan_service, mock_currency_service, mock_tax_service
    ):
        """get_plan_with_pricing should include tax breakdown if country provided."""
        from src.models.tarif_plan import TarifPlan
        from src.models.currency import Currency
        from src.models.enums import BillingPeriod

        plan = TarifPlan()
        plan.id = uuid4()
        plan.name = "Pro Plan"
        plan.price_float = 100.00
        plan.billing_period = BillingPeriod.MONTHLY

        currency = Currency()
        currency.code = "EUR"

        tax_breakdown = {
            "net_amount": Decimal("100.00"),
            "tax_amount": Decimal("19.00"),
            "gross_amount": Decimal("119.00"),
            "tax_rate": Decimal("19.0"),
            "tax_name": "German VAT",
        }

        mock_currency_service.get_currency_by_code.return_value = currency
        mock_tax_service.get_tax_breakdown.return_value = tax_breakdown

        result = tarif_plan_service.get_plan_with_pricing(
            plan, currency_code="EUR", country_code="DE"
        )

        assert result["net_price"] == Decimal("100.00")
        assert result["tax_amount"] == Decimal("19.00")
        assert result["gross_price"] == Decimal("119.00")
        assert result["tax_rate"] == Decimal("19.0")
        mock_tax_service.get_tax_breakdown.assert_called_once()
