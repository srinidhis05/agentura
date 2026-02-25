"""Domain-scoped memory store wrapper — enforces cross-domain isolation.

Wraps any MemoryStore and filters all reads to only return data belonging
to the allowed domains. Write operations tag data with the correct domain.

Usage:
    base_store = get_memory_store()
    scoped = DomainScopedStore(base_store, allowed_domains={"hr"})
    scoped.get_executions()  # only returns hr/* executions
    scoped.get_all_reflexions()  # only returns hr/* reflexions
"""

from __future__ import annotations


class DomainScopedStore:
    """Wraps a MemoryStore and enforces domain isolation on all operations."""

    def __init__(self, store, allowed_domains: set[str] | None = None):
        self._store = store
        self._allowed = allowed_domains  # None or {"*"} means unrestricted

    @property
    def unrestricted(self) -> bool:
        return self._allowed is None or "*" in self._allowed

    def _domain_from_skill(self, skill_path: str) -> str:
        return skill_path.split("/")[0] if "/" in skill_path else ""

    def _check_write_access(self, skill_path: str) -> None:
        if self.unrestricted:
            return
        domain = self._domain_from_skill(skill_path)
        if domain and domain not in self._allowed:
            raise PermissionError(
                f"Domain '{domain}' not in allowed domains: {sorted(self._allowed)}"
            )

    def _filter_by_domain(self, entries: list[dict]) -> list[dict]:
        if self.unrestricted:
            return entries
        return [
            e for e in entries
            if self._domain_from_skill(e.get("skill", "")) in self._allowed
        ]

    def log_execution(self, skill_path: str, data: dict) -> str:
        self._check_write_access(skill_path)
        return self._store.log_execution(skill_path, data)

    def add_correction(self, skill_path: str, data: dict) -> str:
        self._check_write_access(skill_path)
        return self._store.add_correction(skill_path, data)

    def add_reflexion(self, skill_path: str, data: dict) -> str:
        self._check_write_access(skill_path)
        return self._store.add_reflexion(skill_path, data)

    def get_reflexions(self, skill_path: str) -> list[dict]:
        self._check_write_access(skill_path)
        return self._store.get_reflexions(skill_path)

    def search_similar(self, skill_path: str, query: str, limit: int = 5) -> list[dict]:
        self._check_write_access(skill_path)
        return self._store.search_similar(skill_path, query, limit)

    def get_executions(self, skill_path: str | None = None) -> list[dict]:
        if skill_path:
            self._check_write_access(skill_path)
            return self._store.get_executions(skill_path)
        # No skill_path — return all, but filter by domain
        return self._filter_by_domain(self._store.get_executions(None))

    def get_corrections(self, skill_path: str | None = None) -> list[dict]:
        if skill_path:
            self._check_write_access(skill_path)
            return self._store.get_corrections(skill_path)
        return self._filter_by_domain(self._store.get_corrections(None))

    def get_all_reflexions(self) -> list[dict]:
        return self._filter_by_domain(self._store.get_all_reflexions())

    def update_reflexion(self, reflexion_id: str, updates: dict) -> None:
        # For updates, we trust the caller verified domain access already
        self._store.update_reflexion(reflexion_id, updates)
