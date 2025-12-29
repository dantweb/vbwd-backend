"""Dependency injection container."""
from dependency_injector import containers, providers

from src.repositories.user_repository import UserRepository
from src.repositories.user_details_repository import UserDetailsRepository
from src.repositories.subscription_repository import SubscriptionRepository
from src.repositories.tarif_plan_repository import TarifPlanRepository
from src.repositories.invoice_repository import InvoiceRepository
from src.repositories.currency_repository import CurrencyRepository
from src.repositories.tax_repository import TaxRepository
from src.repositories.password_reset_repository import PasswordResetRepository

from src.services.auth_service import AuthService
from src.services.user_service import UserService
from src.services.subscription_service import SubscriptionService
from src.services.tarif_plan_service import TarifPlanService
from src.services.currency_service import CurrencyService
from src.services.tax_service import TaxService
from src.services.password_reset_service import PasswordResetService
from src.services.activity_logger import ActivityLogger

from src.events.domain import DomainEventDispatcher
from src.handlers.password_reset_handler import PasswordResetHandler


class Container(containers.DeclarativeContainer):
    """
    Application dependency injection container.

    Uses dependency-injector for managing service dependencies
    and lifecycle.

    Usage:
        container = Container()
        container.db_session.override(db.session)

        auth_service = container.auth_service()
    """

    # Configuration
    config = providers.Configuration()

    # Database session - must be overridden with actual db.session
    db_session = providers.Dependency()

    # ==================
    # Repositories
    # ==================

    user_repository = providers.Factory(
        UserRepository,
        session=db_session
    )

    user_details_repository = providers.Factory(
        UserDetailsRepository,
        session=db_session
    )

    subscription_repository = providers.Factory(
        SubscriptionRepository,
        session=db_session
    )

    tarif_plan_repository = providers.Factory(
        TarifPlanRepository,
        session=db_session
    )

    invoice_repository = providers.Factory(
        InvoiceRepository,
        session=db_session
    )

    currency_repository = providers.Factory(
        CurrencyRepository,
        session=db_session
    )

    tax_repository = providers.Factory(
        TaxRepository,
        session=db_session
    )

    # ==================
    # Services
    # ==================

    auth_service = providers.Factory(
        AuthService,
        user_repository=user_repository
    )

    user_service = providers.Factory(
        UserService,
        user_repository=user_repository,
        user_details_repository=user_details_repository
    )

    subscription_service = providers.Factory(
        SubscriptionService,
        subscription_repo=subscription_repository,
        tarif_plan_repo=tarif_plan_repository
    )

    tarif_plan_service = providers.Factory(
        TarifPlanService,
        tarif_plan_repository=tarif_plan_repository
    )

    currency_service = providers.Factory(
        CurrencyService,
        currency_repository=currency_repository
    )

    tax_service = providers.Factory(
        TaxService,
        tax_repository=tax_repository
    )

    # ==================
    # Password Reset
    # ==================

    password_reset_repository = providers.Factory(
        PasswordResetRepository,
        session=db_session
    )

    activity_logger = providers.Singleton(
        ActivityLogger
    )

    password_reset_service = providers.Factory(
        PasswordResetService,
        user_repository=user_repository,
        reset_repository=password_reset_repository
    )

    # ==================
    # Event System
    # ==================

    event_dispatcher = providers.Singleton(
        DomainEventDispatcher
    )

    # Note: Handlers are registered in app.py after container is wired
