import os
import tempfile

os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="wallpaper-test-"))

import pytest
from fastapi import HTTPException

from app import seed
from app.db import connect
from app.engines.wallpaper_math import roll_count
from app.modules import floor_merge, floor_stack
from app.repositories import history, walls as walls_repo
from app.services import estimate_service

seed.init_db()

ROLL_ID = 1  # 素色53 0.53m x 10m, no pattern


def _run_count() -> int:
    conn = connect()
    try:
        return conn.execute("SELECT COUNT(*) c FROM calc_runs").fetchone()["c"]
    finally:
        conn.close()


def _roll():
    return {"id": ROLL_ID, "name": "素色53", "width": 0.53, "length": 10.0, "pattern_cm": 0}


def test_merge_floor_sums_wall_rolls():
    ws = [
        {"id": 1, "name": "a", "perimeter": 16.0, "height": 2.7},
        {"id": 2, "name": "b", "perimeter": 20.0, "height": 2.8},
    ]
    res = floor_merge.merge_floor(ws, _roll(), "1F")
    expected = roll_count(16.0, 2.7, 0.53, 10.0, 0)["rolls"] + roll_count(20.0, 2.8, 0.53, 10.0, 0)["rolls"]
    assert res["floor"] == "1F"
    assert res["wall_ids"] == [1, 2]
    assert [w["rolls"] for w in res["walls"]] == [
        roll_count(16.0, 2.7, 0.53, 10.0, 0)["rolls"],
        roll_count(20.0, 2.8, 0.53, 10.0, 0)["rolls"],
    ]
    assert res["rolls"] == expected


def test_stack_floors_aggregates_floor_totals():
    f1 = {"floor": "1F", "wall_ids": [1], "walls": [], "rolls": 11}
    f2 = {"floor": "2F", "wall_ids": [2], "walls": [], "rolls": 13}
    stacked = floor_stack.stack_floors([f1, f2])
    assert stacked["total_rolls"] == 24
    assert stacked["floors"] == [f1, f2]


def test_validate_floors_rejects_empty_list():
    with pytest.raises(ValueError):
        floor_stack.validate_floors([])


def test_validate_floors_rejects_empty_floor():
    with pytest.raises(ValueError):
        floor_stack.validate_floors([{"floor": "1F", "wall_ids": []}])


def test_validate_floors_rejects_cross_floor_duplicates():
    with pytest.raises(ValueError):
        floor_stack.validate_floors(
            [{"floor": "1F", "wall_ids": [1, 2]}, {"floor": "2F", "wall_ids": [2, 3]}]
        )


def test_validate_floors_rejects_within_floor_duplicates():
    with pytest.raises(ValueError):
        floor_stack.validate_floors([{"floor": "1F", "wall_ids": [1, 1]}])


def test_single_floor_total_equals_floor_sum():
    res = estimate_service.run_floor_estimate(
        ROLL_ID, [{"floor": "1F", "wall_ids": [1, 2]}], False, ""
    )
    expected = roll_count(16.0, 2.7, 0.53, 10.0, 0)["rolls"] + roll_count(20.0, 2.8, 0.53, 10.0, 0)["rolls"]
    assert len(res["floors"]) == 1
    assert res["floors"][0]["rolls"] == expected
    assert res["total_rolls"] == expected
    assert res["run_id"] is None


def test_multi_floor_total_is_sum_of_floor_totals():
    res = estimate_service.run_floor_estimate(
        ROLL_ID,
        [{"floor": "1F", "wall_ids": [1]}, {"floor": "2F", "wall_ids": [2]}],
        False,
        "",
    )
    assert [f["rolls"] for f in res["floors"]] == [11, 13]
    assert res["total_rolls"] == 24


def test_empty_floor_fails_and_inserts_no_row():
    before = _run_count()
    with pytest.raises(HTTPException) as exc:
        estimate_service.run_floor_estimate(ROLL_ID, [{"floor": "1F", "wall_ids": []}], True, "")
    assert exc.value.status_code == 422
    assert _run_count() == before


def test_empty_floor_list_fails_and_inserts_no_row():
    before = _run_count()
    with pytest.raises(HTTPException) as exc:
        estimate_service.run_floor_estimate(ROLL_ID, [], True, "")
    assert exc.value.status_code == 422
    assert _run_count() == before


def test_duplicate_wall_across_floors_fails_and_inserts_no_row():
    before = _run_count()
    with pytest.raises(HTTPException) as exc:
        estimate_service.run_floor_estimate(
            ROLL_ID,
            [{"floor": "1F", "wall_ids": [1]}, {"floor": "2F", "wall_ids": [1]}],
            True,
            "",
        )
    assert exc.value.status_code == 422
    assert _run_count() == before


def test_save_persists_single_row_with_breakdown_and_total():
    before = _run_count()
    res = estimate_service.run_floor_estimate(
        ROLL_ID,
        [{"floor": "1F", "wall_ids": [1]}, {"floor": "2F", "wall_ids": [2]}],
        True,
        "叠算",
    )
    assert res["run_id"]
    assert _run_count() == before + 1
    row = history.get_run(res["run_id"])
    assert row["note"] == "叠算"
    assert row["result"]["kind"] == "floor_stack"
    assert [f["floor"] for f in row["result"]["floors"]] == ["1F", "2F"]
    assert row["result"]["floors"][0]["walls"][0]["wall_id"] == 1
    assert row["result"]["total_rolls"] == 24


def test_saved_breakdown_not_recomputed_after_wall_perimeter_change():
    res = estimate_service.run_floor_estimate(
        ROLL_ID, [{"floor": "1F", "wall_ids": [1, 2]}], True, ""
    )
    saved = history.get_run(res["run_id"])
    wall1_rolls = saved["result"]["floors"][0]["walls"][0]["rolls"]
    total = saved["result"]["total_rolls"]
    try:
        walls_repo.update_wall(1, {"perimeter": 99.0})
        again = history.get_run(res["run_id"])
        assert again["result"]["floors"][0]["walls"][0]["rolls"] == wall1_rolls
        assert again["result"]["total_rolls"] == total
    finally:
        walls_repo.update_wall(1, {"perimeter": 16.0})


def test_dirty_wall_fails():
    with pytest.raises(HTTPException) as exc:
        estimate_service.run_floor_estimate(ROLL_ID, [{"floor": "1F", "wall_ids": [3]}], False, "")
    assert exc.value.status_code == 422


def test_unknown_wall_fails():
    with pytest.raises(HTTPException) as exc:
        estimate_service.run_floor_estimate(ROLL_ID, [{"floor": "1F", "wall_ids": [999]}], False, "")
    assert exc.value.status_code == 404


def test_unknown_roll_fails():
    with pytest.raises(HTTPException) as exc:
        estimate_service.run_floor_estimate(999, [{"floor": "1F", "wall_ids": [1]}], False, "")
    assert exc.value.status_code == 404
