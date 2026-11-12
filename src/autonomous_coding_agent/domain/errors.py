"""Application-specific exception hierarchy."""


class AgentError(Exception):
    """Base exception for all application errors."""


class ConfigurationError(AgentError):
    """Raised when application configuration is invalid."""


class InvalidTaskError(AgentError):
    """Raised when a submitted task is invalid."""


class RepositoryError(AgentError):
    """Raised when repository operations fail."""


class WorkspaceError(RepositoryError):
    """Raised when workspace operations fail."""


class LLMError(AgentError):
    """Raised when an LLM operation fails."""


class SandboxError(AgentError):
    """Raised when sandbox execution fails."""


class ApprovalError(AgentError):
    """Raised when an approval operation fails."""


class PersistenceError(AgentError):
    """Raised when state persistence operations fail."""


__all__ = [
    "AgentError",
    "ApprovalError",
    "ConfigurationError",
    "InvalidTaskError",
    "LLMError",
    "PersistenceError",
    "RepositoryError",
    "SandboxError",
    "WorkspaceError",
]
