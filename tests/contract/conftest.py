import pytest
from jsonschema import Draft202012Validator, FormatChecker


@pytest.fixture
def assert_matches():
    """Validate a response body against a schema and show every mismatch at once."""

    def _assert_matches(body, schema):
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        errors = sorted(validator.iter_errors(body), key=lambda e: list(e.path))
        if errors:
            details = "\n".join(f"  {'/'.join(map(str, e.path)) or '(root)'}: {e.message}" for e in errors)
            pytest.fail(f"Response does not match the contract:\n{details}")

    return _assert_matches
