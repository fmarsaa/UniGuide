"""The web admin portal runs in a browser, so the server must say which websites may
call it. Only the portal's own addresses are allowed - not every site on the internet."""

import pytest
from fastapi.testclient import TestClient

import main

pytestmark = pytest.mark.skipif(main._pipeline is None, reason="rf_model_pipeline.pkl not trained yet")


def _preflight(origin):
    client = TestClient(main.app)
    return client.options(
        "/api/health",
        headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
    )


def test_the_portals_own_address_is_allowed():
    response = _preflight("http://localhost:5000")
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5000"


def test_some_other_website_is_not_allowed():
    response = _preflight("https://some-other-site.example")
    assert response.headers.get("access-control-allow-origin") is None


def test_the_wildcard_is_gone():
    assert "*" not in main.CORS_ORIGINS
