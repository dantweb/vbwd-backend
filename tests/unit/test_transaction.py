"""Tests for transaction management utilities."""
import pytest
from unittest.mock import MagicMock


class TestTransactionContext:
    """Tests for TransactionContext context manager."""

    def test_transaction_commits_on_success(self):
        """Transaction commits when block completes successfully."""
        from src.utils.transaction import TransactionContext

        mock_session = MagicMock()
        with TransactionContext(mock_session):
            # Do some work
            pass

        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()

    def test_transaction_rolls_back_on_exception(self):
        """Transaction rolls back when exception occurs."""
        from src.utils.transaction import TransactionContext

        mock_session = MagicMock()
        with pytest.raises(ValueError):
            with TransactionContext(mock_session):
                raise ValueError("Test error")

        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()

    def test_transaction_re_raises_exception(self):
        """Transaction context re-raises the original exception."""
        from src.utils.transaction import TransactionContext

        mock_session = MagicMock()
        with pytest.raises(ValueError) as exc_info:
            with TransactionContext(mock_session):
                raise ValueError("Original error")

        assert str(exc_info.value) == "Original error"

    def test_nested_transaction_uses_savepoint(self):
        """Nested transaction uses savepoint for inner transaction."""
        from src.utils.transaction import TransactionContext

        mock_session = MagicMock()
        mock_session.begin_nested.return_value = MagicMock()

        with TransactionContext(mock_session):
            with TransactionContext(mock_session, nested=True):
                pass

        mock_session.begin_nested.assert_called_once()

    def test_nested_transaction_rollback_does_not_affect_outer(self):
        """Nested transaction rollback doesn't affect outer transaction."""
        from src.utils.transaction import TransactionContext

        mock_session = MagicMock()
        mock_savepoint = MagicMock()
        mock_session.begin_nested.return_value = mock_savepoint

        with TransactionContext(mock_session):
            try:
                with TransactionContext(mock_session, nested=True):
                    raise ValueError("Inner error")
            except ValueError:
                pass  # Handle inner error

        # Outer should still commit
        mock_session.commit.assert_called_once()
        # Savepoint should be rolled back
        mock_savepoint.rollback.assert_called_once()


class TestTransactional:
    """Tests for @transactional decorator."""

    def test_transactional_decorator_commits_on_success(self):
        """@transactional decorator commits when function succeeds."""
        from src.utils.transaction import transactional

        mock_session = MagicMock()

        @transactional(mock_session)
        def my_function():
            return "success"

        result = my_function()

        assert result == "success"
        mock_session.commit.assert_called_once()

    def test_transactional_decorator_rolls_back_on_exception(self):
        """@transactional decorator rolls back when function raises."""
        from src.utils.transaction import transactional

        mock_session = MagicMock()

        @transactional(mock_session)
        def my_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            my_function()

        mock_session.rollback.assert_called_once()

    def test_transactional_decorator_preserves_function_args(self):
        """@transactional decorator passes arguments correctly."""
        from src.utils.transaction import transactional

        mock_session = MagicMock()
        received_args = []

        @transactional(mock_session)
        def my_function(a, b, c=None):
            received_args.extend([a, b, c])
            return a + b

        result = my_function(1, 2, c=3)

        assert result == 3
        assert received_args == [1, 2, 3]

    def test_transactional_with_session_getter(self):
        """@transactional decorator works with session getter function."""
        from src.utils.transaction import transactional

        mock_session = MagicMock()
        session_getter = MagicMock(return_value=mock_session)

        @transactional(session_getter, is_getter=True)
        def my_function():
            return "success"

        result = my_function()

        assert result == "success"
        session_getter.assert_called_once()
        mock_session.commit.assert_called_once()


class TestUnitOfWork:
    """Tests for UnitOfWork pattern implementation."""

    def test_unit_of_work_context_commits_on_exit(self):
        """UnitOfWork commits when exiting context successfully."""
        from src.utils.transaction import UnitOfWork

        mock_session = MagicMock()
        uow = UnitOfWork(mock_session)

        with uow:
            pass

        mock_session.commit.assert_called_once()

    def test_unit_of_work_rolls_back_on_exception(self):
        """UnitOfWork rolls back when exception occurs."""
        from src.utils.transaction import UnitOfWork

        mock_session = MagicMock()
        uow = UnitOfWork(mock_session)

        with pytest.raises(ValueError):
            with uow:
                raise ValueError("Test error")

        mock_session.rollback.assert_called_once()

    def test_unit_of_work_rollback_method(self):
        """UnitOfWork provides explicit rollback method."""
        from src.utils.transaction import UnitOfWork

        mock_session = MagicMock()
        uow = UnitOfWork(mock_session)

        with uow:
            uow.rollback()

        mock_session.rollback.assert_called()

    def test_unit_of_work_commit_method(self):
        """UnitOfWork provides explicit commit method."""
        from src.utils.transaction import UnitOfWork

        mock_session = MagicMock()
        uow = UnitOfWork(mock_session)

        with uow:
            uow.commit()

        # Should be called at least once (explicit + auto on exit)
        assert mock_session.commit.call_count >= 1
