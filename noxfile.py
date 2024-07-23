"""Nox file for testing, creating quick development shells."""

import os
from pathlib import Path

import nox

nox.options.sessions = ["unit_tests"]


@nox.session
def unit_tests(session: nox.Session) -> None:
    """Run all unit tests.

    Right now, this only runs the unit tests for wiki-categories.
    """
    session.install("-r", "requirements.txt", "-r", "requirements-dev.txt")

    # Test paths relative to src/
    tests = [
        Path("cmds/wikicategories.py"),
    ]

    with session.chdir(Path("src/").resolve()):
        tests = [str(p) for p in tests]

        session.run("python", "-m", "unittest", *tests, *session.posargs)


VENV_DEV_DIR = Path("./.venv").resolve()


@nox.session
def devsh(session: nox.Session) -> None:
    """Create a development shell at the path `.venv`."""
    session.install("virtualenv")
    _ = session.run("virtualenv", os.fsdecode(VENV_DEV_DIR), silent=True)

    python_bin = os.fsdecode(VENV_DEV_DIR / "bin" / "python")

    _ = session.run(
        python_bin,
        "-m",
        "pip",
        "install",
        "-r",
        "requirements.txt",
        "-r",
        "requirements-dev.txt",
        external=True,
    )
