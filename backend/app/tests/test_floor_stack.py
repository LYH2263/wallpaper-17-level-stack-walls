import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app import seed
from app.db import connect
from app.modules.floor_merge import merge_floor
from app.modules.stack_aggregate import aggregate_floors, validate_floor_groups
from app.repositories import history
from app.schemas.estimate import FloorGroup, FloorStackRequest
from app.services import stack_service


@pytest.fixture()
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setattr("app.db.DB_PATH", tmp_path / "test.db")
    seed.init_db()
    yield


def fg(floor, ids):
    return FloorGroup(floor=floor, wall_ids=ids)


def count_runs():
    conn = connect()
    try:
        return conn.execute("SELECT COUNT(*) c FROM calc_runs").fetchone()["c"]
    finally:
        conn.close()


def test_merge_floor_sums_rolls_and_drops():
    sub = merge_floor([{"rolls": 11, "drops": 31}, {"rolls": 13, "drops": 38}])
    assert sub == {"rolls": 24, "drops": 69}


def test_merge_floor_rejects_empty():
    with pytest.raises(ValueError):
        merge_floor([])


def test_aggregate_floors_single_floor_equals_its_subtotal():
    assert aggregate_floors([24]) == 24


def test_aggregate_floors_sums_subtotals():
    assert aggregate_floors([11, 13]) == 24


def test_validate_floor_groups_rules():
    assert validate_floor_groups([]) is not None
    assert validate_floor_groups([("1F", [])]) is not None
    assert validate_floor_groups([("1F", [1]), ("2F", [1])]) is not None
    assert validate_floor_groups([("1F", [1, 1])]) is not None
    assert validate_floor_groups([("1F", [1, 2]), ("2F", [3])]) is None


def test_schema_rejects_empty_floor_and_empty_stack():
    with pytest.raises(ValidationError):
        fg("1F", [])
    with pytest.raises(ValidationError):
        FloorStackRequest(roll_id=1, floors=[])


def test_single_floor_total_equals_floor_sum(fresh_db):
    res = stack_service.run_floor_stack(1, [fg("1F", [1, 2])], False)
    assert res["floors"][0]["subtotal_rolls"] == 11 + 13
    assert res["total_rolls"] == res["floors"][0]["subtotal_rolls"]
    assert res["run_id"] is None


def test_multi_floor_aggregates_subtotals(fresh_db):
    res = stack_service.run_floor_stack(1, [fg("1F", [1]), fg("2F", [2])], False)
    assert [f["subtotal_rolls"] for f in res["floors"]] == [11, 13]
    assert res["total_rolls"] == 24


def test_empty_floor_list_fails_without_row(fresh_db):
    empty = FloorGroup.model_construct(floor="1F", wall_ids=[])
    with pytest.raises(HTTPException) as exc:
        stack_service.run_floor_stack(1, [empty], True)
    assert exc.value.status_code == 422
    with pytest.raises(HTTPException) as exc:
        stack_service.run_floor_stack(1, [], True)
    assert exc.value.status_code == 422
    assert count_runs() == 0


def test_duplicate_wall_across_floors_fails_without_row(fresh_db):
    with pytest.raises(HTTPException) as exc:
        stack_service.run_floor_stack(1, [fg("1F", [1]), fg("2F", [1, 2])], True)
    assert exc.value.status_code == 422
    assert count_runs() == 0


def test_missing_or_dirty_entities_fail(fresh_db):
    with pytest.raises(HTTPException) as exc:
        stack_service.run_floor_stack(1, [fg("1F", [999])], True)
    assert exc.value.status_code == 404
    with pytest.raises(HTTPException) as exc:
        stack_service.run_floor_stack(1, [fg("1F", [3])], True)
    assert exc.value.status_code == 422
    with pytest.raises(HTTPException) as exc:
        stack_service.run_floor_stack(3, [fg("1F", [1])], True)
    assert exc.value.status_code == 422
    assert count_runs() == 0


def test_save_inserts_one_row_and_snapshot_survives_wall_edit(fresh_db):
    res = stack_service.run_floor_stack(1, [fg("1F", [1]), fg("2F", [2])], True, "叠算")
    assert res["run_id"]
    assert count_runs() == 1

    saved = history.get_run(res["run_id"])
    assert saved["result"]["kind"] == "floor_stack"
    assert saved["result"]["total_rolls"] == 24
    assert [f["floor"] for f in saved["result"]["floors"]] == ["1F", "2F"]
    assert saved["result"]["floors"][0]["walls"][0]["perimeter"] == 16.0

    conn = connect()
    try:
        conn.execute("UPDATE walls SET perimeter=99.0 WHERE id=1")
        conn.commit()
    finally:
        conn.close()

    again = history.get_run(res["run_id"])
    assert again["result"]["total_rolls"] == 24
    assert again["result"]["floors"][0]["walls"][0]["perimeter"] == 16.0
    assert again["result"]["floors"][0]["subtotal_rolls"] == 11
