from app.db import connect
from app.engines.route_quote import quote_route
from app.modules.day_pass import apply_day_pass, validate_cap
from app.repositories import day_pass as day_pass_repo
from app.repositories import edges as edges_repo
from app.repositories import fare_rules as rules_repo
from app.repositories import runs as runs_repo
from app.repositories import settings as settings_repo
from app.repositories import stations as stations_repo


class MetroService:
    def __init__(self):
        self._conn = connect()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def stations(self):
        return stations_repo.list_all(self._conn)

    def station(self, code: str):
        return stations_repo.get_by_code(self._conn, code)

    def edges(self):
        return [{"a": a, "b": b} for a, b in edges_repo.list_pairs(self._conn)]

    def fare_rules(self):
        return rules_repo.list_ordered(self._conn)

    def settings(self):
        return settings_repo.get_map(self._conn)

    def day_pass(self):
        return day_pass_repo.get(self._conn) or {"day": None, "cap": None, "enabled": False}

    def update_day_pass(self, day: str, cap: float, enabled: bool):
        return day_pass_repo.upsert(self._conn, day, validate_cap(cap), enabled)

    def quote(self, start: str, end: str, persist: bool, use_day_pass: bool = False):
        edges = edges_repo.list_pairs(self._conn)
        rules = rules_repo.as_calc_rules(self._conn)
        result = quote_route(edges, start, end, rules)
        if result.get("reachable"):
            dp = apply_day_pass(result["fare"], day_pass_repo.get(self._conn), use_day_pass)
            result["fare"] = dp["payable"]
            result["original_fare"] = dp["original_fare"]
            result["day_pass"] = {k: dp[k] for k in ("requested", "enabled", "applied", "day", "cap", "capped")}
        run_id = None
        if persist and result.get("reachable"):
            run_id = runs_repo.insert(
                self._conn,
                "quote",
                {"start": start, "end": end, "use_day_pass": use_day_pass},
                result,
            )
        return {"run_id": run_id, **result}

    def history(self, limit=50):
        return runs_repo.list_recent(self._conn, limit)

    def dashboard(self):
        st = stations_repo.list_all(self._conn)
        clean = [s for s in st if "种子" not in s["name"]]
        dirty = [s for s in st if "种子" in s["name"]]
        return {
            "station_count": len(st),
            "edge_count": len(edges_repo.list_pairs(self._conn)),
            "clean_stations": len(clean),
            "dirty_stations": len(dirty),
        }
