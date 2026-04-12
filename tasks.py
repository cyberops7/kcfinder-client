import live
from invoke import Collection, task


@task
def test(c):
    """Run the test suite."""
    c.run("uv run pytest -v", pty=True)


@task
def lint(c):
    """Run ruff linter."""
    c.run("uv run ruff check .", pty=True)


@task
def format(c):
    """Run ruff formatter."""
    c.run("uv run ruff format .", pty=True)


@task
def tc(c):
    """Run pyrefly type checker."""
    c.run("uv run pyrefly check", pty=True)


@task
def mdlint(c):
    """Run markdownlint on documentation."""
    c.run(
        "docker run --rm -i --platform linux/amd64 -v ./:/data"
        " markdownlint/markdownlint -s .markdownlint.rb"
        " README.md CLAUDE.md"
        " docs/auth.md docs/bulk.md docs/directories.md"
        " docs/exceptions.md docs/files.md docs/sync.md",
        pty=True,
    )


@task
def check(c):
    """Run lint, format check, typecheck, and markdown lint."""
    c.run("uv run ruff check .", pty=True)
    c.run("uv run ruff format --check .", pty=True)
    c.run("uv run pyrefly check", pty=True)
    mdlint(c)


@task
def scan(c):
    """Run security scanning (bandit + pip-audit)."""
    c.run("uv run bandit -r src/", pty=True)
    c.run("uv run pip-audit", pty=True)


@task
def build(c):
    """Build the package."""
    c.run("uv build", pty=True)


ns = Collection()
ns.add_task(test)
ns.add_task(lint)
ns.add_task(format)
ns.add_task(tc)
ns.add_task(mdlint)
ns.add_task(check)
ns.add_task(scan)
ns.add_task(build)
ns.add_collection(Collection.from_module(live))
