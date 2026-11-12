import subprocess
from pathlib import Path

import pytest

from autonomous_coding_agent.config import Settings
from autonomous_coding_agent.domain.errors import RepositoryError
from autonomous_coding_agent.repository.explorer import RepositoryExplorer


def initialize_repository(path: Path) -> None:
    """Initialize a temporary Git repository."""

    subprocess.run(
        ["git", "init", str(path)],
        check=True,
        capture_output=True,
    )


def test_explorer_rejects_nonexistent_repository(
    tmp_path: Path,
) -> None:
    explorer = RepositoryExplorer()

    with pytest.raises(RepositoryError):
        explorer.inspect(tmp_path / "missing")


def test_explorer_rejects_non_git_directory(
    tmp_path: Path,
) -> None:
    explorer = RepositoryExplorer()

    with pytest.raises(RepositoryError):
        explorer.inspect(tmp_path)


def test_explorer_discovers_repository_files(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "sample"
    initialize_repository(repository)

    (repository / "src").mkdir()
    (repository / "tests").mkdir()

    (repository / "src" / "main.py").write_text("print('hello')\n")
    (repository / "tests" / "test_main.py").write_text("def test_example(): pass\n")
    (repository / "pyproject.toml").write_text("[project]\nname='sample'\n")
    (repository / ".env.example").write_text("API_KEY=placeholder\n")

    settings = Settings(max_files_to_inspect=100)
    explorer = RepositoryExplorer(settings)

    snapshot = explorer.inspect(repository)

    assert "src/main.py" in snapshot.files
    assert "tests/test_main.py" in snapshot.files
    assert "pyproject.toml" in snapshot.files
    assert ".env.example" in snapshot.files

    assert snapshot.languages == ["Python"]
    assert snapshot.dependency_files == ["pyproject.toml"]


def test_explorer_excludes_sensitive_and_generated_files(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "sample"
    initialize_repository(repository)

    (repository / ".venv" / "lib").mkdir(parents=True)
    (repository / "node_modules" / "package").mkdir(parents=True)

    (repository / "main.py").write_text("print('hello')\n")
    (repository / ".env").write_text("SECRET=value\n")
    (repository / ".venv" / "lib" / "hidden.py").write_text("secret code")
    (repository / "node_modules" / "package" / "index.js").write_text(
        "module.exports = {};"
    )
    (repository / "credentials.json").write_text("{}")
    (repository / "private.pem").write_text("private key")

    # Force-add .env to simulate an accidentally committed secret.
    subprocess.run(
        ["git", "-C", str(repository), "add", "-f", ".env"],
        check=True,
        capture_output=True,
    )

    explorer = RepositoryExplorer()
    snapshot = explorer.inspect(repository)

    assert "main.py" in snapshot.files
    assert ".env" not in snapshot.files
    assert ".venv/lib/hidden.py" not in snapshot.files
    assert "node_modules/package/index.js" not in snapshot.files
    assert "credentials.json" not in snapshot.files
    assert "private.pem" not in snapshot.files


def test_explorer_enforces_file_size_limit(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "sample"
    initialize_repository(repository)

    (repository / "small.py").write_text("print('ok')\n")
    (repository / "large.txt").write_text("x" * 2048)

    settings = Settings(max_file_size_bytes=1024)
    snapshot = RepositoryExplorer(settings).inspect(repository)

    assert "small.py" in snapshot.files
    assert "large.txt" not in snapshot.files


def test_explorer_enforces_file_count_limit(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "sample"
    initialize_repository(repository)

    for name in ["a.py", "b.py", "c.py"]:
        (repository / name).write_text("pass\n")

    settings = Settings(max_files_to_inspect=2)
    snapshot = RepositoryExplorer(settings).inspect(repository)

    assert len(snapshot.files) == 2


def test_explorer_records_latest_commit(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "sample"
    initialize_repository(repository)

    (repository / "main.py").write_text("print('hello')\n")

    subprocess.run(
        ["git", "-C", str(repository), "add", "."],
        check=True,
        capture_output=True,
    )

    subprocess.run(
        [
            "git",
            "-C",
            str(repository),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-m",
            "Initial commit",
        ],
        check=True,
        capture_output=True,
    )

    snapshot = RepositoryExplorer().inspect(repository)

    assert snapshot.base_commit is not None
    assert len(snapshot.base_commit) == 40


def test_explorer_excludes_symlinked_files(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "sample"
    initialize_repository(repository)

    outside_directory = tmp_path / "outside"
    outside_directory.mkdir()

    outside_file = outside_directory / "secret.py"
    outside_file.write_text("SECRET = True\n")

    (repository / "safe.py").write_text("print('safe')\n")
    (repository / "linked.py").symlink_to(outside_file)

    snapshot = RepositoryExplorer().inspect(repository)

    assert "safe.py" in snapshot.files
    assert "linked.py" not in snapshot.files
