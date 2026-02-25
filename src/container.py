"""Dependency injection container."""
from dependency_injector import containers, providers

from src.repositories.user_repository import UserRepository
from src.repositories.user_details_repository import UserDetailsRepository
from src.repositories.subscription_repository import SubscriptionRepository
from src.repositories.tarif_plan_repository import TarifPlanRepository
from src.repositories.invoice_repository import InvoiceRepository
from src.repositories.invoice_line_item_repository import InvoiceLineItemRepository
from src.repositories.currency_repository import CurrencyRepository
from src.repositories.tax_repository import TaxRepository
from src.repositories.password_reset_repository import PasswordResetRepository
from src.repositories.token_bundle_repository import TokenBundleRepository
from src.repositories.token_bundle_purchase_repository import (
    TokenBundlePurchaseRepository,
)
from src.repositories.addon_repository import AddOnRepository
from src.repositories.tarif_plan_category_repository import TarifPlanCategoryRepository
from src.repositories.addon_subscription_repository import AddOnSubscriptionRepository
from src.repositories.token_repository import (
    TokenBalanceRepository,
    TokenTransactionRepository,
)

from src.services.auth_service import AuthService
from src.services.user_service import UserService
from src.services.subscription_service import SubscriptionService
from src.services.tarif_plan_service import TarifPlanService
from src.services.currency_service import CurrencyService
from src.services.tax_service import TaxService
from src.services.password_reset_service import PasswordResetService
from src.services.activity_logger import ActivityLogger
from src.services.token_service import TokenService
from src.services.invoice_service import InvoiceService
from src.services.refund_service import RefundService
from src.services.tarif_plan_category_service import TarifPlanCategoryService

from src.events.domain import DomainEventDispatcher


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
    db_session: providers.Dependency = providers.Dependency()

    # ==================
    # Repositories
    # ==================

    user_repository = providers.Factory(UserRepository, session=db_session)

    user_details_repository = providers.Factory(
        UserDetailsRepository, session=db_session
    )

    subscription_repository = providers.Factory(
        SubscriptionRepository, session=db_session
    )

    tarif_plan_repository = providers.Factory(TarifPlanRepository, session=db_session)

    invoice_repository = providers.Factory(InvoiceRepository, session=db_session)

    invoice_line_item_repository = providers.Factory(
        InvoiceLineItemRepository, session=db_session
    )

    token_bundle_repository = providers.Factory(
        TokenBundleRepository, session=db_session
    )

    token_bundle_purchase_repository = providers.Factory(
        TokenBundlePurchaseRepository, session=db_session
    )

    addon_repository = providers.Factory(AddOnRepository, session=db_session)

    tarif_plan_category_repository = providers.Factory(
        TarifPlanCategoryRepository, session=db_session
    )

    addon_subscription_repository = providers.Factory(
        AddOnSubscriptionRepository, session=db_session
    )

    token_balance_repository = providers.Factory(
        TokenBalanceRepository, session=db_session
    )

    token_transaction_repository = providers.Factory(
        TokenTransactionRepository, session=db_session
    )

    currency_repository = providers.Factory(CurrencyRepository, session=db_session)

    tax_repository = providers.Factory(TaxRepository, session=db_session)

    # ==================
    # Services
    # ==================

    auth_service = providers.Factory(AuthService, user_repository=user_repository)

    user_service = providers.Factory(
        UserService,
        user_repository=user_repository,
        user_details_repository=user_details_repository,
    )

    tarif_plan_service = providers.Factory(
        TarifPlanService, tarif_plan_repository=tarif_plan_repository
    )

    currency_service = providers.Factory(
        CurrencyService, currency_repository=currency_repository
    )

    tax_service = providers.Factory(TaxService, tax_repository=tax_repository)

    token_service = providers.Factory(
        TokenService,
        balance_repo=token_balance_repository,
        transaction_repo=token_transaction_repository,
        purchase_repo=token_bundle_purchase_repository,
    )

    subscription_service = providers.Factory(
        SubscriptionService,
        subscription_repo=subscription_repository,
        tarif_plan_repo=tarif_plan_repository,
        token_service=token_service,
    )

    tarif_plan_category_service = providers.Factory(
        TarifPlanCategoryService,
        category_repo=tarif_plan_category_repository,
        tarif_plan_repo=tarif_plan_repository,
    )

    invoice_service = providers.Factory(
        InvoiceService,
        invoice_repository=invoice_repository,
    )

    refund_service = providers.Factory(
        RefundService,
        invoice_repo=invoice_repository,
        subscription_repo=subscription_repository,
        token_service=token_service,
        purchase_repo=token_bundle_purchase_repository,
        addon_sub_repo=addon_subscription_repository,
    )

    # ==================
    # Password Reset
    # ==================

    password_reset_repository = providers.Factory(
        PasswordResetRepository, session=db_session
    )

    activity_logger = providers.Singleton(ActivityLogger)

    password_reset_service = providers.Factory(
        PasswordResetService,
        user_repository=user_repository,
        reset_repository=password_reset_repository,
    )

    # ==================
    # Event System
    # ==================

    event_dispatcher = providers.Singleton(DomainEventDispatcher)

    # Note: Handlers are registered in app.py after container is wired
