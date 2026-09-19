"""一日通 (day pass): daily fare cap.

Config is one persisted row: natural day (YYYY-MM-DD), cap amount (must be
positive), and an enabled flag. When a quote opts in and the pass is enabled,
the payable fare is min(segment fare, cap).

The cap comparison is stateless per quote: it only ever looks at the current
quote's own segment fare, never at earlier quotes of the same day.
"""


def validate_cap(cap) -> float:
    """Cap must be a positive number; returns it rounded to cents."""
    value = round(float(cap), 2)
    if value <= 0:
        raise ValueError("day pass cap must be positive")
    return value


def apply_day_pass(fare: float, config: dict | None, use_day_pass: bool) -> dict:
    """Fold the day-pass cap into a segment fare.

    Returns the original fare, the cap in effect, whether the cap bit (触顶),
    and the resulting payable fare.
    """
    original = round(float(fare), 2)
    enabled = bool(config and config.get("enabled"))
    applied = bool(use_day_pass and enabled)
    cap = round(float(config["cap"]), 2) if config and config.get("cap") is not None else None
    capped = bool(applied and cap is not None and original > cap)
    payable = cap if capped else original
    return {
        "requested": bool(use_day_pass),
        "enabled": enabled,
        "applied": applied,
        "day": config.get("day") if config else None,
        "cap": cap,
        "capped": capped,
        "original_fare": original,
        "payable": payable,
    }
