"""Tests for auth middleware."""

from agentura_sdk.server.auth import _extract_domain_from_path, get_auth_required


class TestDomainExtraction:
    def test_skills_path(self):
        assert _extract_domain_from_path("/api/v1/skills/ecm/triage") == "ecm"

    def test_domains_path(self):
        assert _extract_domain_from_path("/api/v1/domains/frm") == "frm"

    def test_knowledge_search_path(self):
        assert _extract_domain_from_path("/api/v1/knowledge/search/ecm/triage") == "ecm"

    def test_knowledge_validate_path(self):
        assert _extract_domain_from_path("/api/v1/knowledge/validate/ecm/triage") == "ecm"

    def test_memory_prompt_assembly_path(self):
        assert _extract_domain_from_path("/api/v1/memory/prompt-assembly/ecm/triage") == "ecm"

    def test_non_domain_path(self):
        assert _extract_domain_from_path("/api/v1/executions") is None

    def test_analytics_path(self):
        assert _extract_domain_from_path("/api/v1/analytics") is None

    def test_health_path(self):
        assert _extract_domain_from_path("/health") is None


class TestAuthRequired:
    def test_default_false(self, monkeypatch):
        monkeypatch.delenv("AUTH_REQUIRED", raising=False)
        assert get_auth_required() is False

    def test_true(self, monkeypatch):
        monkeypatch.setenv("AUTH_REQUIRED", "true")
        assert get_auth_required() is True

    def test_yes(self, monkeypatch):
        monkeypatch.setenv("AUTH_REQUIRED", "yes")
        assert get_auth_required() is True
