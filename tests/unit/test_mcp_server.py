from unittest.mock import MagicMock, patch

from app.interface.mcp.schema import (
    AgentItem,
    PublishContentResult,
    _get_mcp_schema,
)
from app.interface.mcp.server import _build_auth
from app.interface.mcp.registrar import McpRegistrar
from app.interface.mcp.default_tool_registrar import DefaultToolRegistrar
from app.interface.mcp.prompt_registry import PromptRegistry


class TestMcpModels:
    def test_agent_item(self):
        item = AgentItem(
            id="a1",
            agent_name="Test Agent",
            agent_type="test_echo",
            agent_summary="An echo agent",
            language_model_id="lm1",
            is_active=True,
        )
        assert item.id == "a1"
        assert item.agent_name == "Test Agent"
        assert item.agent_type == "test_echo"
        assert item.is_active is True

    def test_publish_content_result(self):
        result = PublishContentResult(
            status="published",
            message="Content published successfully",
            doc_id="doc-123",
        )
        assert result.status == "published"
        assert result.message == "Content published successfully"
        assert result.doc_id == "doc-123"


class TestBuildAuth:
    def test_build_auth_disabled(self):
        config = {"auth": {"enabled": False}}
        result = _build_auth(config)
        assert result is None

    @patch("key_value.aio.wrappers.encryption.FernetEncryptionWrapper")
    @patch("key_value.aio.stores.redis.RedisStore")
    @patch("fastmcp.server.auth.providers.jwt.JWTVerifier")
    @patch("fastmcp.server.auth.OAuthProxy")
    def test_build_auth_enabled(
        self, mock_oauth, mock_jwt, mock_redis_store, mock_fernet_wrapper
    ):
        config = {
            "auth": {
                "enabled": True,
                "url": "http://keycloak:8080",
                "realm": "test-realm",
                "client_id": "test-client",
                "client_secret": "test-secret",
            },
            "api_base_url": "http://localhost:8000",
            "broker": {"url": "redis://localhost:6379/0"},
        }

        _build_auth(config)

        mock_jwt.assert_called_once()
        mock_oauth.assert_called_once()
        mock_redis_store.assert_called_once_with(url="redis://localhost:6379/0")
        mock_fernet_wrapper.assert_called_once()
        wrapper_kwargs = mock_fernet_wrapper.call_args[1]
        assert wrapper_kwargs["key_value"] is mock_redis_store.return_value
        assert wrapper_kwargs["raise_on_decryption_error"] is False
        call_kwargs = mock_oauth.call_args[1]
        assert "test-realm" in call_kwargs["upstream_authorization_endpoint"]
        assert "test-realm" in call_kwargs["upstream_token_endpoint"]
        assert call_kwargs["upstream_client_id"] == "test-client"
        assert call_kwargs["base_url"] == "http://localhost:8000/mcp"
        assert call_kwargs["client_storage"] is mock_fernet_wrapper.return_value


class TestGetMcpSchema:
    @patch("app.interface.mcp.schema.get_access_token", return_value=None)
    def test_get_mcp_schema_no_token(self, mock_token):
        result = _get_mcp_schema()
        assert result == "public"

    @patch("app.interface.mcp.schema.get_access_token")
    def test_get_mcp_schema_with_token(self, mock_token):
        mock_token.return_value = MagicMock(claims={"sub": "abc-def-123"})
        result = _get_mcp_schema()
        assert result == "id_abc_def_123"

    @patch("app.interface.mcp.schema.get_access_token")
    def test_get_mcp_schema_token_no_sub(self, mock_token):
        mock_token.return_value = MagicMock(claims={})
        result = _get_mcp_schema()
        assert result == "public"


class TestMcpRegistrar:
    def test_base_registrar_no_ops(self):
        class NoOpRegistrar(McpRegistrar):
            pass

        registrar = NoOpRegistrar()
        mcp = MagicMock()
        container = MagicMock()
        registrar.register_tools(mcp, container)
        registrar.register_prompts(mcp)
        registrar.register_resources(mcp)

    def test_default_tool_registrar_is_mcp_registrar(self):
        assert issubclass(DefaultToolRegistrar, McpRegistrar)

    def test_default_tool_registrar_registers_tools(self):
        registrar = DefaultToolRegistrar(PromptRegistry())
        mcp = MagicMock()
        container = MagicMock()
        registrar.register_tools(mcp, container)
        tool_names = sorted(call[1]["name"] for call in mcp.tool.call_args_list)
        assert tool_names == [
            "get_agent_list",
            "publish_content_mcp",
            "read_prompt_mcp",
        ]

    def test_custom_registrar_overrides(self):
        class CustomRegistrar(McpRegistrar):
            def register_prompts(self, mcp):
                mcp.prompt(name="test_prompt")(lambda: "test")

        registrar = CustomRegistrar()
        mcp = MagicMock()
        container = MagicMock()
        registrar.register_prompts(mcp)
        mcp.prompt.assert_called_once_with(name="test_prompt")
        registrar.register_tools(mcp, container)
        registrar.register_resources(mcp)
