import pytest

from autonomous_coding_agent.domain.errors import (
    AgentError,
    ApprovalError,
    ConfigurationError,
    InvalidTaskError,
    LLMError,
    PersistenceError,
    RepositoryError,
    SandboxError,
    WorkspaceError,
)


@pytest.mark.parametrize(
    "exception_type",
    [
        ConfigurationError,
        InvalidTaskError,
        RepositoryError,
        WorkspaceError,
        LLMError,
        SandboxError,
        ApprovalError,
        PersistenceError,
    ],
)
def test_all_application_errors_inherit_from_agent_error(
    exception_type: type[AgentError],
) -> None:
    error = exception_type("Test error")

    assert isinstance(error, AgentError)
    assert str(error) == "Test error"


def test_workspace_error_inherits_from_repository_error() -> None:
    error = WorkspaceError("Workspace creation failed")

    assert isinstance(error, RepositoryError)
    assert isinstance(error, AgentError)
