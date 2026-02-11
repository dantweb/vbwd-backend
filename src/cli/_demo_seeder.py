"""Demo data seeder — resets transactional data and seeds clean catalog."""
from sqlalchemy.orm import Session
from sqlalchemy import text


# Demo catalog definition
DEMO_PLANS = [
    {
        "name": "Basic",
        "slug": "basic",
        "description": "Essential features for individuals and small teams.",
        "price_float": 9.99,
        "price": 9.99,
        "currency": "EUR",
        "billing_period": "monthly",
        "is_active": True,
        "sort_order": 1,
        "features": {"api_calls": 1000, "storage_gb": 5, "users": 1},
    },
    {
        "name": "Pro",
        "slug": "pro",
        "description": "Advanced features for growing businesses.",
        "price_float": 29.99,
        "price": 29.99,
        "currency": "EUR",
        "billing_period": "monthly",
        "is_active": True,
        "sort_order": 2,
        "features": {"api_calls": 10000, "storage_gb": 50, "users": 10},
    },
    {
        "name": "Enterprise",
        "slug": "enterprise",
        "description": "Full platform access with premium support.",
        "price_float": 99.99,
        "price": 99.99,
        "currency": "EUR",
        "billing_period": "monthly",
        "is_active": True,
        "sort_order": 3,
        "features": {"api_calls": -1, "storage_gb": 500, "users": -1},
    },
]

DEMO_ADDONS = [
    {
        "name": "Priority Support",
        "slug": "priority-support",
        "description": "24/7 priority email and chat support with 1-hour response time.",
        "price": 15.00,
        "currency": "EUR",
        "billing_period": "monthly",
        "is_active": True,
        "sort_order": 1,
        "config": {"response_time_hours": 1, "channels": ["email", "chat"]},
    },
    {
        "name": "Premium Analytics",
        "slug": "premium-analytics",
        "description": "Advanced analytics dashboard with custom reports and data export.",
        "price": 25.00,
        "currency": "EUR",
        "billing_period": "monthly",
        "is_active": True,
        "sort_order": 2,
        "config": {"custom_reports": True, "data_export": True, "retention_days": 365},
    },
]

DEMO_TOKEN_BUNDLES = [
    {
        "name": "Starter Pack (500)",
        "description": "500 tokens for light usage.",
        "token_amount": 500,
        "price": 5.00,
        "is_active": True,
        "sort_order": 1,
    },
    {
        "name": "Standard Pack (1000)",
        "description": "1,000 tokens — best for regular use.",
        "token_amount": 1000,
        "price": 10.00,
        "is_active": True,
        "sort_order": 2,
    },
    {
        "name": "Pro Pack (5000)",
        "description": "5,000 tokens at a 10% discount.",
        "token_amount": 5000,
        "price": 45.00,
        "is_active": True,
        "sort_order": 3,
    },
]


class DemoSeeder:
    """Reset transactional data and seed clean demo catalog."""

    def __init__(self, db_session: Session):
        self.session = db_session

    def run(self) -> dict:
        """Execute full reset and return stats."""
        stats = {}
        stats.update(self._clear_transactional_data())
        stats.update(self._clear_catalog())
        stats.update(self._seed_catalog())
        self.session.commit()
        return stats

    def _clear_transactional_data(self) -> dict:
        """Delete all invoices, subscriptions, purchases, balances."""
        counts = {}
        # Order matters: children before parents (FK constraints)
        tables = [
            "token_transaction",
            "token_bundle_purchase",
            "addon_subscription",
            "invoice_line_item",
            "user_invoice",
            "subscription",
            "user_token_balance",
            "feature_usage",
            "password_reset_token",
        ]
        for table in tables:
            result = self.session.execute(text(f"DELETE FROM {table}"))
            counts[f"deleted_{table}"] = result.rowcount  # type: ignore[attr-defined]
        return counts

    def _clear_catalog(self) -> dict:
        """Delete all plans, addons, token bundles, and orphan prices."""
        counts = {}

        # Null out price_id FK on tarif_plan before deleting prices
        self.session.execute(text("UPDATE tarif_plan SET price_id = NULL"))

        for table in ["tarif_plan", "addon", "token_bundle", "price"]:
            result = self.session.execute(text(f"DELETE FROM {table}"))
            counts[f"deleted_{table}"] = result.rowcount  # type: ignore[attr-defined]

        return counts

    def _seed_catalog(self) -> dict:
        """Insert demo plans, addons, and token bundles."""
        from src.models.tarif_plan import TarifPlan
        from src.models.addon import AddOn
        from src.models.token_bundle import TokenBundle
        from src.models.enums import BillingPeriod

        for p in DEMO_PLANS:
            plan = TarifPlan(
                name=p["name"],
                slug=p["slug"],
                description=p["description"],
                price_float=p["price_float"],
                price=p["price"],
                currency=p["currency"],
                billing_period=BillingPeriod(p["billing_period"]),
                is_active=p["is_active"],
                sort_order=p["sort_order"],
                features=p["features"],
            )
            self.session.add(plan)

        for a in DEMO_ADDONS:
            addon = AddOn(
                name=a["name"],
                slug=a["slug"],
                description=a["description"],
                price=a["price"],
                currency=a["currency"],
                billing_period=a["billing_period"],
                is_active=a["is_active"],
                sort_order=a["sort_order"],
                config=a["config"],
            )
            self.session.add(addon)

        for b in DEMO_TOKEN_BUNDLES:
            bundle = TokenBundle(
                name=b["name"],
                description=b["description"],
                token_amount=b["token_amount"],
                price=b["price"],
                is_active=b["is_active"],
                sort_order=b["sort_order"],
            )
            self.session.add(bundle)

        self.session.flush()

        return {
            "seeded_plans": len(DEMO_PLANS),
            "seeded_addons": len(DEMO_ADDONS),
            "seeded_token_bundles": len(DEMO_TOKEN_BUNDLES),
        }
