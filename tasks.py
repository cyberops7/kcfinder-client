from invoke import task


@task
def test(c):
    """Run the test suite."""
    c.run("uv run pytest -v", pty=True)


@task
def lint(c):
    """Run ruff linter."""
    c.run("uv run ruff check src/ tests/", pty=True)


@task
def format(c):
    """Run ruff formatter."""
    c.run("uv run ruff format src/ tests/", pty=True)


@task
def tc(c):
    """Run pyrefly type checker."""
    c.run("uv run pyrefly check src/", pty=True)


@task
def check(c):
    """Run lint, format check, and typecheck."""
    c.run("uv run ruff check src/ tests/", pty=True)
    c.run("uv run ruff format --check src/ tests/", pty=True)
    c.run("uv run pyrefly check src/", pty=True)


@task
def scan(c):
    """Run security scanning (bandit + pip-audit)."""
    c.run("uv run bandit -r src/", pty=True)
    c.run("uv run pip-audit", pty=True)


@task
def build(c):
    """Build the package."""
    c.run("uv build", pty=True)
