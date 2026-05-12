import os
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.main import app, setup_exception_handlers

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
        assert "resource" in data

    def test_oauth_protected_resource_metadata_trailing_slash(self, client):
        response = client.get("/.well-known/oauth-protected-resource/mcp/")
        assert response.status_code == 200

    def test_oauth_authorization_server_metadata(self, client):
        response = client.get("/.well-known/oauth-authorization-server/mcp")
        assert response.status_code == 200
        data = response.json()
        assert "issuer" in data

    def test_oauth_authorization_server_metadata_trailing_slash(self, client):
        response = client.get("/.well-known/oauth-authorization-server/mcp/")
        assert response.status_code == 200
