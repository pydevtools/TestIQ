"""
Plugin and hook system for TestIQ.
Allows users to extend functionality with custom callbacks.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

from testiq.logging_config import get_logger

logger = get_logger(__name__)


class HookType(Enum):
    """Types of hooks available in TestIQ."""

    BEFORE_ANALYSIS = "before_analysis"
    AFTER_ANALYSIS = "after_analysis"
    ON_DUPLICATE_FOUND = "on_duplicate_found"
    ON_SUBSET_FOUND = "on_subset_found"
    ON_SIMILAR_FOUND = "on_similar_found"
    ON_ERROR = "on_error"
    ON_QUALITY_GATE_FAIL = "on_quality_gate_fail"


@dataclass
class HookContext:
    """Context passed to hook callbacks."""

    hook_type: HookType
    data: dict[str, Any]
    metadata: dict[str, Any]


class PluginManager:
    """Manage plugins and hooks for TestIQ."""

    def __init__(self) -> None:
        """Initialize plugin manager."""
        self._hooks: dict[HookType, list[Callable]] = {hook: [] for hook in HookType}
        logger.debug("Plugin manager initialized")

    def register_hook(
        self, hook_type: HookType, callback: Callable[[HookContext], None]
    ) -> None:
        """
        Register a hook callback.

        Args:
            hook_type: Type of hook to register
            callback: Callback function that receives HookContext

        Example:
            >>> def on_duplicate(ctx: HookContext):
            ...     print(f"Found duplicates: {ctx.data['group']}")
            >>> plugin_manager.register_hook(HookType.ON_DUPLICATE_FOUND, on_duplicate)
        """
        self._hooks[hook_type].append(callback)
        logger.info(f"Registered hook: {hook_type.value} -> {callback.__name__}")

    def unregister_hook(
        self, hook_type: HookType, callback: Callable[[HookContext], None]
    ) -> bool:
        """
        Unregister a hook callback.

        Args:
            hook_type: Type of hook
            callback: Callback to remove

        Returns:
            True if callback was found and removed
        """
        if callback in self._hooks[hook_type]:
            self._hooks[hook_type].remove(callback)
            logger.info(f"Unregistered hook: {hook_type.value} -> {callback.__name__}")
            return True
        return False

    def trigger(
        self, hook_type: HookType, data: dict[str, Any], metadata: Optional[dict[str, Any]] = None
    ) -> None:
        """
        Trigger all callbacks for a hook type.

        Args:
            hook_type: Type of hook to trigger
            data: Data to pass to callbacks
            metadata: Optional metadata
        """
        if not self._hooks[hook_type]:
            return

        context = HookContext(
            hook_type=hook_type, data=data, metadata=metadata or {}
        )

        logger.debug(f"Triggering hook: {hook_type.value} ({len(self._hooks[hook_type])} callbacks)")

        for callback in self._hooks[hook_type]:
            try:
                callback(context)
            except Exception as e:
                logger.error(
                    f"Error in hook callback {callback.__name__}: {e}",
                    exc_info=True,
                )

    def get_hooks(self, hook_type: HookType) -> list[Callable]:
        """Get all registered hooks for a type."""
        return self._hooks[hook_type].copy()

    def clear_hooks(self, hook_type: Optional[HookType] = None) -> None:
        """
        Clear hooks.

        Args:
            hook_type: Specific hook type to clear, or None to clear all
        """
        if hook_type:
            self._hooks[hook_type].clear()
            logger.info(f"Cleared hooks: {hook_type.value}")
        else:
            for hook in HookType:
                self._hooks[hook].clear()
            logger.info("Cleared all hooks")

    @property
    def hooks(self) -> dict[HookType, list[Callable]]:
        """Get all hooks."""
        return self._hooks


# Global plugin manager instance (singleton pattern with lazy initialization)
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager instance."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


# Convenience functions
def register_hook(hook_type: HookType, callback: Callable[[HookContext], None]) -> None:
    """Register a hook callback (convenience function)."""
    get_plugin_manager().register_hook(hook_type, callback)


def unregister_hook(hook_type: HookType, callback: Callable[[HookContext], None]) -> bool:
    """Unregister a hook callback (convenience function)."""
    return get_plugin_manager().unregister_hook(hook_type, callback)


def trigger_hook(
    hook_type: HookType, data: Optional[dict[str, Any]] = None, metadata: Optional[dict[str, Any]] = None, **kwargs
) -> None:
    """Trigger hook callbacks (convenience function)."""
    # If kwargs provided, use them as data
    if kwargs and data is None:
        data = kwargs
    elif data is None:
        data = {}
    get_plugin_manager().trigger(hook_type, data, metadata)


def clear_hooks(hook_type: Optional[HookType] = None) -> None:
    """Clear hooks (convenience function)."""
    get_plugin_manager().clear_hooks(hook_type)


# Alias for backward compatibility
def get_global_manager() -> PluginManager:
    """Get the global plugin manager instance (alias for get_plugin_manager)."""
    return get_plugin_manager()
