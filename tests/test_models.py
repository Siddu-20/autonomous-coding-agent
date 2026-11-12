from pathlib import Path

import pytest
from pydantic import ValidationError

from autonomous_coding_agent.domain.models import (
    ApprovalStatus,
    ExecutionPlan,
    ExecutionResult,
    FileChange,
    FileChangeType,
    PlanStep,
    RepositorySnapshot,
    TaskRequest,
    TaskStatus,
)


def test_task_request_generates_unique_id(tmp_path: Path) -> None:
    request = TaskRequest(
        task_description="Fix authentication validation",
        repository_path=tmp_path,
    )

    assert request.task_id
    assert request.repository_path == tmp_path
    assert request.task_description == "Fix authentication validation"


def test_task_request_rejects_empty_description(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        TaskRequest(task_description="   ", repository_path=tmp_path)


def test_task_request_rejects_relative_repository_path() -> None:
    with pytest.raises(ValidationError):
        TaskRequest(
            task_description="Fix a bug",
            repository_path=Path("relative/repository"),
        )


def test_execution_plan_accepts_valid_steps() -> None:
    plan = ExecutionPlan(
        goal="Fix authentication",
        steps=[
            PlanStep(
                step_number=1,
                description="Inspect authentication code",
                target_files=["src/auth.py"],
            ),
            PlanStep(
                step_number=2,
                description="Add validation",
                target_files=["src/auth.py"],
            ),
        ],
        acceptance_criteria=["All authentication tests pass"],
    )

    assert len(plan.steps) == 2


def test_execution_plan_rejects_duplicate_step_numbers() -> None:
    with pytest.raises(ValidationError):
        ExecutionPlan(
            goal="Fix authentication",
            steps=[
                PlanStep(step_number=1, description="Inspect code"),
                PlanStep(step_number=1, description="Modify code"),
            ],
            acceptance_criteria=["Tests pass"],
        )


def test_repository_snapshot_validates_and_counts_files(
    tmp_path: Path,
) -> None:
    snapshot = RepositorySnapshot(
        repository_path=tmp_path,
        files=["src\\main.py", "tests/test_main.py"],
        languages=["Python"],
        dependency_files=["pyproject.toml"],
    )

    assert snapshot.file_count == 2
    assert snapshot.files[0] == "src/main.py"


@pytest.mark.parametrize(
    "path",
    [
        "../outside.py",
        "/etc/passwd",
        "C:\\Windows\\secret.py",
    ],
)
def test_file_change_rejects_unsafe_paths(path: str) -> None:
    with pytest.raises(ValidationError):
        FileChange(
            path=path,
            change_type=FileChangeType.MODIFIED,
            diff="Sample diff",
        )


def test_file_change_accepts_valid_rename() -> None:
    change = FileChange(
        path="src/new_name.py",
        previous_path="src/old_name.py",
        change_type=FileChangeType.RENAMED,
        diff="Rename file",
    )

    assert change.previous_path == "src/old_name.py"


def test_file_change_rejects_rename_without_previous_path() -> None:
    with pytest.raises(ValidationError):
        FileChange(
            path="src/new_name.py",
            change_type=FileChangeType.RENAMED,
            diff="Rename file",
        )


def test_execution_result_detects_success() -> None:
    result = ExecutionResult(
        command=["python", "-m", "pytest"],
        exit_code=0,
        duration_seconds=1.5,
    )

    assert result.succeeded is True


def test_execution_result_detects_failure_and_timeout() -> None:
    failure = ExecutionResult(
        command=["python", "-m", "pytest"],
        exit_code=1,
        stderr="Tests failed",
        duration_seconds=2.0,
    )

    timeout = ExecutionResult(
        command=["python", "long_running.py"],
        exit_code=None,
        duration_seconds=30.0,
        timed_out=True,
    )

    assert failure.succeeded is False
    assert timeout.succeeded is False


def test_status_enums_have_expected_values() -> None:
    assert TaskStatus.PENDING.value == "pending"
    assert TaskStatus.SUCCEEDED.value == "succeeded"
    assert ApprovalStatus.APPROVED.value == "approved"
