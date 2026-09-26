"""叠算聚合: validate floor groups and aggregate floor subtotals into a total."""


def validate_floor_groups(floors):
    """Check a floor grouping before any calculation or persistence.

    floors: iterable of (floor_label, wall_ids) pairs.
    Returns an error message string, or None when the grouping is valid.
    Rules: at least one floor; every floor lists at least one wall;
    a wall id may not repeat, within one floor or across floors.
    """
    floors = list(floors)
    if not floors:
        return "floors must not be empty"
    seen = set()
    for label, wall_ids in floors:
        wall_ids = list(wall_ids)
        if not wall_ids:
            return f"floor {label!r} has an empty wall list"
        for wid in wall_ids:
            if wid in seen:
                return f"duplicate wall id across floors: {wid}"
            seen.add(wid)
    return None


def aggregate_floors(floor_rolls):
    """Sum each floor's subtotal rolls into the stack grand total.

    A single-floor stack therefore totals exactly that floor's subtotal.
    """
    floor_rolls = list(floor_rolls)
    if not floor_rolls:
        raise ValueError("stack must contain at least one floor")
    return sum(int(r) for r in floor_rolls)
