import os, pytest
HAS_PG = bool(os.environ.get("DATABASE_URL"))


def test_schema_has_tables():
    from agentura_sdk.memory.seat_store import SEAT_SCHEMA
    assert "CREATE TABLE IF NOT EXISTS seats" in SEAT_SCHEMA
    assert "CREATE TABLE IF NOT EXISTS seat_events" in SEAT_SCHEMA


@pytest.mark.skipif(not HAS_PG, reason="DATABASE_URL not set")
def test_get_or_create_is_idempotent():
    import uuid
    from agentura_sdk.memory.seat_store import SeatStore
    s = SeatStore()
    nm = f"dev/idem-{uuid.uuid4().hex[:8]}"
    a = s.get_or_create_seat(name=nm, role="idem", domain="dev")
    b = s.get_or_create_seat(name=nm, role="idem", domain="dev")
    assert a == b
    assert s.get_seat(a)["name"] == nm


@pytest.mark.skipif(not HAS_PG, reason="DATABASE_URL not set")
def test_current_model_not_wiped_by_empty():
    import uuid
    from agentura_sdk.memory.seat_store import SeatStore
    s = SeatStore()
    nm = f"dev/model-{uuid.uuid4().hex[:8]}"
    s.get_or_create_seat(name=nm, role="m", domain="dev", model="glm-5")
    s.get_or_create_seat(name=nm, role="m", domain="dev")  # empty model must NOT wipe
    assert s.get_seat_by_name(nm)["current_model"] == "glm-5"


@pytest.mark.skipif(not HAS_PG, reason="DATABASE_URL not set")
def test_track_record_math():
    from agentura_sdk.memory.seat_store import SeatStore
    s = SeatStore()
    seat = s.get_or_create_seat(name=f"dev/tr-{__import__('uuid').uuid4().hex[:8]}", role="tr", domain="dev")
    # empty record
    tr0 = s.get_track_record(seat)
    assert tr0["runs"] == 0 and tr0["success_rate"] == 0.0
    # two completed, one failed
    s.append_event(seat, "session_completed", payload={"cost_usd": 0.10, "latency_ms": 1000})
    s.append_event(seat, "session_completed", payload={"cost_usd": 0.20, "latency_ms": 3000})
    s.append_event(seat, "session_failed", payload={"cost_usd": 0.05, "latency_ms": 500})
    s.append_event(seat, "gate_passed")
    s.append_event(seat, "gate_failed")
    tr = s.get_track_record(seat)
    assert tr["runs"] == 3
    assert abs(tr["success_rate"] - (2/3)) < 1e-6
    assert abs(tr["gate_pass_rate"] - 0.5) < 1e-6
    assert len(tr["recent_wins"]) == 2


@pytest.mark.skipif(not HAS_PG, reason="DATABASE_URL not set")
def test_rename_keeps_id_and_history():
    import uuid
    from agentura_sdk.memory.seat_store import SeatStore
    s = SeatStore()
    old = f"dev/rn-{uuid.uuid4().hex[:8]}"
    new = f"dev/rn2-{uuid.uuid4().hex[:8]}"
    seat = s.get_or_create_seat(name=old, role="rn", domain="dev")
    s.rename_seat(seat, new)
    row = s.get_seat(seat)
    assert row["name"] == new
    assert row["renamed_from"] == old


def test_fleet_schema_has_seat_id():
    from agentura_sdk.memory.fleet_store import FLEET_SCHEMA
    assert "seat_id" in FLEET_SCHEMA


def test_record_outcome_appends_events():
    from agentura_sdk.runner.seat_hooks import record_outcome
    calls = []
    class Fake:
        def append_event(self, seat_id, type, session_id=None, model="", payload=None):
            calls.append((type, payload))
    record_outcome(Fake(), "seat1", "sess1", True, cost_usd=0.1, latency_ms=900, gate="pass")
    types = [c[0] for c in calls]
    assert "session_completed" in types and "gate_passed" in types


def test_record_outcome_never_raises():
    from agentura_sdk.runner.seat_hooks import record_outcome
    class Boom:
        def append_event(self, *a, **k):
            raise RuntimeError("db down")
    record_outcome(Boom(), "seat1", "sess1", False)  # must not raise
    record_outcome(None, None, "sess1", True)         # must not raise


@pytest.mark.skipif(not HAS_PG, reason="DATABASE_URL not set")
def test_identity_persists_across_sessions():
    import uuid
    from agentura_sdk.memory.seat_store import SeatStore
    from agentura_sdk.runner.seat_resolver import resolve_seat
    from agentura_sdk.runner.seat_hooks import record_outcome
    s = SeatStore()
    skill = f"dev/persist-{uuid.uuid4().hex[:8]}"
    a = resolve_seat(s, skill)
    record_outcome(s, a, "sess-1", True, cost_usd=0.1, latency_ms=500)
    b = resolve_seat(s, skill)          # second run resolves the SAME seat
    record_outcome(s, b, "sess-2", True, cost_usd=0.2, latency_ms=700)
    assert a == b                        # identity persists across sessions
    assert s.get_track_record(a)["runs"] == 2   # runs 1 -> 2


def test_record_rating_appends_event():
    from agentura_sdk.runner.seat_hooks import record_rating
    calls = []
    class Fake:
        def get_or_create_seat(self, **k): return "seat1"
        def append_event(self, seat_id, type, session_id=None, model="", payload=None):
            calls.append((type, payload))
    record_rating(Fake(), "dev/x", 4, task_id="t1", model="glm-5")
    assert calls and calls[0][0] == "rating" and calls[0][1]["rating"] == 4


def test_record_rating_never_raises():
    from agentura_sdk.runner.seat_hooks import record_rating
    class Boom:
        def get_or_create_seat(self, **k): raise RuntimeError("down")
    record_rating(Boom(), "dev/x", 3)   # must not raise
    record_rating(None, "dev/x", 3)     # must not raise


@pytest.mark.skipif(not HAS_PG, reason="DATABASE_URL not set")
def test_track_record_endpoint_and_avg_rating():
    import uuid
    from fastapi.testclient import TestClient
    from agentura_sdk.server.app import app
    from agentura_sdk.memory.seat_store import get_seat_store
    from agentura_sdk.runner.seat_hooks import record_rating
    c = TestClient(app)
    skill = f"dev/ep-{uuid.uuid4().hex[:8]}"
    assert c.get("/api/v1/seat-track-record", params={"skill": skill}).status_code == 404
    record_rating(get_seat_store(), skill, 4)
    r = c.get("/api/v1/seat-track-record", params={"skill": skill})
    assert r.status_code == 200
    assert r.json()["track_record"]["avg_rating"] == 4.0
