"""Tests for shared payment route helpers."""
import pytest
from uuid import uuid4
from unittest.mock import MagicMock

from flask import Flask

from src.plugins.config_store import PluginConfigEntry
from src.plugins.payment_route_helpers import (
    check_plugin_enabled,
    validate_invoice_for_payment,
    emit_payment_captured,
)
from src.events.payment_events import PaymentCapturedEvent
from src.models.enums import InvoiceStatus


@pytest.fixture
def stripe_config():
    return {"secret_key": "sk_test", "webhook_secret": "whsec_test", "sandbox": True}


@pytest.fixture
def mock_config_store(mocker, stripe_config):
    store = mocker.MagicMock()
    store.get_by_name.return_value = PluginConfigEntry(
        plugin_name="stripe", status="enabled", config=stripe_config
    )
    store.get_config.return_value = stripe_config
    return store


@pytest.fixture
def mock_container(mocker):
    container = mocker.MagicMock()
    container.invoice_repository.return_value = mocker.MagicMock()
    container.event_dispatcher.return_value = mocker.MagicMock()
    return container


@pytest.fixture
def app(mock_config_store, mock_container):
    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True
    flask_app.config_store = mock_config_store
    flask_app.container = mock_container
    return flask_app


class TestCheckPluginEnabled:
    """Tests for check_plugin_enabled helper."""

    def test_check_enabled_returns_config(self, app, stripe_config):
        """Should return (config_dict, None) when plugin is enabled."""
        with app.app_context():
            config, err = check_plugin_enabled("stripe")
            assert config == stripe_config
            assert err is None

    def test_check_enabled_returns_404_disabled(self, app, mocker):
        """Should return (None, (response, 404)) when plugin status != 'enabled'."""
        app.config_store.get_by_name.return_value = PluginConfigEntry(
            plugin_name="stripe", status="disabled"
        )
        with app.app_context():
            config, err = check_plugin_enabled("stripe")
            assert config is None
            response, status_code = err
            assert status_code == 404

    def test_check_enabled_returns_503_no_store(self, app):
        """Should return (None, (response, 503)) when config_store is absent."""
        app.config_store = None
        delattr(app, "config_store")
        with app.app_context():
            config, err = check_plugin_enabled("stripe")
            assert config is None
            response, status_code = err
            assert status_code == 503


class TestValidateInvoiceForPayment:
    """Tests for validate_invoice_for_payment helper."""

    def test_validate_invoice_valid(self, app, mock_container):
        """Should return (invoice, None) for valid pending invoice owned by user."""
        user_id = uuid4()
        invoice = MagicMock()
        invoice.id = uuid4()
        invoice.status = InvoiceStatus.PENDING
        invoice.user_id = user_id
        mock_container.invoice_repository.return_value.find_by_id.return_value = invoice
        app.container = mock_container

        with app.app_context():
            result, err = validate_invoice_for_payment(str(invoice.id), user_id)
            assert result is invoice
            assert err is None

    def test_validate_invoice_bad_uuid(self, app):
        """Should return (None, (response, 400)) for invalid UUID string."""
        with app.app_context():
            result, err = validate_invoice_for_payment("not-a-uuid", uuid4())
            assert result is None
            response, status_code = err
            assert status_code == 400

    def test_validate_invoice_not_found(self, app, mock_container):
        """Should return (None, (response, 404)) when invoice not in DB."""
        mock_container.invoice_repository.return_value.find_by_id.return_value = None
        with app.app_context():
            result, err = validate_invoice_for_payment(str(uuid4()), uuid4())
            assert result is None
            response, status_code = err
            assert status_code == 404

    def test_validate_invoice_not_pending(self, app, mock_container):
        """Should return (None, (response, 400)) when invoice is not PENDING."""
        invoice = MagicMock()
        invoice.id = uuid4()
        invoice.status = InvoiceStatus.PAID
        invoice.user_id = uuid4()
        mock_container.invoice_repository.return_value.find_by_id.return_value = invoice

        with app.app_context():
            result, err = validate_invoice_for_payment(str(invoice.id), invoice.user_id)
            assert result is None
            response, status_code = err
            assert status_code == 400

    def test_validate_invoice_wrong_user(self, app, mock_container):
        """Should return (None, (response, 403)) when user_id doesn't match."""
        invoice = MagicMock()
        invoice.id = uuid4()
        invoice.status = InvoiceStatus.PENDING
        invoice.user_id = uuid4()
        mock_container.invoice_repository.return_value.find_by_id.return_value = invoice
        app.container = mock_container

        different_user = uuid4()
        with app.app_context():
            result, err = validate_invoice_for_payment(str(invoice.id), different_user)
            assert result is None
            response, status_code = err
            assert status_code == 403


class TestEmitPaymentCaptured:
    """Tests for emit_payment_captured helper."""

    def test_emit_payment_captured_calls_emit(self, app, mock_container):
        """Should call container.event_dispatcher().emit() once."""
        with app.app_context():
            emit_payment_captured(
                invoice_id=uuid4(),
                payment_reference="cs_test_abc",
                amount="29.99",
                currency="EUR",
                provider="stripe",
                transaction_id="pi_test_xyz",
            )
        dispatcher = mock_container.event_dispatcher.return_value
        dispatcher.emit.assert_called_once()

    def test_emit_payment_captured_event_fields(self, app, mock_container):
        """Emitted event should have correct field values."""
        inv_id = uuid4()
        with app.app_context():
            emit_payment_captured(
                invoice_id=inv_id,
                payment_reference="cs_ref",
                amount="49.99",
                currency="USD",
                provider="stripe",
                transaction_id="pi_abc",
            )
        event = mock_container.event_dispatcher.return_value.emit.call_args[0][0]
        assert isinstance(event, PaymentCapturedEvent)
        assert event.invoice_id == inv_id
        assert event.payment_reference == "cs_ref"
        assert event.amount == "49.99"
        assert event.currency == "USD"
        assert event.provider == "stripe"
        assert event.transaction_id == "pi_abc"
