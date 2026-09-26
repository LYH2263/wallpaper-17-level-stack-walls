"""单层合并：同一楼层内多面墙按同卷材合计卷数。"""

from app.engines.wallpaper_math import roll_count


def merge_floor(walls: list[dict], roll: dict, floor: str = "") -> dict:
    """Merge one floor's walls (all sharing the same roll) into per-wall
    calcs plus a floor subtotal of rolls."""
    items = []
    total = 0
    for w in walls:
        calc = roll_count(w["perimeter"], w["height"], roll["width"], roll["length"], roll["pattern_cm"])
        items.append({"wall_id": w["id"], "name": w["name"], **calc})
        total += calc["rolls"]
    return {
        "floor": floor,
        "wall_ids": [w["id"] for w in walls],
        "walls": items,
        "rolls": total,
    }
