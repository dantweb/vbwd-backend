"""Admin routes package."""
from src.routes.admin.users import admin_users_bp
from src.routes.admin.subscriptions import admin_subs_bp
from src.routes.admin.invoices import admin_invoices_bp
from src.routes.admin.plans import admin_plans_bp
from src.routes.admin.analytics import admin_analytics_bp
from src.routes.admin.profile import admin_profile_bp
from src.routes.admin.token_bundles import admin_token_bundles_bp
from src.routes.admin.addons import admin_addons_bp
from src.routes.admin.settings import admin_settings_bp

__all__ = [
    "admin_users_bp",
    "admin_subs_bp",
    "admin_invoices_bp",
    "admin_plans_bp",
    "admin_analytics_bp",
    "admin_profile_bp",
    "admin_token_bundles_bp",
    "admin_addons_bp",
    "admin_settings_bp",
]
