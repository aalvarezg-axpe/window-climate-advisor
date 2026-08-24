"""Run the repository's cross-platform verification gate."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PARTS = {
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "artifacts",
    "config",
    "htmlcov",
    "test-results",
}
SECRET_PATTERNS = (
    re.compile(r"(?m)^HOME_ASSISTANT_(?:ACCESS_TOKEN|URL)[ \t]*=[ \t]*\S+"),
    re.compile(r"-----BEGIN (?:EC |OPENSSH |RSA )?PRIVATE KEY-----"),
)


def run(command: list[str]) -> bool:
    """Run one command from the repository root."""
    print(f"+ {' '.join(command)}", flush=True)
    return subprocess.run(command, cwd=ROOT, check=False).returncode == 0


def repository_files() -> list[Path]:
    """Return tracked and untracked, non-ignored repository files."""
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [ROOT / item for item in result.stdout.decode().split("\0") if item]


def check_artifacts() -> bool:
    """Reject generated artifacts, secrets, and malformed JSON."""
    problems: list[str] = []
    for path in repository_files():
        relative = path.relative_to(ROOT)
        if (
            any(part in FORBIDDEN_PARTS for part in relative.parts)
            or path.suffix.lower() in {".key", ".pem", ".pyc"}
            or path.name == ".env"
            or (path.name.startswith(".env.") and path.name != ".env.example")
        ):
            problems.append(f"forbidden artifact: {relative}")
            continue
        if path.suffix.lower() == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
                problems.append(f"invalid JSON: {relative}: {error}")
        try:
            text = path.read_text(encoding="utf-8")
        except OSError, UnicodeDecodeError:
            continue
        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            problems.append(f"possible secret: {relative}")
    for problem in problems:
        print(problem, file=sys.stderr)
    return not problems


def main() -> int:
    """Run static checks and the available test suite."""
    commands = [
        ["git", "diff", "--check"],
        ["git", "diff", "--cached", "--check"],
        [sys.executable, "-m", "ruff", "check", "."],
        [sys.executable, "-m", "ruff", "format", "--check", "."],
    ]
    if not check_artifacts():
        return 1
    if not all(run(command) for command in commands):
        return 1

    mypy_targets = ["scripts"]
    if (ROOT / "custom_components").is_dir():
        mypy_targets.append("custom_components")
    if not run([sys.executable, "-m", "mypy", *mypy_targets]):
        return 1

    tests = ROOT / "tests"
    if any(tests.rglob("test_*.py")) and not run([sys.executable, "-m", "pytest"]):
        return 1
    if not tests.is_dir():
        print("- pytest: skipped until P00-T03 creates the test scaffold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
