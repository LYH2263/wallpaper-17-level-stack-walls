from fastapi import HTTPException

from app.engines.wallpaper_math import roll_count
from app.modules.floor_merge import merge_floor
from app.modules.stack_aggregate import aggregate_floors, validate_floor_groups
from app.repositories import history, rolls, walls


def run_floor_stack(roll_id: int, floors, save: bool, note: str = ""):
    """楼层叠算: per floor merge wall rolls on one roll, then aggregate floors.

    Persists at most one calc_runs row whose result_json is a self-contained
    snapshot; later wall edits never recompute a saved stack.
    """
    groups = [(f.floor, f.wall_ids) for f in floors]
    error = validate_floor_groups(groups)
    if error:
        raise HTTPException(422, error)

    roll = rolls.get_roll(roll_id)
    if not roll:
        raise HTTPException(404, "roll not found")
    if roll.get("data_quality") == "dirty":
        raise HTTPException(422, "dirty seed entity")

    floor_results = []
    for label, wall_ids in groups:
        wall_entries = []
        for wid in wall_ids:
            wall = walls.get_wall(wid)
            if not wall:
                raise HTTPException(404, f"wall not found: {wid}")
            if wall.get("data_quality") == "dirty":
                raise HTTPException(422, "dirty seed entity")
            calc = roll_count(
                wall["perimeter"], wall["height"], roll["width"], roll["length"], roll["pattern_cm"]
            )
            wall_entries.append({
                "wall_id": wid,
                "name": wall["name"],
                "perimeter": wall["perimeter"],
                "height": wall["height"],
                "drops": calc["drops"],
                "rolls": calc["rolls"],
            })
        subtotal = merge_floor(wall_entries)
        floor_results.append({
            "floor": label,
            "walls": wall_entries,
            "subtotal_rolls": subtotal["rolls"],
            "subtotal_drops": subtotal["drops"],
        })

    total_rolls = aggregate_floors([f["subtotal_rolls"] for f in floor_results])

    run_id = None
    if save:
        snapshot = {
            "kind": "floor_stack",
            "roll_id": roll_id,
            "roll_name": roll["name"],
            "floors": floor_results,
            "total_rolls": total_rolls,
        }
        run_id = history.insert_run(None, roll_id, snapshot, note)
    return {"roll": roll, "floors": floor_results, "total_rolls": total_rolls, "run_id": run_id}
