"""Tests for AddOn tarif_plans many-to-many relationship (Sprint 13)."""
from decimal import Decimal
from src.models.addon import AddOn, addon_tarif_plans


class TestAddOnTarifPlanRelationship:
    """Test AddOn model tarif_plans relationship definition."""

    def test_addon_tarif_plans_table_exists(self):
        """Junction table addon_tarif_plans should be defined."""
        assert addon_tarif_plans is not None
        assert addon_tarif_plans.name == "addon_tarif_plans"

    def test_addon_tarif_plans_table_has_columns(self):
        """Junction table should have addon_id and tarif_plan_id columns."""
        col_names = [c.name for c in addon_tarif_plans.columns]
        assert "addon_id" in col_names
        assert "tarif_plan_id" in col_names

    def test_addon_tarif_plans_table_primary_key(self):
        """Junction table should have composite primary key."""
        pk_cols = [c.name for c in addon_tarif_plans.primary_key.columns]
        assert "addon_id" in pk_cols
        assert "tarif_plan_id" in pk_cols

    def test_addon_has_tarif_plans_relationship(self):
        """AddOn model should have tarif_plans relationship attribute."""
        assert hasattr(AddOn, "tarif_plans")

    def test_addon_is_independent_property_exists(self):
        """AddOn model should have is_independent property."""
        assert hasattr(AddOn, "is_independent")
        assert isinstance(
            getattr(AddOn, "is_independent"), property
        ), "is_independent should be a property"

    def test_addon_is_recurring_property_exists(self):
        """AddOn model should still have is_recurring property (no regression)."""
        assert hasattr(AddOn, "is_recurring")
        assert isinstance(getattr(AddOn, "is_recurring"), property)


class TestAddOnToDict:
    """Test AddOn.to_dict() includes tarif_plan fields."""

    def test_to_dict_has_tarif_plan_ids_key(self):
        """to_dict() should include tarif_plan_ids field."""
        addon = AddOn(
            name="Test",
            slug="test",
            price=Decimal("5.00"),
        )
        # In non-DB context, tarif_plans may not be initialized.
        # We set it manually for the test.
        addon.tarif_plans = []
        result = addon.to_dict()
        assert "tarif_plan_ids" in result
        assert result["tarif_plan_ids"] == []

    def test_to_dict_has_tarif_plans_key(self):
        """to_dict() should include tarif_plans field with id and name."""
        addon = AddOn(
            name="Test",
            slug="test",
            price=Decimal("5.00"),
        )
        addon.tarif_plans = []
        result = addon.to_dict()
        assert "tarif_plans" in result
        assert result["tarif_plans"] == []


class TestAddOnColumnDefaults:
    """Test AddOn column defaults are still correct (no regression)."""

    def test_is_active_default(self):
        """is_active should default to True."""
        columns = {c.name: c for c in AddOn.__table__.columns}
        assert columns["is_active"].default.arg is True

    def test_sort_order_default(self):
        """sort_order should default to 0."""
        columns = {c.name: c for c in AddOn.__table__.columns}
        assert columns["sort_order"].default.arg == 0

    def test_currency_default(self):
        """currency should default to EUR."""
        columns = {c.name: c for c in AddOn.__table__.columns}
        assert columns["currency"].default.arg == "EUR"
