"""叠算聚合：楼层分组校验与跨层总卷数聚合。"""


def validate_floors(floors: list[dict]) -> None:
    """Reject an empty floor list, any floor with an empty wall list, and
    wall ids repeated across (or within) floors."""
    if not floors:
        raise ValueError("floors must not be empty")
    seen = set()
    for f in floors:
        wall_ids = list(f.get("wall_ids") or [])
        if not wall_ids:
            raise ValueError("floor wall list must not be empty")
        for wid in wall_ids:
            if wid in seen:
                raise ValueError(f"duplicate wall id across floors: {wid}")
            seen.add(wid)


def stack_floors(floor_results: list[dict]) -> dict:
    """Aggregate merged floor subtotals into the grand total."""
    floors = list(floor_results)
    return {"floors": floors, "total_rolls": sum(f["rolls"] for f in floors)}
