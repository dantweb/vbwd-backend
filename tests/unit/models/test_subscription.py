"""Tests for Subscription model trial methods."""
from datetime import datetime, timedelta
from unittest.mock import patch  # noqa: F401

from src.models.enums import SubscriptionStatus
from src.models.subscription import Subscription


class TestSubscriptionTrial:
    """Tests for trial-related model methods and properties."""

    def test_subscription_status_has_trialing(self):
        """TRIALING value exists in SubscriptionStatus enum."""
        assert SubscriptionStatus.TRIALING.value == "TRIALING"

    def test_start_trial_sets_trialing_status(self):
        """start_trial() sets status, started_at, trial_end_at, expires_at."""
        sub = Subscription()
        sub.start_trial(14)

        assert sub.status == SubscriptionStatus.TRIALING
        assert sub.started_at is not None
        assert sub.trial_end_at is not None
        assert sub.expires_at == sub.trial_end_at
        # trial_end_at should be ~14 days from now
        delta = sub.trial_end_at - sub.started_at
        assert delta.days == 14

    def test_is_trialing_true_for_trialing_status(self):
        """is_trialing returns True when status is TRIALING."""
        sub = Subscription()
        sub.status = SubscriptionStatus.TRIALING
        assert sub.is_trialing is True

    def test_is_trialing_false_for_active_status(self):
        """is_trialing returns False when status is ACTIVE."""
        sub = Subscription()
        sub.status = SubscriptionStatus.ACTIVE
        assert sub.is_trialing is False

    def test_is_valid_true_for_trialing_with_future_expiry(self):
        """is_valid returns True for TRIALING subscription with future expires_at."""
        sub = Subscription()
        sub.status = SubscriptionStatus.TRIALING
        sub.expires_at = datetime.utcnow() + timedelta(days=7)
        assert sub.is_valid is True

    def test_is_valid_false_for_expired_trial(self):
        """is_valid returns False for TRIALING subscription with past expires_at."""
        sub = Subscription()
        sub.status = SubscriptionStatus.TRIALING
        sub.expires_at = datetime.utcnow() - timedelta(days=1)
        assert sub.is_valid is False

    def test_is_valid_still_true_for_active(self):
        """is_valid still returns True for ACTIVE subscription."""
        sub = Subscription()
        sub.status = SubscriptionStatus.ACTIVE
        sub.expires_at = datetime.utcnow() + timedelta(days=30)
        assert sub.is_valid is True

    def test_to_dict_includes_trial_fields(self):
        """to_dict() includes is_trialing and trial_end_at."""
        sub = Subscription()
        sub.start_trial(7)
        d = sub.to_dict()
        assert "is_trialing" in d
        assert d["is_trialing"] is True
        assert "trial_end_at" in d
        assert d["trial_end_at"] is not None
