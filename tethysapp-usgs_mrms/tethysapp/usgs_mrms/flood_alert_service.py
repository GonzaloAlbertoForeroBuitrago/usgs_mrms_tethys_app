from __future__ import annotations

from pathlib import Path

from .flood_alert_s3 import download_flood_alert_inputs
from .flood_alert_utils import build_run_directory, build_run_id

from mrms_usgs_events.ews.state_rain import build_current_state_rain_npz
from mrms_usgs_events.ews.current_alerts import compute_current_alerts_for_state
from mrms_usgs_events.ews.tethys_outputs import export_state_alerts_for_tethys


def run_flood_alert_pipeline(
    *,
    base_dir: Path,
    state: str,
    start: str,
    end: str,
    workers: int = 4,
) -> dict:
    state = state.upper()
    base_dir = Path(base_dir)

    run_id = build_run_id(start, end)
    run_dir = build_run_directory(base_dir, state, start, end)

    print("=" * 100, flush=True)
    print("TETHYS FLOOD ALERT PIPELINE", flush=True)
    print("=" * 100, flush=True)
    print(f"state   : {state}", flush=True)
    print(f"start   : {start}", flush=True)
    print(f"end     : {end}", flush=True)
    print(f"workers : {workers}", flush=True)
    print(f"base_dir: {base_dir}", flush=True)
    print(f"run_id  : {run_id}", flush=True)
    print(f"run_dir : {run_dir}", flush=True)

    inputs = download_flood_alert_inputs(
        base_dir=base_dir,
        state=state,
        workers=workers,
    )

    current_rain_npz = base_dir / "current_rain" / f"{state}_{run_id}_current_rain.npz"

    build_current_state_rain_npz(
        state=state,
        state_mask_fp=inputs["state_mask_fp"],
        out_npz=current_rain_npz,
        base_dir=base_dir,
        start=start,
        end=end,
        workers=workers,
    )

    alerts_result = compute_current_alerts_for_state(
        state=state,
        current_rain_npz=current_rain_npz,
        state_basin_index_npz=inputs["state_basin_index_fp"],
        pixel_event_index_npz=inputs["pixel_event_index_fp"],
        out_dir=base_dir / "ews_alerts",
        max_pixels_per_basin_output=100,
    )

    export_result = export_state_alerts_for_tethys(
        state=state,
        base_dir=base_dir,
        alerts_dir=base_dir / "ews_alerts" / state,
        out_dir=run_dir,
        max_pixels=100_000,
        pixel_size_deg=0.01,
    )

    return {
        "state": state,
        "start": start,
        "end": end,
        "workers": workers,
        "base_dir": str(base_dir),
        "run_id": run_id,
        "run_dir": str(run_dir),
        "current_rain_npz": str(current_rain_npz),
        "inputs": {k: str(v) for k, v in inputs.items()},
        "alerts": {k: str(v) for k, v in alerts_result.items()},
        "exports": {k: str(v) for k, v in export_result.items()},
    }