"""Register shared fixtures for the complete test suite."""

pytest_plugins = (
    "tests.fixtures.client",
    "tests.fixtures.database",
)
