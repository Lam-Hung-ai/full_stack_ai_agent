"""Register shared fixtures for the complete test suite."""

pytest_plugins = (
    "tests.fixtures.ai",
    "tests.fixtures.auth",
    "tests.fixtures.client",
    "tests.fixtures.database",
    "tests.fixtures.mail",
    "tests.fixtures.storage",
)
