"""Tests for PaymentMethod model.

TDD RED PHASE: These tests are written BEFORE implementation.
All tests should FAIL initially until the PaymentMethod model is implemented.
"""
import pytest
from uuid import uuid4
from decimal import Decimal


class TestPaymentMethodModel:
    """Test cases for PaymentMethod model."""

    def test_payment_method_has_required_fields(self):
        """PaymentMethod should have all required fields."""
        from src.models.payment_method import PaymentMethod

        method = PaymentMethod(
            code="invoice",
            name="Invoice",
        )

        assert method.code == "invoice"
        assert method.name == "Invoice"

    def test_payment_method_has_optional_fields(self):
        """PaymentMethod should support optional fields."""
        from src.models.payment_method import PaymentMethod

        method = PaymentMethod(
            code="stripe",
            name="Credit Card",
            description="Pay with credit or debit card",
            short_description="Card payment",
            icon="credit-card",
            plugin_id="stripe-plugin",
            is_active=True,
            is_default=False,
            position=1,
            min_amount=Decimal("1.00"),
            max_amount=Decimal("10000.00"),
            currencies=["EUR", "USD"],
            countries=["DE", "AT", "CH"],
            fee_type="percentage",
            fee_amount=Decimal("2.9"),
            fee_charged_to="customer",
            instructions="You will be redirected to Stripe.",
        )

        assert method.description == "Pay with credit or debit card"
        assert method.short_description == "Card payment"
        assert method.icon == "credit-card"
        assert method.plugin_id == "stripe-plugin"
        assert method.is_active is True
        assert method.is_default is False
        assert method.position == 1
        assert method.min_amount == Decimal("1.00")
        assert method.max_amount == Decimal("10000.00")
        assert method.currencies == ["EUR", "USD"]
        assert method.countries == ["DE", "AT", "CH"]
        assert method.fee_type == "percentage"
        assert method.fee_amount == Decimal("2.9")
        assert method.fee_charged_to == "customer"
        assert method.instructions == "You will be redirected to Stripe."

    def test_payment_method_defaults(self):
        """PaymentMethod column defaults should be defined correctly."""
        from src.models.payment_method import PaymentMethod

        # Test that column defaults are defined (not applied to instances)
        # Defaults are applied when persisting to database, not on object creation
        columns = {c.name: c for c in PaymentMethod.__table__.columns}

        # Verify default definitions exist for expected columns
        assert columns["is_active"].default.arg is True
        assert columns["is_default"].default.arg is False
        assert columns["position"].default.arg == 0
        assert columns["fee_type"].default.arg == "none"
        assert columns["fee_charged_to"].default.arg == "customer"

        # Verify callable defaults are set (for list/dict columns)
        assert callable(columns["currencies"].default.arg)
        assert callable(columns["countries"].default.arg)
        assert callable(columns["config"].default.arg)

        # Test the callable defaults return expected values
        assert columns["currencies"].default.arg(None) == []
        assert columns["countries"].default.arg(None) == []
        assert columns["config"].default.arg(None) == {}

    def test_payment_method_to_dict(self):
        """PaymentMethod.to_dict() should return proper dictionary."""
        from src.models.payment_method import PaymentMethod

        method = PaymentMethod(
            code="invoice",
            name="Invoice",
            description="Pay by invoice",
            is_active=True,
            position=0,
        )
        method.id = uuid4()

        data = method.to_dict()

        assert "id" in data
        assert data["code"] == "invoice"
        assert data["name"] == "Invoice"
        assert data["description"] == "Pay by invoice"
        assert data["is_active"] is True

    def test_payment_method_to_public_dict(self):
        """PaymentMethod.to_public_dict() should exclude sensitive fields."""
        from src.models.payment_method import PaymentMethod

        method = PaymentMethod(
            code="stripe",
            name="Credit Card",
            config={"api_key_ref": "STRIPE_SECRET_KEY"},  # Should NOT be exposed
            is_active=True,
        )
        method.id = uuid4()

        data = method.to_public_dict()

        assert "id" in data
        assert "code" in data
        assert "name" in data
        # Config should NOT be in public dict (contains sensitive references)
        assert "config" not in data

    def test_payment_method_fee_calculation_none(self):
        """PaymentMethod with fee_type='none' should return zero fee."""
        from src.models.payment_method import PaymentMethod

        method = PaymentMethod(code="test", name="Test", fee_type="none")

        fee = method.calculate_fee(Decimal("100.00"))

        assert fee == Decimal("0")

    def test_payment_method_fee_calculation_fixed(self):
        """PaymentMethod with fee_type='fixed' should return fixed amount."""
        from src.models.payment_method import PaymentMethod

        method = PaymentMethod(
            code="test",
            name="Test",
            fee_type="fixed",
            fee_amount=Decimal("1.50"),
        )

        fee = method.calculate_fee(Decimal("100.00"))

        assert fee == Decimal("1.50")

    def test_payment_method_fee_calculation_percentage(self):
        """PaymentMethod with fee_type='percentage' should return percentage."""
        from src.models.payment_method import PaymentMethod

        method = PaymentMethod(
            code="test",
            name="Test",
            fee_type="percentage",
            fee_amount=Decimal("2.5"),  # 2.5%
        )

        fee = method.calculate_fee(Decimal("100.00"))

        assert fee == Decimal("2.50")

    def test_payment_method_is_available_for_amount(self):
        """PaymentMethod.is_available_for_amount() should check min/max."""
        from src.models.payment_method import PaymentMethod

        method = PaymentMethod(
            code="test",
            name="Test",
            min_amount=Decimal("10.00"),
            max_amount=Decimal("1000.00"),
            is_active=True,
        )

        assert method.is_available_for_amount(Decimal("50.00")) is True
        assert method.is_available_for_amount(Decimal("5.00")) is False
        assert method.is_available_for_amount(Decimal("2000.00")) is False

    def test_payment_method_is_available_for_currency(self):
        """PaymentMethod.is_available_for_currency() should check currencies."""
        from src.models.payment_method import PaymentMethod

        method = PaymentMethod(
            code="test",
            name="Test",
            currencies=["EUR", "USD"],
            is_active=True,
        )

        assert method.is_available_for_currency("EUR") is True
        assert method.is_available_for_currency("USD") is True
        assert method.is_available_for_currency("GBP") is False

    def test_payment_method_empty_currencies_means_all(self):
        """Empty currencies list means available for all currencies."""
        from src.models.payment_method import PaymentMethod

        method = PaymentMethod(
            code="test",
            name="Test",
            currencies=[],
            is_active=True,
        )

        assert method.is_available_for_currency("EUR") is True
        assert method.is_available_for_currency("GBP") is True

    def test_payment_method_is_available_for_country(self):
        """PaymentMethod.is_available_for_country() should check countries."""
        from src.models.payment_method import PaymentMethod

        method = PaymentMethod(
            code="test",
            name="Test",
            countries=["DE", "AT"],
            is_active=True,
        )

        assert method.is_available_for_country("DE") is True
        assert method.is_available_for_country("AT") is True
        assert method.is_available_for_country("FR") is False

    def test_payment_method_empty_countries_means_all(self):
        """Empty countries list means available for all countries."""
        from src.models.payment_method import PaymentMethod

        method = PaymentMethod(
            code="test",
            name="Test",
            countries=[],
            is_active=True,
        )

        assert method.is_available_for_country("DE") is True
        assert method.is_available_for_country("US") is True


class TestPaymentMethodTranslation:
    """Test cases for PaymentMethodTranslation model."""

    def test_translation_has_required_fields(self):
        """PaymentMethodTranslation should have required fields."""
        from src.models.payment_method import PaymentMethodTranslation

        translation = PaymentMethodTranslation(
            payment_method_id=uuid4(),
            locale="de",
            name="Rechnung",
        )

        assert translation.locale == "de"
        assert translation.name == "Rechnung"

    def test_translation_has_optional_fields(self):
        """PaymentMethodTranslation should support optional fields."""
        from src.models.payment_method import PaymentMethodTranslation

        translation = PaymentMethodTranslation(
            payment_method_id=uuid4(),
            locale="de",
            name="Rechnung",
            description="Zahlung per Rechnung",
            short_description="Rechnung",
            instructions="Sie erhalten eine Rechnung per E-Mail.",
        )

        assert translation.description == "Zahlung per Rechnung"
        assert translation.short_description == "Rechnung"
        assert translation.instructions == "Sie erhalten eine Rechnung per E-Mail."
