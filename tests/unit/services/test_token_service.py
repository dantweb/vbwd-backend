"""Tests for TokenService."""
from unittest.mock import MagicMock
from uuid import uuid4

from src.models.enums import TokenTransactionType


class TestTokenServiceRefundTokens:
    """Tests for TokenService.refund_tokens()."""

    def test_refund_tokens_debits_balance(self):
        """refund_tokens debits the correct amount from balance."""
        from src.services.token_service import TokenService

        user_id = uuid4()
        balance_mock = MagicMock(balance=100)
        balance_repo = MagicMock()
        balance_repo.find_by_user_id.return_value = balance_mock
        transaction_repo = MagicMock()
        purchase_repo = MagicMock()

        service = TokenService(
            balance_repo=balance_repo,
            transaction_repo=transaction_repo,
            purchase_repo=purchase_repo,
        )

        actual = service.refund_tokens(
            user_id=user_id,
            amount=50,
            reference_id=uuid4(),
            description="Refund: 50 tokens",
        )

        assert actual == 50
        assert balance_mock.balance == 50
        balance_repo.save.assert_called_once_with(balance_mock)
        transaction_repo.create.assert_called_once()
        tx = transaction_repo.create.call_args[0][0]
        assert tx.amount == -50
        assert tx.transaction_type == TokenTransactionType.REFUND

    def test_refund_tokens_clamps_to_zero(self):
        """refund_tokens clamps debit to available balance when insufficient."""
        from src.services.token_service import TokenService

        user_id = uuid4()
        balance_mock = MagicMock(balance=30)
        balance_repo = MagicMock()
        balance_repo.find_by_user_id.return_value = balance_mock
        transaction_repo = MagicMock()
        purchase_repo = MagicMock()

        service = TokenService(
            balance_repo=balance_repo,
            transaction_repo=transaction_repo,
            purchase_repo=purchase_repo,
        )

        actual = service.refund_tokens(user_id=user_id, amount=100)

        assert actual == 30
        assert balance_mock.balance == 0
        balance_repo.save.assert_called_once()
        tx = transaction_repo.create.call_args[0][0]
        assert tx.amount == -30

    def test_refund_tokens_returns_zero_when_no_balance(self):
        """refund_tokens returns 0 when user has no balance record."""
        from src.services.token_service import TokenService

        balance_repo = MagicMock()
        balance_repo.find_by_user_id.return_value = None
        transaction_repo = MagicMock()
        purchase_repo = MagicMock()

        service = TokenService(
            balance_repo=balance_repo,
            transaction_repo=transaction_repo,
            purchase_repo=purchase_repo,
        )

        actual = service.refund_tokens(user_id=uuid4(), amount=50)

        assert actual == 0
        balance_repo.save.assert_not_called()
        transaction_repo.create.assert_not_called()


class TestTokenServiceCreditTokens:
    """Tests for TokenService.credit_tokens()."""

    def test_credit_tokens_increases_balance(self):
        """credit_tokens increases user balance."""
        from src.services.token_service import TokenService

        user_id = uuid4()
        balance_mock = MagicMock(balance=10)
        balance_repo = MagicMock()
        balance_repo.get_or_create.return_value = balance_mock
        transaction_repo = MagicMock()
        purchase_repo = MagicMock()

        service = TokenService(
            balance_repo=balance_repo,
            transaction_repo=transaction_repo,
            purchase_repo=purchase_repo,
        )

        service.credit_tokens(
            user_id=user_id,
            amount=50,
            transaction_type=TokenTransactionType.PURCHASE,
        )

        assert balance_mock.balance == 60
        balance_repo.save.assert_called_once()
        transaction_repo.create.assert_called_once()

    def test_credit_tokens_rejects_non_positive(self):
        """credit_tokens raises ValueError for non-positive amount."""
        from src.services.token_service import TokenService
        import pytest

        service = TokenService(
            balance_repo=MagicMock(),
            transaction_repo=MagicMock(),
            purchase_repo=MagicMock(),
        )

        with pytest.raises(ValueError, match="positive"):
            service.credit_tokens(
                user_id=uuid4(),
                amount=0,
                transaction_type=TokenTransactionType.PURCHASE,
            )


class TestTokenServiceDebitTokens:
    """Tests for TokenService.debit_tokens()."""

    def test_debit_tokens_raises_on_insufficient_balance(self):
        """debit_tokens raises ValueError when balance insufficient."""
        from src.services.token_service import TokenService
        import pytest

        balance_repo = MagicMock()
        balance_repo.find_by_user_id.return_value = MagicMock(balance=10)

        service = TokenService(
            balance_repo=balance_repo,
            transaction_repo=MagicMock(),
            purchase_repo=MagicMock(),
        )

        with pytest.raises(ValueError, match="Insufficient"):
            service.debit_tokens(
                user_id=uuid4(),
                amount=50,
                transaction_type=TokenTransactionType.USAGE,
            )
