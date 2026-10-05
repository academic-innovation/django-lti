import nox


@nox.session
def lint(session):
    """Checks for linting errors with ruff."""
    session.install("-r", "requirements.txt")
    session.run("ruff", "check")


@nox.session
def format(session):  # noqa: A001
    """Checks that code is correctly formatted using ruff."""
    session.install("-r", "requirements.txt")
    session.run("ruff", "format", "--check")


@nox.session
def types(session):
    """Check types using mypy."""
    session.install("-r", "requirements.txt")
    session.run("mypy", ".")


@nox.session
@nox.parametrize(
    "python,django",
    [
        (python, django)
        for python in ("3.10", "3.11", "3.12", "3.13", "3.14")
        for django in ("5.2.0", "6.0.0", "6.1.0")
        if (python, django)
        not in [
            ("3.10", "6.0.0"),
            ("3.11", "6.0.0"),
            ("3.10", "6.1.0"),
            ("3.11", "6.1.0"),
        ]
    ],
)
def test(session, django):
    """Runs tests with pytest."""
    session.install(f"django~={django}")
    session.install("-r", "requirements.txt")
    session.run("pytest")
