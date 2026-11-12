from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError
from pydantic_settings import SettingsConfigDict

from autonomous_coding_agent.config import Settings


class IsolatedSettings(Settings):
    """Test settings without loading a local .env file."""

    model_config = SettingsConfigDict(env_file=None)


@pytest.fixture(autouse=True)
def isolate_settings_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prevent unrelated environment variables from affecting tests."""
    for field_name in Settings.model_fields:
        monkeypatch.delenv(field_name.upper(), raising=False)


def test_settings_load_default_values() -> None:
    settings = IsolatedSettings()

    assert settings.app_name == "Autonomous Coding Agent"
    assert settings.environment == "development"
    assert settings.log_level == "INFO"
    assert settings.llm_provider == "gemini"
    assert settings.max_retries == 3
    assert settings.execution_timeout_seconds == 120
    assert settings.docker_network_disabled is True


def test_settings_load_environment_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("MAX_RETRIES", "5")
    monkeypatch.setenv("EXECUTION_TIMEOUT_SECONDS", "180")

    settings = IsolatedSettings()

    assert settings.llm_provider == "anthropic"
    assert settings.max_retries == 5
    assert settings.execution_timeout_seconds == 180


def test_settings_protect_api_keys() -> None:
    settings = IsolatedSettings(
        gemini_api_key=SecretStr("test-secret-key"),
    )

    assert settings.gemini_api_key is not None
    assert settings.gemini_api_key.get_secret_value() == "test-secret-key"
    assert "test-secret-key" not in str(settings.gemini_api_key)


def test_active_llm_api_key_selects_gemini_key() -> None:
    settings = IsolatedSettings(
        llm_provider="gemini",
        gemini_api_key=SecretStr("gemini-secret"),
        anthropic_api_key=SecretStr("anthropic-secret"),
    )

    assert settings.active_llm_api_key is not None
    assert settings.active_llm_api_key.get_secret_value() == "gemini-secret"


def test_active_llm_api_key_selects_anthropic_key() -> None:
    settings = IsolatedSettings(
        llm_provider="anthropic",
        gemini_api_key=SecretStr("gemini-secret"),
        anthropic_api_key=SecretStr("anthropic-secret"),
    )

    assert settings.active_llm_api_key is not None
    assert settings.active_llm_api_key.get_secret_value() == "anthropic-secret"


def test_settings_accept_custom_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "agent-workspaces"

    settings = IsolatedSettings(workspace_root=workspace)

    assert settings.workspace_root == workspace


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("max_retries", -1),
        ("max_retries", 11),
        ("execution_timeout_seconds", 0),
        ("execution_timeout_seconds", 3601),
        ("docker_memory_limit_mb", 64),
        ("docker_cpu_limit", 0),
    ],
)
def test_settings_reject_invalid_limits(
    field: str,
    value: int | float,
) -> None:
    with pytest.raises(ValidationError):
        IsolatedSettings.model_validate({field: value})


def test_settings_reject_invalid_llm_provider() -> None:
    with pytest.raises(ValidationError):
        IsolatedSettings.model_validate({"llm_provider": "invalid"})


def test_settings_reject_invalid_environment() -> None:
    with pytest.raises(ValidationError):
        IsolatedSettings.model_validate({"environment": "invalid"})
