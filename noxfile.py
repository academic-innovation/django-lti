import nox

nox.options.default_venv_backend = "uv"


def install_dev(session):
    """Installs the project and its dev dependency group from the lockfile."""
    session.run_install(
        "uv",
        "sync",
        "--locked",
        "--group",
        "dev",
        "--python",
        session.virtualenv.location,
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )


@nox.session
def lint(session):
    """Checks for linting errors with ruff."""
    install_dev(session)
    session.run("ruff", "check")


@nox.session
def format(session):  # noqa: A001
    """Checks that code is correctly formatted using ruff."""
    install_dev(session)
    session.run("ruff", "format", "--check")


@nox.session
def types(session):
    """Check types using mypy."""
    install_dev(session)
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
    install_dev(session)
    session.install(f"django~={django}")
    session.run("pytest")
