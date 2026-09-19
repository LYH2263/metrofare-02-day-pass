import json

import pytest

from app import seed
from app.modules.day_pass import apply_day_pass, validate_cap
from app.services.metro_service import MetroService


@pytest.fixture()
def svc(tmp_path, monkeypatch):
    monkeypatch.setattr("app.db.DB_PATH", tmp_path / "test.db")
    seed.init_db()
    with MetroService() as s:
        yield s


def set_pass(svc, cap, enabled=True, day="2026-09-19"):
    return svc.update_day_pass(day, cap, enabled)


def test_validate_cap_rejects_non_positive():
    with pytest.raises(ValueError):
        validate_cap(0)
    with pytest.raises(ValueError):
        validate_cap(-3)
    assert validate_cap(3.5) == 3.5


def test_apply_caps_when_enabled_and_requested():
    cfg = {"day": "2026-09-19", "cap": 3.5, "enabled": True}
    r = apply_day_pass(4.0, cfg, True)
    assert r["payable"] == 3.5
    assert r["original_fare"] == 4.0
    assert r["capped"] is True


def test_apply_untouched_when_not_requested_or_disabled():
    cfg = {"day": "2026-09-19", "cap": 3.5, "enabled": True}
    r = apply_day_pass(4.0, cfg, False)
    assert r["payable"] == 4.0 and r["capped"] is False and r["applied"] is False
    r = apply_day_pass(4.0, {**cfg, "enabled": False}, True)
    assert r["payable"] == 4.0 and r["applied"] is False


def test_apply_no_accumulation_within_day():
    cfg = {"day": "2026-09-19", "cap": 5.0, "enabled": True}
    first = apply_day_pass(4.0, cfg, True)
    second = apply_day_pass(4.0, cfg, True)
    assert first["payable"] == 4.0 and second["payable"] == 4.0
    assert second["capped"] is False


def test_quote_with_day_pass(svc):
    set_pass(svc, 3.5)
    q = svc.quote("A1", "B2", True, use_day_pass=True)  # segment fare 4.0
    assert q["fare"] == 3.5
    assert q["original_fare"] == 4.0
    assert q["hops"] == 3
    assert q["day_pass"]["capped"] is True
    assert q["day_pass"]["cap"] == 3.5
    assert q["run_id"] is not None


def test_quote_without_day_pass_matches_legacy(svc):
    set_pass(svc, 3.5)
    q = svc.quote("A1", "B2", True, use_day_pass=False)
    assert q["fare"] == 4.0 and q["original_fare"] == 4.0
    assert q["day_pass"]["applied"] is False and q["day_pass"]["capped"] is False


def test_readonly_trial_not_persisted(svc):
    set_pass(svc, 3.5)
    before = len(svc.history())
    q = svc.quote("A1", "B2", False, use_day_pass=True)
    assert q["run_id"] is None
    assert q["fare"] == 3.5
    assert len(svc.history()) == before


def test_records_keep_snapshot_after_cap_change(svc):
    set_pass(svc, 3.5)
    svc.quote("A1", "B2", True, use_day_pass=True)  # capped at 3.5
    set_pass(svc, 5.0)  # raise the cap afterwards
    q2 = svc.quote("A1", "B2", True, use_day_pass=True)
    assert q2["fare"] == 4.0 and q2["day_pass"]["capped"] is False
    snaps = [json.loads(i["result_json"]) for i in svc.history()]
    old = next(r for r in snaps if r.get("day_pass", {}).get("capped"))
    assert old["fare"] == 3.5
    assert old["original_fare"] == 4.0
    assert old["day_pass"]["cap"] == 3.5


def test_two_quotes_same_day_no_accumulation(svc):
    set_pass(svc, 5.0)
    svc.quote("A1", "B2", True, use_day_pass=True)  # 4.0, under the cap
    q2 = svc.quote("A1", "B2", True, use_day_pass=True)
    # second quote compares only its own 4.0 against the 5.0 cap
    assert q2["fare"] == 4.0 and q2["day_pass"]["capped"] is False


def test_day_pass_roundtrip(svc):
    assert svc.day_pass()["enabled"] is False
    cfg = set_pass(svc, 12.5, enabled=True, day="2026-09-20")
    assert cfg == {"day": "2026-09-20", "cap": 12.5, "enabled": True}
    assert svc.day_pass() == cfg
