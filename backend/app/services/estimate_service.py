from fastapi import HTTPException

from app.engines.wallpaper_math import roll_count
from app.modules import floor_merge, floor_stack
from app.repositories import history, rolls, walls


def run_estimate(wall_id: int, roll_id: int, save: bool, note: str):
    wall = walls.get_wall(wall_id)
    if not wall:
        raise HTTPException(404, "wall not found")
    roll = rolls.get_roll(roll_id)
    if not roll:
        raise HTTPException(404, "roll not found")
    if wall.get("data_quality") == "dirty" or roll.get("data_quality") == "dirty":
        raise HTTPException(422, "dirty seed entity")

    calc = roll_count(
        wall["perimeter"], wall["height"], roll["width"], roll["length"], roll["pattern_cm"]
    )
    run_id = None
    if save:
        run_id = history.insert_run(wall_id, roll_id, {**calc, "wall_id": wall_id, "roll_id": roll_id}, note)
    return {"wall": wall, "roll": roll, "run_id": run_id, **calc}


def run_floor_estimate(roll_id: int, floors: list[dict], save: bool, note: str):
    roll = rolls.get_roll(roll_id)
    if not roll:
        raise HTTPException(404, "roll not found")
    if roll.get("data_quality") == "dirty":
        raise HTTPException(422, "dirty seed entity")
    try:
        floor_stack.validate_floors(floors)
    except ValueError as exc:
        raise HTTPException(422, str(exc))

    merged = []
    for f in floors:
        floor_walls = []
        for wid in f["wall_ids"]:
            wall = walls.get_wall(wid)
            if not wall:
                raise HTTPException(404, f"wall {wid} not found")
            if wall.get("data_quality") == "dirty":
                raise HTTPException(422, "dirty seed entity")
            floor_walls.append(wall)
        merged.append(floor_merge.merge_floor(floor_walls, roll, f.get("floor", "")))
    stacked = floor_stack.stack_floors(merged)

    run_id = None
    if save:
        run_id = history.insert_run(None, roll_id, {"kind": "floor_stack", **stacked}, note)
    return {"roll": roll, "run_id": run_id, **stacked}
