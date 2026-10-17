import json
import logging

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.healthcheck import healthcheck_router


@pytest.fixture(name="test_client")
def fixture_test_client():
    # Routes need FastAPI's middleware (e.g. fastapi_middleware_astack), so serve
    # the router from a FastAPI app rather than using it as the ASGI app directly
    app = FastAPI()
    app.include_router(healthcheck_router)
    return TestClient(app)


class TestAPI:
    def test_get_healthcheck_200(self, caplog, test_client):
        with caplog.at_level(logging.INFO):
            response = test_client.get("/health")
            response_data = json.loads(response.content)
            assert response.status_code == 200
            assert response_data["status"] == "OK"
            assert "Healthy" in caplog.messages[1]

    def test_head_healthcheck_200(self, caplog, test_client):
        response = test_client.head("/health")
        assert response.status_code == 200

    # This endpoint is only required by the infra CI "Test Service"
    # Adding test coverage to document this requirement -- this
    # test can be removed if we later add a page at '/'
    def test_get_root_200(self, caplog, test_client):
        with caplog.at_level(logging.INFO):
            response = test_client.get("/")
            assert response.status_code == 200
