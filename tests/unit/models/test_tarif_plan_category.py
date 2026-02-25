"""Tests for TarifPlanCategory model."""
from src.models.tarif_plan_category import TarifPlanCategory, tarif_plan_category_plans


class TestTarifPlanCategoryJunctionTable:
    """Test junction table definition."""

    def test_junction_table_exists(self):
        """Junction table tarif_plan_category_plans should be defined."""
        assert tarif_plan_category_plans is not None
        assert tarif_plan_category_plans.name == "tarif_plan_category_plans"

    def test_junction_table_has_columns(self):
        """Junction table should have category_id and tarif_plan_id columns."""
        col_names = [c.name for c in tarif_plan_category_plans.columns]
        assert "category_id" in col_names
        assert "tarif_plan_id" in col_names

    def test_junction_table_primary_key(self):
        """Junction table should have composite primary key."""
        pk_cols = [c.name for c in tarif_plan_category_plans.primary_key.columns]
        assert "category_id" in pk_cols
        assert "tarif_plan_id" in pk_cols


class TestTarifPlanCategoryModel:
    """Test TarifPlanCategory model definition."""

    def test_tablename(self):
        """Model should have correct table name."""
        assert TarifPlanCategory.__tablename__ == "tarif_plan_category"

    def test_has_tarif_plans_relationship(self):
        """Model should have tarif_plans relationship."""
        assert hasattr(TarifPlanCategory, "tarif_plans")

    def test_has_children_relationship(self):
        """Model should have children relationship."""
        assert hasattr(TarifPlanCategory, "children")

    def test_has_parent_relationship(self):
        """Model should have parent backref."""
        assert hasattr(TarifPlanCategory, "parent")


class TestTarifPlanCategoryDefaults:
    """Test column defaults."""

    def test_is_single_default(self):
        """is_single should default to True."""
        columns = {c.name: c for c in TarifPlanCategory.__table__.columns}
        assert columns["is_single"].default.arg is True

    def test_sort_order_default(self):
        """sort_order should default to 0."""
        columns = {c.name: c for c in TarifPlanCategory.__table__.columns}
        assert columns["sort_order"].default.arg == 0

    def test_parent_id_nullable(self):
        """parent_id should be nullable (root categories have no parent)."""
        columns = {c.name: c for c in TarifPlanCategory.__table__.columns}
        assert columns["parent_id"].nullable is True

    def test_description_nullable(self):
        """description should be nullable."""
        columns = {c.name: c for c in TarifPlanCategory.__table__.columns}
        assert columns["description"].nullable is True

    def test_slug_unique(self):
        """slug should be unique."""
        columns = {c.name: c for c in TarifPlanCategory.__table__.columns}
        assert columns["slug"].unique is True


class TestTarifPlanCategoryToDict:
    """Test to_dict() serialization."""

    def test_to_dict_returns_dict(self):
        """to_dict() should return a dictionary."""
        category = TarifPlanCategory(
            name="Test Category",
            slug="test-category",
            is_single=True,
        )
        category.tarif_plans = []
        category.children = []
        result = category.to_dict()
        assert isinstance(result, dict)

    def test_to_dict_has_required_fields(self):
        """to_dict() should include all expected fields."""
        category = TarifPlanCategory(
            name="Test",
            slug="test",
            description="A test category",
            is_single=False,
            sort_order=5,
        )
        category.tarif_plans = []
        category.children = []
        result = category.to_dict()

        assert result["name"] == "Test"
        assert result["slug"] == "test"
        assert result["description"] == "A test category"
        assert result["is_single"] is False
        assert result["sort_order"] == 5
        assert result["plan_count"] == 0
        assert result["children"] == []

    def test_to_dict_parent_id_none_when_no_parent(self):
        """to_dict() should have null parent_id for root categories."""
        category = TarifPlanCategory(
            name="Root",
            slug="root",
        )
        category.tarif_plans = []
        category.children = []
        result = category.to_dict()
        assert result["parent_id"] is None

    def test_repr(self):
        """__repr__ should include name, slug, and is_single."""
        category = TarifPlanCategory(
            name="Test",
            slug="test",
            is_single=True,
        )
        repr_str = repr(category)
        assert "Test" in repr_str
        assert "test" in repr_str
