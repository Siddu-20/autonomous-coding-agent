from pathlib import Path

import autonomous_coding_agent


def test_package_imports_from_src_layout() -> None:
    package_file = Path(autonomous_coding_agent.__file__ or "")

    assert package_file.name == "__init__.py"
    assert package_file.parent.name == "autonomous_coding_agent"
    assert "src" in package_file.parts
