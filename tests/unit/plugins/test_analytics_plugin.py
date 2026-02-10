"""Tests for analytics plugin — delegates to plugin's own test suite.

The canonical tests live in plugins/analytics/tests/test_plugin.py.
This file imports them so they're discoverable by the main test runner.
"""
from plugins.analytics.tests.test_plugin import *  # noqa: F401,F403
