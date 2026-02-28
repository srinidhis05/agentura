"""Tests for OpenRouter integration."""

from agentura_sdk.runner.openrouter import resolve_model, MODEL_ALIASES, FALLBACK_CHAINS


class TestModelResolution:
    def test_alias_resolution(self):
        assert resolve_model("claude-sonnet-4.5") == "anthropic/claude-sonnet-4.5"
        assert resolve_model("gpt-4o") == "openai/gpt-4o"
        assert resolve_model("deepseek-v3") == "deepseek/deepseek-chat"

    def test_passthrough_full_id(self):
        assert resolve_model("anthropic/claude-opus-4") == "anthropic/claude-opus-4"

    def test_unknown_model_passthrough(self):
        assert resolve_model("custom/my-model") == "custom/my-model"

    def test_fallback_chains_exist(self):
        assert "anthropic/claude-sonnet-4.5" in FALLBACK_CHAINS
        assert len(FALLBACK_CHAINS["anthropic/claude-sonnet-4.5"]) >= 1

    def test_all_aliases_are_strings(self):
        for alias, full_id in MODEL_ALIASES.items():
            assert isinstance(alias, str)
            assert isinstance(full_id, str)
            assert "/" in full_id
