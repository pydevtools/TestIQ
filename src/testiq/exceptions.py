"""
Custom exceptions for TestIQ.
Provides detailed error codes and categories for better error handling.
"""


class TestIQError(Exception):
    """Base exception for all TestIQ errors."""

    def __init__(self, message: str, error_code: str = "TESTIQ_ERROR") -> None:
        self.message = message
        self.error_code = error_code
        super().__init__(message)

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"


class ConfigurationError(TestIQError):
    """Configuration-related errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "CONFIG_ERROR")


class ValidationError(TestIQError):
    """Input validation errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "VALIDATION_ERROR")


class SecurityError(TestIQError):
    """Security-related errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "SECURITY_ERROR")


class FileOperationError(TestIQError):
    """File operation errors."""

    def __init__(self, message: str, filepath: str = "") -> None:
        self.filepath = filepath
        super().__init__(message, "FILE_ERROR")


class ParseError(TestIQError):
    """Data parsing errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "PARSE_ERROR")


class AnalysisError(TestIQError):
    """Analysis operation errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "ANALYSIS_ERROR")


class ResourceLimitError(TestIQError):
    """Resource limit exceeded errors."""

    def __init__(self, message: str, limit_type: str = "") -> None:
        self.limit_type = limit_type
        super().__init__(message, "RESOURCE_LIMIT_ERROR")
