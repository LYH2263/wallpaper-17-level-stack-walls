"""单层合并: merge one floor's per-wall roll counts into a floor subtotal."""


def merge_floor(wall_calcs):
    """Sum the rolls/drops of every wall in a single floor.

    wall_calcs: iterable of dicts with at least "rolls" and "drops" keys,
    as produced per wall by engines.wallpaper_math.roll_count.
    Returns {"rolls": int, "drops": int} for the floor.
    """
    wall_calcs = list(wall_calcs)
    if not wall_calcs:
        raise ValueError("floor must contain at least one wall")
    return {
        "rolls": sum(int(c["rolls"]) for c in wall_calcs),
        "drops": sum(int(c["drops"]) for c in wall_calcs),
    }
