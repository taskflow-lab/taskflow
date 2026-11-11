import pytest

from tests.contract import schemas


@pytest.mark.parametrize("url", ["/health", "/api/v1/health"])
def test_health_contract(client, url, assert_matches):
    assert_matches(client.get(url).json, schemas.HEALTH)


@pytest.mark.parametrize("url", ["/ready", "/api/v1/ready"])
def test_ready_contract(client, url, assert_matches):
    assert_matches(client.get(url).json, schemas.READY)
