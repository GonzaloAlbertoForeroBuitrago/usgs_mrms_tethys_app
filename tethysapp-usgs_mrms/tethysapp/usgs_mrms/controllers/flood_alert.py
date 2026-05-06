from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from django.http import JsonResponse
from tethys_sdk.routing import controller

from ..app import App
from ..flood_alert_service import run_flood_alert_pipeline
from ..flood_alert_utils import build_run_id


STATES = [
    "TEXAS",
    "UTAH",
    "IOWA",
    "OKLAHOMA",
    "LOUISIANA",
    "ARKANSAS",
    "COLORADO",
]


ALERT_COLORS = {
    "NORMAL": "#3BA55D",
    "WATCH": "#F1C40F",
    "WARNING": "#E67E22",
    "SEVERE": "#E74C3C",
}


def _normalize_datetime_from_form(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return value
    if "T" in value:
        value = value.replace("T", " ")
    if len(value) == 16:
        value = value + ":00"
    return value


def _json_safe(v):
    if pd.isna(v):
        return None
    if hasattr(v, "item"):
        return v.item()
    return v


def _geometry_bbox_area(geometry: dict | None) -> float:
    if not geometry:
        return 0.0

    coords = geometry.get("coordinates")
    if not coords:
        return 0.0

    xs = []
    ys = []

    def collect(obj):
        if isinstance(obj, list):
            if len(obj) >= 2 and all(isinstance(x, (int, float)) for x in obj[:2]):
                xs.append(float(obj[0]))
                ys.append(float(obj[1]))
            else:
                for item in obj:
                    collect(item)

    collect(coords)

    if not xs or not ys:
        return 0.0

    return (max(xs) - min(xs)) * (max(ys) - min(ys))


def _pixel_polygon_from_center(lon: float, lat: float, dx: float = 0.01, dy: float = 0.01) -> dict:
    half_dx = dx / 2.0
    half_dy = dy / 2.0
    x0 = lon - half_dx
    x1 = lon + half_dx
    y0 = lat - half_dy
    y1 = lat + half_dy

    return {
        "type": "Polygon",
        "coordinates": [[
            [x0, y0],
            [x1, y0],
            [x1, y1],
            [x0, y1],
            [x0, y0],
        ]],
    }


@controller(name="flood_alert", url="flood-alert/", app_media=True)
def flood_alert(request, app_media):
    return App.render(request, "flood_alert.html", {"states": STATES})


@controller(name="run_flood_alert", url="flood-alert/run/", app_media=True)
def run_flood_alert(request, app_media):
    if request.method != "POST":
        return App.render(request, "flood_alert.html", {"states": STATES})

    state = request.POST.get("state", "").upper().strip()
    start_dt = _normalize_datetime_from_form(request.POST.get("start_datetime", ""))
    end_dt = _normalize_datetime_from_form(request.POST.get("end_datetime", ""))
    workers = int(request.POST.get("workers", "4"))

    base_dir = Path(app_media.path)
    run_id = build_run_id(start_dt, end_dt)
    run_dir = base_dir / "flood_alert_runs" / state / run_id

    lock_fp = run_dir / ".running.lock"
    done_fp = run_dir / ".done"

    if lock_fp.exists():
        context = {
            "status": "error",
            "error_message": (
                f"This Flood Alert run is already running: {state} / {run_id}. "
                "Please wait until it finishes instead of submitting it again."
            ),
            "state": state,
            "start_datetime": start_dt,
            "end_datetime": end_dt,
            "workers": workers,
        }
        return App.render(request, "flood_alert_run_status.html", context)

    if done_fp.exists() and (run_dir / "basin_alerts.geojson").exists():
        context = {
            "status": "success",
            "state": state,
            "run_id": run_id,
            "run_dir": str(run_dir),
            "basin_geojson": str(run_dir / "basin_alerts.geojson"),
            "pixel_alerts_parquet": str(base_dir / "ews_alerts" / state / "pixel_alerts.parquet"),
            "message": "This run already exists. Reusing previous outputs.",
        }
        return App.render(request, "flood_alert_run_status.html", context)

    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        lock_fp.write_text("running\n", encoding="utf-8")

        result = run_flood_alert_pipeline(
            base_dir=base_dir,
            state=state,
            start=start_dt,
            end=end_dt,
            workers=workers,
        )

        done_fp.write_text("done\n", encoding="utf-8")

        context = {
            "status": "success",
            "result": result,
            "state": result["state"],
            "run_id": result["run_id"],
            "run_dir": result["run_dir"],
            "basin_geojson": result["exports"]["basin_geojson"],
            "pixel_alerts_parquet": result["exports"]["pixel_alerts_parquet"],
        }

    except Exception as e:
        context = {
            "status": "error",
            "error_message": str(e),
            "state": state,
            "start_datetime": start_dt,
            "end_datetime": end_dt,
            "workers": workers,
        }

    finally:
        try:
            lock_fp.unlink(missing_ok=True)
        except Exception:
            pass

    return App.render(request, "flood_alert_run_status.html", context)


@controller(
    name="flood_alert_results",
    url="flood-alert/results/{state}/{run_id}/",
    app_media=True,
)
def flood_alert_results(request, state, run_id, app_media):
    base_dir = Path(app_media.path)
    state = state.upper()

    run_dir = base_dir / "flood_alert_runs" / state / run_id
    basin_geojson = run_dir / "basin_alerts.geojson"
    pixel_parquet = base_dir / "ews_alerts" / state / "pixel_alerts.parquet"

    context = {
        "state": state,
        "run_id": run_id,
        "run_dir": str(run_dir),
        "basin_geojson_exists": basin_geojson.exists(),
        "pixel_parquet_exists": pixel_parquet.exists(),
        "basin_geojson_path": str(basin_geojson),
        "pixel_parquet_path": str(pixel_parquet),
    }

    return App.render(request, "flood_alert_results.html", context)


@controller(
    name="flood_alert_basin_geojson",
    url="flood-alert/geojson/{state}/{run_id}/basins/",
    app_media=True,
)
def flood_alert_basin_geojson(request, state, run_id, app_media):
    base_dir = Path(app_media.path)
    state = state.upper()

    fp = base_dir / "flood_alert_runs" / state / run_id / "basin_alerts.geojson"

    if not fp.exists():
        return JsonResponse({"error": f"Missing basin GeoJSON: {fp}"}, status=404)

    with open(fp, "r", encoding="utf-8") as f:
        obj = json.load(f)

    relevant_levels = {"WARNING", "SEVERE"}

    features = [
        feat
        for feat in obj.get("features", [])
        if feat.get("properties", {}).get("alert_level") in relevant_levels
    ]

    # IMPORTANT:
    # Draw larger basins first and smaller basins last.
    # In Leaflet, later features sit on top, so small basins remain clickable.
    features = sorted(
        features,
        key=lambda feat: _geometry_bbox_area(feat.get("geometry")),
        reverse=True,
    )

    obj["features"] = features
    obj.setdefault("metadata", {})
    obj["metadata"]["filtered_to_relevant_alerts"] = True
    obj["metadata"]["included_alert_levels"] = sorted(relevant_levels)
    obj["metadata"]["filtered_n_features"] = len(features)
    obj["metadata"]["sorted_large_to_small_for_clickability"] = True

    return JsonResponse(obj, safe=False)


@controller(
    name="flood_alert_pixel_geojson",
    url="flood-alert/geojson/{state}/{run_id}/pixels/",
    app_media=True,
)
def flood_alert_pixel_geojson(request, state, run_id, app_media):
    base_dir = Path(app_media.path)
    state = state.upper()

    site_id = request.GET.get("site_id")
    max_pixels = int(request.GET.get("max_pixels", "5000"))

    if not site_id:
        return JsonResponse({"error": "Missing required query parameter: site_id"}, status=400)

    parquet_fp = base_dir / "ews_alerts" / state / "pixel_alerts.parquet"

    if not parquet_fp.exists():
        return JsonResponse({"error": f"Missing pixel alerts parquet: {parquet_fp}"}, status=404)

    df = pd.read_parquet(parquet_fp)

    if df.empty:
        return JsonResponse(
            {
                "type": "FeatureCollection",
                "features": [],
                "metadata": {
                    "state": state,
                    "site_id": site_id,
                    "n_features": 0,
                    "note": "pixel_alerts.parquet is empty",
                },
            },
            safe=False,
        )

    df = df[df["site_id"].astype(str) == str(site_id)].copy()

    if df.empty:
        return JsonResponse(
            {
                "type": "FeatureCollection",
                "features": [],
                "metadata": {
                    "state": state,
                    "site_id": site_id,
                    "n_features": 0,
                    "note": "No pixel alerts found for site_id",
                },
            },
            safe=False,
        )

    sort_cols = [c for c in ["estimated_delta_water_stage", "current_pixel_value"] if c in df.columns]
    if sort_cols:
        df = df.sort_values(sort_cols, ascending=False)

    if max_pixels is not None and len(df) > max_pixels:
        df = df.head(max_pixels).copy()

    property_cols = [
        "state",
        "site_id",
        "pixel_id_state",
        "pixel_id_basin",
        "row",
        "col",
        "current_pixel_value",
        "current_pixel_accumulation",
        "current_basin_accumulation",
        "historical_basin_accumulation_threshold",
        "estimated_delta_water_stage",
        "estimated_time_to_rain_peak_accumulation_hr",
        "estimated_time_to_stage_peak_hr",
        "matched_hist_pixel_value",
        "matched_hist_basin_accumulation",
        "matched_hist_delta_water_stage",
        "match_score",
        "matched_n",
    ]

    features = []

    for _, row in df.iterrows():
        lon = float(row["lon"])
        lat = float(row["lat"])

        props = {c: _json_safe(row[c]) for c in property_cols if c in row.index}

        delta = props.get("estimated_delta_water_stage")
        if delta is None:
            alert_level = "WATCH"
        elif delta >= 10.0:
            alert_level = "SEVERE"
        elif delta >= 2.0:
            alert_level = "WARNING"
        else:
            alert_level = "WATCH"

        props["alert_level"] = alert_level
        props["fill_color"] = ALERT_COLORS.get(alert_level, "#808080")
        props["stroke_color"] = "#222222"

        features.append(
            {
                "type": "Feature",
                "geometry": _pixel_polygon_from_center(lon, lat),
                "properties": props,
            }
        )

    return JsonResponse(
        {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "state": state,
                "site_id": site_id,
                "n_features": len(features),
                "source": str(parquet_fp),
                "dynamic_from_parquet": True,
                "max_pixels": max_pixels,
            },
        },
        safe=False,
    )