"""Transaction management utilities for multi-step database operations."""
from functools import wraps
from typing import Callable, Any, Union


class TransactionContext:
    """
    Context manager for database transactions.

    Provides automatic commit on success and rollback on exception.
    Supports nested transactions using savepoints.

    Usage:
        with TransactionContext(session):
            user = user_repo.save(user)
            subscription = sub_repo.save(subscription)
            # Both commit together or rollback together

    For nested transactions:
        with TransactionContext(session):
            user = user_repo.save(user)
            try:
                with TransactionContext(session, nested=True):
                    # If this fails, only this part rolls back
                    risky_operation()
            except Exception:
                pass  # Handle inner error, outer continues
    """

    def __init__(self, session, nested: bool = False):
        """
        Initialize transaction context.

        Args:
            session: SQLAlchemy session
            nested: If True, use savepoint for nested transaction
        """
        self._session = session
        self._nested = nested
        self._savepoint = None

    def __enter__(self):
        """Enter transaction context."""
        if self._nested:
            self._savepoint = self._session.begin_nested()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit transaction context with commit or rollback."""
        if exc_type is not None:
            # Exception occurred - rollback
            if self._nested and self._savepoint:
                self._savepoint.rollback()
            else:
                self._session.rollback()
            # Re-raise the exception
            return False
        else:
            # Success - commit
            if not self._nested:
                self._session.commit()
        return False


class UnitOfWork:
    """
    Unit of Work pattern implementation.

    Tracks multiple operations and commits them as a unit.
    Provides explicit commit and rollback methods.

    Usage:
        with UnitOfWork(session) as uow:
            user = user_repo.save(user)
            subscription = sub_repo.save(subscription)
            # Commits automatically on exit

        # Or with explicit control:
        with UnitOfWork(session) as uow:
            user = user_repo.save(user)
            if some_condition:
                uow.rollback()
            else:
                uow.commit()
    """

    def __init__(self, session):
        """
        Initialize Unit of Work.

        Args:
            session: SQLAlchemy session
        """
        self._session = session
        self._committed = False
        self._rolled_back = False

    def __enter__(self):
        """Enter unit of work context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit unit of work with auto-commit or rollback."""
        if exc_type is not None:
            # Exception occurred - rollback if not already done
            if not self._rolled_back:
                self._session.rollback()
            return False
        else:
            # Success - commit if not already done
            if not self._committed and not self._rolled_back:
                self._session.commit()
        return False

    def commit(self):
        """Explicitly commit the unit of work."""
        self._session.commit()
        self._committed = True

    def rollback(self):
        """Explicitly rollback the unit of work."""
        self._session.rollback()
        self._rolled_back = True


def transactional(
    session_or_getter: Union[Any, Callable[[], Any]], is_getter: bool = False
):
    """
    Decorator to wrap a function in a transaction.

    The decorated function will automatically commit on success
    or rollback on exception.

    Args:
        session_or_getter: SQLAlchemy session or a callable that returns one
        is_getter: Set to True if session_or_getter is a callable that returns a session

    Usage:
        @transactional(db.session)
        def create_user_with_subscription(user_data, plan_id):
            user = user_repo.save(User(**user_data))
            subscription = sub_repo.save(Subscription(user_id=user.id, plan_id=plan_id))
            return user, subscription

        # Or with a session getter:
        @transactional(lambda: db.session, is_getter=True)
        def my_function():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get session (call getter if needed)
            if is_getter:
                session = session_or_getter()
            else:
                session = session_or_getter

            try:
                result = func(*args, **kwargs)
                session.commit()
                return result
            except Exception:
                session.rollback()
                raise

        return wrapper

    return decorator
