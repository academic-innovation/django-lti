import nox


@nox.session
def format(session):
    """Checks that code is correctly formatted using black."""
    session.install("-r", "requirements.txt")
    session.run("black", ".", "--check")
