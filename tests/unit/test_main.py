import os
import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient

from app.main import app, setup_exception_handlers, setup_mcp_authorize_resource_rewrite


@pytest.fixture
def client():
    yield TestClient(app)


def _auth_headers():
    return {"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"}


class TestExceptionHandler:
    def test_http_exception_with_status_prefix(self, client):
        response = client.post(
            "/auth/login",
            json={"username": "nonexistent", "password": "wrong"},
        )
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_http_exception_with_409_prefix(self):
        test_app = FastAPI()
        setup_exception_handlers(test_app)

        @test_app.get("/test-409-prefix")
        async def trigger_409():
            raise HTTPException(status_code=500, detail="409: Conflict occurred")

        test_client = TestClient(test_app)
        response = test_client.get("/test-409-prefix")
        assert response.status_code == 409
        assert response.json()["detail"] == "Conflict occurred"

    def test_http_exception_without_prefix(self):
        test_app = FastAPI()
        setup_exception_handlers(test_app)

        @test_app.get("/test-plain-error")
        async def trigger_plain():
            raise HTTPException(status_code=422, detail="Validation failed")

        test_client = TestClient(test_app)
        response = test_client.get("/test-plain-error")
        assert response.status_code == 422
        assert response.json()["detail"] == "Validation failed"


class TestMcpSlashRewrite:
    def test_mcp_path_rewrite(self, client):
        response = client.get("/mcp")
        assert response.status_code != 404

    def test_mcp_slash_path_works(self, client):
        response = client.get("/mcp/")
        assert response.status_code != 404


class TestResourceMetadata:
    def test_oauth_protected_resource_metadata(self, client):
        response = client.get("/.well-known/oauth-protected-resource/mcp")
        assert response.status_code == 200
        data = response.json()
        assert data["resource"] == "http://localhost/mcp"
        assert data["authorization_servers"] == ["http://localhost/mcp"]

    def test_oauth_protected_resource_metadata_trailing_slash(self, client):
        response = client.get("/.well-known/oauth-protected-resource/mcp/")
        assert response.status_code == 200
        data = response.json()
        assert data["resource"] == "http://localhost/mcp"

    def test_oauth_protected_resource_metadata_no_user_agent(self, client):
        response = client.get(
            "/.well-known/oauth-protected-resource/mcp",
            headers={"User-Agent": ""},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["resource"] == "http://localhost"
        assert data["authorization_servers"] == ["http://localhost/mcp"]

    def test_oauth_authorization_server_metadata(self, client):
        response = client.get("/.well-known/oauth-authorization-server/mcp")
        assert response.status_code == 200
        data = response.json()
        assert "issuer" in data

    def test_oauth_authorization_server_metadata_trailing_slash(self, client):
        response = client.get("/.well-known/oauth-authorization-server/mcp/")
        assert response.status_code == 200


class TestMcpAuthorizeResourceRewrite:
    def _build_app(self, auth_enabled: bool):
        class FakeContainer:
            def config(self_inner):
                return {
                    "auth": {"enabled": auth_enabled},
                    "api_base_url": "http://localhost",
                }

        test_app = FastAPI()
        setup_mcp_authorize_resource_rewrite(FakeContainer(), test_app)

        @test_app.get("/mcp/authorize")
        async def echo(request: Request):
            return {"resource": request.query_params.get("resource")}

        return TestClient(test_app)

    def test_rewrites_bare_origin_to_path_qualified(self):
        client = self._build_app(auth_enabled=True)
        response = client.get(
            "/mcp/authorize",
            params={"resource": "http://localhost", "client_id": "x"},
        )
        assert response.status_code == 200
        assert response.json()["resource"] == "http://localhost/mcp"

    def test_passes_through_path_qualified_resource(self):
        client = self._build_app(auth_enabled=True)
        response = client.get(
            "/mcp/authorize",
            params={"resource": "http://localhost/mcp", "client_id": "x"},
        )
        assert response.status_code == 200
        assert response.json()["resource"] == "http://localhost/mcp"

    def test_skips_when_auth_disabled(self):
        client = self._build_app(auth_enabled=False)
        response = client.get(
            "/mcp/authorize",
            params={"resource": "http://localhost", "client_id": "x"},
        )
        assert response.status_code == 200
        assert response.json()["resource"] == "http://localhost"
