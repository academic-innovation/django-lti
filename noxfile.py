import nox


@nox.session
def lint(session):
    """Checks for linting errors with flake8."""
    session.install("-r", "requirements.txt")
    session.run("flake8")


@nox.session
def sort(session):
    """Checks that imports are correctly sorted using isort."""
    session.install("-r", "requirements.txt")
    session.run("isort", ".", "--check")


@nox.session
def format(session):
    """Checks that code is correctly formatted using black."""
    session.install("-r", "requirements.txt")
    session.run("black", ".", "--check")


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
        for django in ("5.2.0", "6.0.0")
        if (python, django) not in [("3.10", "6.0.0"), ("3.11", "6.0.0")]
    ],
)
def test(session, django):
    """Runs tests with pytest."""
    session.install(f"django~={django}")
    session.install("-r", "requirements.txt")
    session.run("pytest")
