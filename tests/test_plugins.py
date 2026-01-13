"""
Tests for plugin/hook system.
"""

import pytest

from testiq.plugins import (
    HookContext,
    HookType,
    PluginManager,
    clear_hooks,
    get_global_manager,
    register_hook,
    trigger_hook,
    unregister_hook,
)


@pytest.fixture(autouse=True)
def reset_global_manager():
    """Reset global plugin manager before each test."""
    manager = get_global_manager()
    manager.clear_hooks()
    yield
    manager.clear_hooks()


class TestHookType:
    """Tests for HookType enum."""

    def test_all_hook_types_exist(self):
        """Test that all expected hook types are defined."""
        expected_hooks = [
            "BEFORE_ANALYSIS",
            "AFTER_ANALYSIS",
            "ON_DUPLICATE_FOUND",
            "ON_SUBSET_FOUND",
            "ON_SIMILAR_FOUND",
            "ON_ERROR",
            "ON_QUALITY_GATE_FAIL",
        ]

        for hook in expected_hooks:
            assert hasattr(HookType, hook)

    def test_hook_type_values(self):
        """Test that hook types have string values."""
        assert isinstance(HookType.BEFORE_ANALYSIS.value, str)
        assert HookType.BEFORE_ANALYSIS.value == "before_analysis"


class TestPluginManager:
    """Tests for PluginManager."""

    def test_register_hook(self):
        """Test registering a hook."""
        manager = PluginManager()
        called = []

        def my_hook(ctx: HookContext):
            called.append(ctx.data)

        manager.register_hook(HookType.BEFORE_ANALYSIS, my_hook)

        # Verify hook is registered
        assert HookType.BEFORE_ANALYSIS in manager.hooks
        assert len(manager.hooks[HookType.BEFORE_ANALYSIS]) == 1

    def test_register_multiple_hooks(self):
        """Test registering multiple hooks for same event."""
        manager = PluginManager()

        def hook1(ctx: HookContext):
            pass

        def hook2(ctx: HookContext):
            pass

        manager.register_hook(HookType.BEFORE_ANALYSIS, hook1)
        manager.register_hook(HookType.BEFORE_ANALYSIS, hook2)

        assert len(manager.hooks[HookType.BEFORE_ANALYSIS]) == 2

    def test_trigger_hook(self):
        """Test triggering a hook."""
        manager = PluginManager()
        results = []

        def my_hook(ctx: HookContext):
            results.append(ctx.data)

        manager.register_hook(HookType.AFTER_ANALYSIS, my_hook)
        manager.trigger(HookType.AFTER_ANALYSIS, {"test": "data", "count": 42})

        assert len(results) == 1
        assert results[0]["test"] == "data"
        assert results[0]["count"] == 42

    def test_trigger_multiple_hooks(self):
        """Test triggering multiple hooks in order."""
        manager = PluginManager()
        results = []

        def hook1(ctx: HookContext):
            results.append("hook1")

        def hook2(ctx: HookContext):
            results.append("hook2")

        manager.register_hook(HookType.ON_ERROR, hook1)
        manager.register_hook(HookType.ON_ERROR, hook2)
        manager.trigger(HookType.ON_ERROR, {})

        assert results == ["hook1", "hook2"]

    def test_trigger_nonexistent_hook(self):
        """Test triggering a hook with no registered callbacks."""
        manager = PluginManager()

        # Should not raise an error
        manager.trigger(HookType.BEFORE_ANALYSIS, {})

    def test_unregister_hook(self):
        """Test unregistering a hook."""
        manager = PluginManager()

        def my_hook(ctx: HookContext):
            pass

        manager.register_hook(HookType.AFTER_ANALYSIS, my_hook)
        assert len(manager.hooks[HookType.AFTER_ANALYSIS]) == 1

        manager.unregister_hook(HookType.AFTER_ANALYSIS, my_hook)
        assert len(manager.hooks.get(HookType.AFTER_ANALYSIS, [])) == 0

    def test_unregister_nonexistent_hook(self):
        """Test unregistering a hook that wasn't registered."""
        manager = PluginManager()

        def my_hook(ctx: HookContext):
            pass

        # Should not raise an error
        manager.unregister_hook(HookType.BEFORE_ANALYSIS, my_hook)

    def test_clear_hooks(self):
        """Test clearing all hooks."""
        manager = PluginManager()

        def hook1(ctx: HookContext):
            pass

        def hook2(ctx: HookContext):
            pass

        manager.register_hook(HookType.BEFORE_ANALYSIS, hook1)
        manager.register_hook(HookType.AFTER_ANALYSIS, hook2)

        manager.clear_hooks()
        # All hooks should be empty lists
        for hooks_list in manager.hooks.values():
            assert len(hooks_list) == 0

    def test_hook_error_handling(self):
        """Test that hook errors don't break the system."""
        manager = PluginManager()
        results = []

        def failing_hook(ctx: HookContext):
            raise ValueError("Hook error!")

        def working_hook(ctx: HookContext):
            results.append("worked")

        manager.register_hook(HookType.ON_ERROR, failing_hook)
        manager.register_hook(HookType.ON_ERROR, working_hook)

        # Should not raise, and working_hook should still execute
        manager.trigger(HookType.ON_ERROR, {})

        # Working hook should have been called despite first hook failing
        assert "worked" in results


class TestGlobalFunctions:
    """Tests for global convenience functions."""

    def test_register_global_hook(self):
        """Test registering a hook globally."""
        called = []

        def my_hook(ctx: HookContext):
            called.append(True)

        register_hook(HookType.BEFORE_ANALYSIS, my_hook)
        trigger_hook(HookType.BEFORE_ANALYSIS)

        assert len(called) == 1

    def test_unregister_global_hook(self):
        """Test unregistering a global hook."""
        called = []

        def my_hook(ctx: HookContext):
            called.append(True)

        register_hook(HookType.AFTER_ANALYSIS, my_hook)
        unregister_hook(HookType.AFTER_ANALYSIS, my_hook)
        trigger_hook(HookType.AFTER_ANALYSIS)

        assert len(called) == 0

    def test_clear_global_hooks(self):
        """Test clearing all global hooks."""

        def hook1(ctx: HookContext):
            pass

        def hook2(ctx: HookContext):
            pass

        register_hook(HookType.BEFORE_ANALYSIS, hook1)
        register_hook(HookType.AFTER_ANALYSIS, hook2)

        clear_hooks()

        manager = get_global_manager()
        for hooks_list in manager.hooks.values():
            assert len(hooks_list) == 0

    def test_multiple_registrations_same_function(self):
        """Test registering the same function multiple times."""
        called = []

        def my_hook(ctx: HookContext):
            called.append(True)

        register_hook(HookType.ON_DUPLICATE_FOUND, my_hook)
        register_hook(HookType.ON_DUPLICATE_FOUND, my_hook)  # Register again

        trigger_hook(HookType.ON_DUPLICATE_FOUND)

        # Function should be called twice
        assert len(called) == 2

    def test_hook_with_data(self):
        """Test hooks receive correct data."""
        received_data = []

        def my_hook(ctx: HookContext):
            received_data.append(ctx.data)

        register_hook(HookType.ON_DUPLICATE_FOUND, my_hook)
        trigger_hook(
            HookType.ON_DUPLICATE_FOUND,
            test1="test_login_1",
            test2="test_login_2",
            similarity=1.0,
        )

        assert len(received_data) == 1
        assert received_data[0]["test1"] == "test_login_1"
        assert received_data[0]["test2"] == "test_login_2"
        assert received_data[0]["similarity"] == 1.0


class TestPluginIntegration:
    """Integration tests for plugin system."""

    def test_complete_workflow(self):
        """Test a complete workflow with multiple hooks."""
        events = []

        def before_hook(ctx: HookContext):
            events.append("before")

        def after_hook(ctx: HookContext):
            events.append("after")

        def duplicate_hook(ctx: HookContext):
            events.append(f"duplicate: {ctx.data.get('count', 0)}")

        # Register hooks
        register_hook(HookType.BEFORE_ANALYSIS, before_hook)
        register_hook(HookType.AFTER_ANALYSIS, after_hook)
        register_hook(HookType.ON_DUPLICATE_FOUND, duplicate_hook)

        # Simulate analysis workflow
        trigger_hook(HookType.BEFORE_ANALYSIS)
        trigger_hook(HookType.ON_DUPLICATE_FOUND, count=5)
        trigger_hook(HookType.ON_DUPLICATE_FOUND, count=3)
        trigger_hook(HookType.AFTER_ANALYSIS)

        assert events == [
            "before",
            "duplicate: 5",
            "duplicate: 3",
            "after",
        ]

    def test_conditional_hook_execution(self):
        """Test that hooks can conditionally execute logic."""
        high_priority_alerts = []

        def alert_hook(ctx: HookContext):
            count = ctx.data.get("count", 0)
            if count > 10:
                high_priority_alerts.append(count)

        register_hook(HookType.ON_DUPLICATE_FOUND, alert_hook)

        # Low count - should not alert
        trigger_hook(HookType.ON_DUPLICATE_FOUND, count=5)
        assert len(high_priority_alerts) == 0

        # High count - should alert
        trigger_hook(HookType.ON_DUPLICATE_FOUND, count=15)
        assert len(high_priority_alerts) == 1
        assert high_priority_alerts[0] == 15
