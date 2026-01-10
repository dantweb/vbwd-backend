"""Tests for user schemas."""
import pytest
from uuid import uuid4
from types import SimpleNamespace
from src.schemas.user_schemas import (
    UserDetailsSchema,
    UserDetailsUpdateSchema,
    UserProfileSchema,
)


class TestUserDetailsSchema:
    """Tests for UserDetailsSchema."""

    def test_serializes_model_fields(self):
        """UserDetailsSchema should serialize UserDetails model without error."""
        details = SimpleNamespace(
            id=uuid4(),
            user_id=uuid4(),
            first_name="John",
            last_name="Doe",
            phone="+1234567890",
            address_line_1="123 Main St",
            address_line_2="Apt 4B",
            city="New York",
            postal_code="10001",
            country="US",
            created_at=None,
            updated_at=None,
        )

        schema = UserDetailsSchema()
        result = schema.dump(details)

        assert result["first_name"] == "John"
        assert result["last_name"] == "Doe"
        assert result["address_line_1"] == "123 Main St"
        assert result["address_line_2"] == "Apt 4B"
        assert result["city"] == "New York"
        assert result["postal_code"] == "10001"
        assert result["country"] == "US"

    def test_serializes_none_values(self):
        """UserDetailsSchema should handle None values."""
        details = SimpleNamespace(
            id=uuid4(),
            user_id=uuid4(),
            first_name=None,
            last_name=None,
            phone=None,
            address_line_1=None,
            address_line_2=None,
            city=None,
            postal_code=None,
            country=None,
            created_at=None,
            updated_at=None,
        )

        schema = UserDetailsSchema()
        result = schema.dump(details)

        assert result["first_name"] is None
        assert result["address_line_1"] is None
        assert result["address_line_2"] is None

    def test_does_not_have_removed_fields(self):
        """UserDetailsSchema should not have address, company, vat_number fields."""
        schema = UserDetailsSchema()
        field_names = set(schema.fields.keys())

        assert "address" not in field_names
        assert "company" not in field_names
        assert "vat_number" not in field_names


class TestUserDetailsUpdateSchema:
    """Tests for UserDetailsUpdateSchema."""

    def test_loads_valid_data(self):
        """UserDetailsUpdateSchema should load valid update data."""
        schema = UserDetailsUpdateSchema()
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "address_line_1": "123 Main St",
            "address_line_2": "Apt 4B",
            "city": "New York",
            "postal_code": "10001",
            "country": "US",
        }

        result = schema.load(data)

        assert result["first_name"] == "John"
        assert result["address_line_1"] == "123 Main St"
        assert result["country"] == "US"

    def test_validates_country_length(self):
        """UserDetailsUpdateSchema should reject country > 2 chars."""
        from marshmallow import ValidationError

        schema = UserDetailsUpdateSchema()
        data = {"country": "USA"}  # 3 chars, should fail

        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)

        assert "country" in exc_info.value.messages

    def test_does_not_have_removed_fields(self):
        """UserDetailsUpdateSchema should not have address, company, vat_number fields."""
        schema = UserDetailsUpdateSchema()
        field_names = set(schema.fields.keys())

        assert "address" not in field_names
        assert "company" not in field_names
        assert "vat_number" not in field_names


class TestUserProfileSchema:
    """Tests for UserProfileSchema."""

    def test_serializes_user_and_details(self):
        """UserProfileSchema should serialize nested user and details."""
        user = SimpleNamespace(
            id=uuid4(),
            email="test@example.com",
            status="active",
            role="user",
            created_at=None,
            updated_at=None,
        )

        details = SimpleNamespace(
            id=uuid4(),
            user_id=user.id,
            first_name="Test",
            last_name="User",
            phone=None,
            address_line_1="123 Main St",
            address_line_2=None,
            city="New York",
            postal_code="10001",
            country="US",
            created_at=None,
            updated_at=None,
        )

        schema = UserProfileSchema()
        result = schema.dump({"user": user, "details": details})

        assert result["user"]["email"] == "test@example.com"
        assert result["details"]["first_name"] == "Test"
        assert result["details"]["address_line_1"] == "123 Main St"

    def test_handles_null_details(self):
        """UserProfileSchema should handle null details."""
        user = SimpleNamespace(
            id=uuid4(),
            email="test@example.com",
            status="active",
            role="user",
            created_at=None,
            updated_at=None,
        )

        schema = UserProfileSchema()
        result = schema.dump({"user": user, "details": None})

        assert result["user"]["email"] == "test@example.com"
        assert result["details"] is None
