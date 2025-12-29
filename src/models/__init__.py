"""Domain models package."""
from src.models.user import User
from src.models.user_details import UserDetails
from src.models.user_case import UserCase
from src.models.currency import Currency
from src.models.tax import Tax, TaxRate
from src.models.price import Price
from src.models.tarif_plan import TarifPlan
from src.models.subscription import Subscription
from src.models.invoice import UserInvoice
from src.models.password_reset_token import PasswordResetToken
from src.models.role import Role, Permission, role_permissions, user_roles
from src.models.feature_usage import FeatureUsage
from src.models.enums import (
    UserStatus,
    UserRole,
    SubscriptionStatus,
    InvoiceStatus,
    BillingPeriod,
    UserCaseStatus,
)

__all__ = [
    # Models
    "User",
    "UserDetails",
    "UserCase",
    "Currency",
    "Tax",
    "TaxRate",
    "Price",
    "TarifPlan",
    "Subscription",
    "UserInvoice",
    "PasswordResetToken",
    "Role",
    "Permission",
    "FeatureUsage",
    # Association tables
    "role_permissions",
    "user_roles",
    # Enums
    "UserStatus",
    "UserRole",
    "SubscriptionStatus",
    "InvoiceStatus",
    "BillingPeriod",
    "UserCaseStatus",
]
