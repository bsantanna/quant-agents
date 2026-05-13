import pytest

from app.interface.mcp.prompt_registry import PromptRegistry


class TestPromptRegistry:
    def test_register_and_resolve(self):
        registry = PromptRegistry()
        registry.register("p1", lambda **kwargs: f"rendered:{kwargs}")
        result = registry.resolve("p1", current_time="t", tickers="AAPL")
        assert "current_time" in result
        assert "AAPL" in result

    def test_duplicate_registration_raises(self):
        registry = PromptRegistry()
        registry.register("p1", lambda **_: "a")
        with pytest.raises(ValueError, match="already registered"):
            registry.register("p1", lambda **_: "b")

    def test_unknown_name_raises_with_available_list(self):
        registry = PromptRegistry()
        registry.register("alpha", lambda **_: "")
        registry.register("beta", lambda **_: "")
        with pytest.raises(KeyError) as excinfo:
            registry.resolve("gamma")
        message = str(excinfo.value)
        assert "gamma" in message
        assert "alpha" in message
        assert "beta" in message

    def test_unknown_name_with_empty_registry(self):
        registry = PromptRegistry()
        with pytest.raises(KeyError, match="<none>"):
            registry.resolve("x")

    def test_names_returns_sorted_keys(self):
        registry = PromptRegistry()
        registry.register("beta", lambda **_: "")
        registry.register("alpha", lambda **_: "")
        assert registry.names() == ["alpha", "beta"]

    def test_contains(self):
        registry = PromptRegistry()
        registry.register("alpha", lambda **_: "")
        assert "alpha" in registry
        assert "beta" not in registry

    def test_resolve_passes_kwargs_to_resolver(self):
        registry = PromptRegistry()
        captured: dict = {}

        def resolver(**kwargs):
            captured.update(kwargs)
            return "ok"

        registry.register("p", resolver)
        registry.resolve("p", a=1, b="two", c=None)
        assert captured == {"a": 1, "b": "two", "c": None}
