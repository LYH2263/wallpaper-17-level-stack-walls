from app.db import connect


def list_walls():
    conn = connect()
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM walls ORDER BY id").fetchall()]
    finally:
        conn.close()


def get_wall(wid: int):
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM walls WHERE id=?", (wid,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_wall(wid: int, fields: dict):
    allowed = {k: v for k, v in fields.items() if k in ("name", "perimeter", "height", "note")}
    if not allowed:
        return
    cols = ", ".join(f"{k}=?" for k in allowed)
    conn = connect()
    try:
        conn.execute(f"UPDATE walls SET {cols} WHERE id=?", (*allowed.values(), wid))
        conn.commit()
    finally:
        conn.close()
