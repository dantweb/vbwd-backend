"""Tests for TarifPlanCategoryService."""
import pytest
from unittest.mock import Mock
from uuid import uuid4

from src.services.tarif_plan_category_service import TarifPlanCategoryService
from src.models.tarif_plan_category import TarifPlanCategory
from src.models.tarif_plan import TarifPlan


class TestTarifPlanCategoryServiceCreate:
    """Test cases for creating categories."""

    @pytest.fixture
    def mock_category_repo(self):
        return Mock()

    @pytest.fixture
    def mock_plan_repo(self):
        return Mock()

    @pytest.fixture
    def service(self, mock_category_repo, mock_plan_repo):
        return TarifPlanCategoryService(
            category_repo=mock_category_repo,
            tarif_plan_repo=mock_plan_repo,
        )

    def test_create_category_success(self, service, mock_category_repo):
        """Create should save and return category."""
        mock_category_repo.find_by_slug.return_value = None
        mock_category_repo.save.side_effect = lambda c: c

        result = service.create(name="Test Category", slug="test-category")

        assert result.name == "Test Category"
        assert result.slug == "test-category"
        mock_category_repo.save.assert_called_once()

    def test_create_auto_generates_slug(self, service, mock_category_repo):
        """Create should auto-generate slug from name if not provided."""
        mock_category_repo.find_by_slug.return_value = None
        mock_category_repo.save.side_effect = lambda c: c

        result = service.create(name="Customer Tier")

        assert result.slug == "customer-tier"

    def test_create_fails_on_duplicate_slug(self, service, mock_category_repo):
        """Create should raise ValueError if slug already exists."""
        existing = TarifPlanCategory(name="Existing", slug="test")
        mock_category_repo.find_by_slug.return_value = existing

        with pytest.raises(ValueError, match="already exists"):
            service.create(name="Test", slug="test")

    def test_create_validates_parent_exists(self, service, mock_category_repo):
        """Create should raise ValueError if parent_id doesn't exist."""
        mock_category_repo.find_by_slug.return_value = None
        mock_category_repo.find_by_id.return_value = None

        parent_id = uuid4()
        with pytest.raises(ValueError, match="not found"):
            service.create(name="Child", parent_id=parent_id)

    def test_create_with_valid_parent(self, service, mock_category_repo):
        """Create with valid parent_id should succeed."""
        parent = TarifPlanCategory(name="Parent", slug="parent")
        parent.id = uuid4()

        mock_category_repo.find_by_slug.return_value = None
        mock_category_repo.find_by_id.return_value = parent
        mock_category_repo.save.side_effect = lambda c: c

        result = service.create(name="Child", parent_id=parent.id)

        assert result.parent_id == parent.id

    def test_create_with_is_single_false(self, service, mock_category_repo):
        """Create with is_single=False should allow multi subscriptions."""
        mock_category_repo.find_by_slug.return_value = None
        mock_category_repo.save.side_effect = lambda c: c

        result = service.create(name="Software", is_single=False)

        assert result.is_single is False


class TestTarifPlanCategoryServiceUpdate:
    """Test cases for updating categories."""

    @pytest.fixture
    def mock_category_repo(self):
        return Mock()

    @pytest.fixture
    def mock_plan_repo(self):
        return Mock()

    @pytest.fixture
    def service(self, mock_category_repo, mock_plan_repo):
        return TarifPlanCategoryService(
            category_repo=mock_category_repo,
            tarif_plan_repo=mock_plan_repo,
        )

    def test_update_not_found(self, service, mock_category_repo):
        """Update should raise ValueError if category not found."""
        mock_category_repo.find_by_id.return_value = None

        with pytest.raises(ValueError, match="not found"):
            service.update(uuid4(), name="New Name")

    def test_update_slug_conflict(self, service, mock_category_repo):
        """Update should raise ValueError on slug conflict."""
        category = TarifPlanCategory(name="Old", slug="old")
        category.id = uuid4()
        existing = TarifPlanCategory(name="Other", slug="new-slug")

        mock_category_repo.find_by_id.return_value = category
        mock_category_repo.find_by_slug.return_value = existing

        with pytest.raises(ValueError, match="already exists"):
            service.update(category.id, slug="new-slug")

    def test_update_cannot_be_own_parent(self, service, mock_category_repo):
        """Update should prevent category from being its own parent."""
        cat_id = uuid4()
        category = TarifPlanCategory(name="Test", slug="test")
        category.id = cat_id

        mock_category_repo.find_by_id.return_value = category

        with pytest.raises(ValueError, match="own parent"):
            service.update(cat_id, parent_id=cat_id)

    def test_update_success(self, service, mock_category_repo):
        """Update should save updated fields."""
        category = TarifPlanCategory(name="Old", slug="old")
        category.id = uuid4()

        mock_category_repo.find_by_id.return_value = category
        mock_category_repo.save.side_effect = lambda c: c

        result = service.update(category.id, name="New Name")

        assert result.name == "New Name"
        mock_category_repo.save.assert_called_once()


class TestTarifPlanCategoryServiceDelete:
    """Test cases for deleting categories."""

    @pytest.fixture
    def mock_category_repo(self):
        return Mock()

    @pytest.fixture
    def mock_plan_repo(self):
        return Mock()

    @pytest.fixture
    def service(self, mock_category_repo, mock_plan_repo):
        return TarifPlanCategoryService(
            category_repo=mock_category_repo,
            tarif_plan_repo=mock_plan_repo,
        )

    def test_delete_not_found(self, service, mock_category_repo):
        """Delete should raise ValueError if category not found."""
        mock_category_repo.find_by_id.return_value = None

        with pytest.raises(ValueError, match="not found"):
            service.delete(uuid4())

    def test_delete_root_forbidden(self, service, mock_category_repo):
        """Delete should prevent deleting root category."""
        root = TarifPlanCategory(name="Root", slug="root")
        root.id = uuid4()
        mock_category_repo.find_by_id.return_value = root

        with pytest.raises(ValueError, match="root"):
            service.delete(root.id)

    def test_delete_with_children_forbidden(self, service, mock_category_repo):
        """Delete should prevent deleting category with children."""
        category = TarifPlanCategory(name="Parent", slug="parent")
        category.id = uuid4()
        child = TarifPlanCategory(name="Child", slug="child")
        child.id = uuid4()

        mock_category_repo.find_by_id.return_value = category
        mock_category_repo.find_children.return_value = [child]

        with pytest.raises(ValueError, match="children"):
            service.delete(category.id)

    def test_delete_success(self, service, mock_category_repo):
        """Delete should succeed for leaf category."""
        category = TarifPlanCategory(name="Leaf", slug="leaf")
        category.id = uuid4()

        mock_category_repo.find_by_id.return_value = category
        mock_category_repo.find_children.return_value = []
        mock_category_repo.delete.return_value = True

        result = service.delete(category.id)

        assert result is True
        mock_category_repo.delete.assert_called_once_with(category.id)


class TestTarifPlanCategoryServiceAttachDetach:
    """Test cases for attaching/detaching plans."""

    @pytest.fixture
    def mock_category_repo(self):
        return Mock()

    @pytest.fixture
    def mock_plan_repo(self):
        return Mock()

    @pytest.fixture
    def service(self, mock_category_repo, mock_plan_repo):
        return TarifPlanCategoryService(
            category_repo=mock_category_repo,
            tarif_plan_repo=mock_plan_repo,
        )

    def test_attach_plans_category_not_found(self, service, mock_category_repo):
        """attach_plans should raise ValueError if category not found."""
        mock_category_repo.find_by_id.return_value = None

        with pytest.raises(ValueError, match="not found"):
            service.attach_plans(uuid4(), [uuid4()])

    def test_attach_plans_plan_not_found(
        self, service, mock_category_repo, mock_plan_repo
    ):
        """attach_plans should raise ValueError if plan not found."""
        category = TarifPlanCategory(name="Test", slug="test")
        category.id = uuid4()
        category.tarif_plans = []

        mock_category_repo.find_by_id.return_value = category
        mock_plan_repo.find_by_id.return_value = None

        with pytest.raises(ValueError, match="not found"):
            service.attach_plans(category.id, [uuid4()])

    def test_attach_plans_success(self, service, mock_category_repo, mock_plan_repo):
        """attach_plans should add plans to category."""
        category = TarifPlanCategory(name="Test", slug="test")
        category.id = uuid4()
        category.tarif_plans = []

        plan = TarifPlan()
        plan.id = uuid4()
        plan.name = "Pro"

        mock_category_repo.find_by_id.return_value = category
        mock_plan_repo.find_by_id.return_value = plan
        mock_category_repo.save.side_effect = lambda c: c

        result = service.attach_plans(category.id, [plan.id])

        assert len(result.tarif_plans) == 1
        mock_category_repo.save.assert_called_once()

    def test_attach_plans_skips_duplicates(
        self, service, mock_category_repo, mock_plan_repo
    ):
        """attach_plans should skip plans already attached."""
        plan = TarifPlan()
        plan.id = uuid4()
        plan.name = "Pro"

        category = TarifPlanCategory(name="Test", slug="test")
        category.id = uuid4()
        category.tarif_plans = [plan]

        mock_category_repo.find_by_id.return_value = category
        mock_category_repo.save.side_effect = lambda c: c

        result = service.attach_plans(category.id, [plan.id])

        # Should still have exactly 1 plan (no duplicate)
        assert len(result.tarif_plans) == 1

    def test_detach_plans_category_not_found(self, service, mock_category_repo):
        """detach_plans should raise ValueError if category not found."""
        mock_category_repo.find_by_id.return_value = None

        with pytest.raises(ValueError, match="not found"):
            service.detach_plans(uuid4(), [uuid4()])

    def test_detach_plans_success(self, service, mock_category_repo):
        """detach_plans should remove plans from category."""
        plan = TarifPlan()
        plan.id = uuid4()
        plan.name = "Pro"

        category = TarifPlanCategory(name="Test", slug="test")
        category.id = uuid4()
        category.tarif_plans = [plan]

        mock_category_repo.find_by_id.return_value = category
        mock_category_repo.save.side_effect = lambda c: c

        result = service.detach_plans(category.id, [plan.id])

        assert len(result.tarif_plans) == 0
        mock_category_repo.save.assert_called_once()
