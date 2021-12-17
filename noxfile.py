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
@nox.parametrize(
    "python,django",
    [
        (python, django)
        for python in ("3.6", "3.7", "3.8", "3.9", "3.10")
        for django in ("3.2.0", "4.0.0")
        if (python, django) not in [("3.6", "4.0.0"), ("3.7", "4.0.0")]
    ],
)
def test(session, django):
    """Runs tests with pytest."""
    session.install(f"django~={django}")
    session.install("-r", "requirements.txt")
    session.run("pytest")
