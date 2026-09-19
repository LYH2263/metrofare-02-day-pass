import sqlite3

CONFIG_ID = 1


def get(conn: sqlite3.Connection) -> dict | None:
    row = conn.execute(
        "SELECT id, day, cap, enabled FROM day_pass_config WHERE id = ?", (CONFIG_ID,)
    ).fetchone()
    if row is None:
        return None
    return {"day": row["day"], "cap": row["cap"], "enabled": bool(row["enabled"])}


def upsert(conn: sqlite3.Connection, day: str, cap: float, enabled: bool) -> dict:
    conn.execute(
        """
        INSERT INTO day_pass_config(id, day, cap, enabled) VALUES (?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET day=excluded.day, cap=excluded.cap, enabled=excluded.enabled
        """,
        (CONFIG_ID, day, cap, int(enabled)),
    )
    conn.commit()
    return get(conn)
