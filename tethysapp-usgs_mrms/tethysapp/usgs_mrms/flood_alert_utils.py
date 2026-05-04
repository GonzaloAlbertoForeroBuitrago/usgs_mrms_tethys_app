from __future__ import annotations

from datetime import datetime
from pathlib import Path


def build_run_id(start_dt: str, end_dt: str) -> str:
    """
    Build a stable run identifier from start/end datetimes.
    """
    start_fmt = datetime.fromisoformat(start_dt).strftime("%Y%m%d_%H%M%S")
    end_fmt = datetime.fromisoformat(end_dt).strftime("%Y%m%d_%H%M%S")

    return f"{start_fmt}_{end_fmt}"


def build_run_directory(
    base_dir: Path,
    state: str,
    start_dt: str,
    end_dt: str,
) -> Path:
    """
    Build the output directory for a Flood Alert run.
    """
    run_id = build_run_id(start_dt, end_dt)

    run_dir = (
        Path(base_dir)
        / "flood_alert_runs"
        / state.upper()
        / run_id
    )

    run_dir.mkdir(parents=True, exist_ok=True)

    return run_dir