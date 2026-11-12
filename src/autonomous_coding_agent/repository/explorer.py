"""Safe metadata inspection for local Git repositories."""

import os
import stat
import subprocess
from pathlib import Path, PurePosixPath

from autonomous_coding_agent.config import Settings, get_settings
from autonomous_coding_agent.domain.errors import RepositoryError
from autonomous_coding_agent.domain.models import RepositorySnapshot

_IGNORED_DIRECTORIES = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        ".nox",
        ".agent-workspaces",
        "node_modules",
        "dist",
        "build",
        "htmlcov",
        ".idea",
    }
)

_SENSITIVE_FILENAMES = frozenset(
    {
        "credentials.json",
        "secrets.json",
        "id_rsa",
        "id_ed25519",
        "service-account.json",
    }
)

_PRIVATE_KEY_SUFFIXES = frozenset({".pem", ".key", ".p12", ".pfx", ".keystore"})

_LANGUAGE_BY_SUFFIX = {
    ".py": "Python",
    ".pyi": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".cpp": "C++",
    ".cc": "C++",
    ".c": "C",
    ".h": "C/C++",
    ".hpp": "C++",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".sql": "SQL",
}

_DEPENDENCY_FILENAMES = frozenset(
    {
        "pyproject.toml",
        "poetry.lock",
        "uv.lock",
        "pipfile",
        "pipfile.lock",
        "setup.py",
        "setup.cfg",
        "requirements.txt",
    }
)


class RepositoryExplorer:
    """Inspect repository metadata without reading source contents."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def inspect(self, repository_path: Path) -> RepositorySnapshot:
        """Inspect a Git repository and return a validated snapshot."""

        try:
            requested_path = repository_path.expanduser().resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise RepositoryError(
                "Repository path does not exist or cannot be resolved."
            ) from exc

        if not requested_path.is_dir():
            raise RepositoryError("Repository path must be a directory.")

        root_result = self._run_git(
            requested_path,
            "rev-parse",
            "--show-toplevel",
        )

        if root_result.returncode != 0:
            raise RepositoryError(
                "The supplied directory is not inside a Git repository."
            )

        try:
            repository_root = Path(self._decode(root_result).strip()).resolve(
                strict=True
            )
        except (OSError, RuntimeError) as exc:
            raise RepositoryError("Could not resolve the Git repository root.") from exc

        if not repository_root.is_dir():
            raise RepositoryError("Git repository root is invalid.")

        head_result = self._run_git(
            repository_root,
            "rev-parse",
            "--verify",
            "HEAD",
        )

        base_commit = (
            self._decode(head_result).strip() if head_result.returncode == 0 else None
        )

        file_result = self._run_git(
            repository_root,
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
        )

        if file_result.returncode != 0:
            raise RepositoryError("Could not retrieve repository file information.")

        discovered_paths = sorted(
            {
                os.fsdecode(raw_path)
                for raw_path in file_result.stdout.split(b"\0")
                if raw_path
            }
        )

        accepted_files: list[str] = []

        for relative_path in discovered_paths:
            if self._should_skip(relative_path):
                continue

            candidate = repository_root.joinpath(*PurePosixPath(relative_path).parts)

            if self._contains_symlink(repository_root, candidate):
                continue

            try:
                file_info = candidate.lstat()
            except OSError:
                continue

            if not stat.S_ISREG(file_info.st_mode):
                continue

            if file_info.st_size > self.settings.max_file_size_bytes:
                continue

            accepted_files.append(relative_path)

            if len(accepted_files) >= self.settings.max_files_to_inspect:
                break

        detected_languages: set[str] = set()

        for path in accepted_files:
            language = self._detect_language(path)
            if language is not None:
                detected_languages.add(language)

        languages = sorted(detected_languages)

        dependency_files = [
            path for path in accepted_files if self._is_dependency_file(path)
        ]

        return RepositorySnapshot(
            repository_path=repository_root,
            base_commit=base_commit,
            files=accepted_files,
            languages=languages,
            dependency_files=dependency_files,
        )

    @staticmethod
    def _run_git(
        repository_path: Path,
        *arguments: str,
    ) -> subprocess.CompletedProcess[bytes]:
        """Execute a fixed, read-only Git operation."""

        try:
            return subprocess.run(
                [
                    "git",
                    "-C",
                    str(repository_path),
                    *arguments,
                ],
                capture_output=True,
                check=False,
                timeout=15,
            )
        except FileNotFoundError as exc:
            raise RepositoryError("Git executable was not found.") from exc
        except subprocess.TimeoutExpired as exc:
            raise RepositoryError("Git operation exceeded its timeout.") from exc
        except OSError as exc:
            raise RepositoryError("Git operation could not be executed.") from exc

    @staticmethod
    def _decode(
        result: subprocess.CompletedProcess[bytes],
    ) -> str:
        """Decode Git output safely."""

        return result.stdout.decode("utf-8", errors="replace")

    @staticmethod
    def _should_skip(relative_path: str) -> bool:
        """Exclude generated directories and sensitive filenames."""

        path = PurePosixPath(relative_path)

        if path.is_absolute() or ".." in path.parts or not path.parts:
            return True

        if any(part.lower() in _IGNORED_DIRECTORIES for part in path.parts[:-1]):
            return True

        filename = path.name.lower()

        if filename == ".env" or (
            filename.startswith(".env.") and filename != ".env.example"
        ):
            return True

        if filename in _SENSITIVE_FILENAMES:
            return True

        if PurePosixPath(filename).suffix in _PRIVATE_KEY_SUFFIXES:
            return True

        return False

    @staticmethod
    def _contains_symlink(root: Path, candidate: Path) -> bool:
        """Reject paths containing symbolic links."""

        current = root

        try:
            relative = candidate.relative_to(root)

            for part in relative.parts:
                current = current / part

                if current.is_symlink():
                    return True

        except (OSError, ValueError):
            return True

        return False

    @staticmethod
    def _detect_language(relative_path: str) -> str | None:
        """Identify a language using its file extension."""

        suffix = PurePosixPath(relative_path).suffix.lower()

        return _LANGUAGE_BY_SUFFIX.get(suffix)

    @staticmethod
    def _is_dependency_file(relative_path: str) -> bool:
        """Identify common dependency and packaging files."""

        filename = PurePosixPath(relative_path).name.lower()

        return (
            filename in _DEPENDENCY_FILENAMES
            or (filename.startswith("requirements") and filename.endswith(".txt"))
            or (filename.startswith("constraints") and filename.endswith(".txt"))
        )
