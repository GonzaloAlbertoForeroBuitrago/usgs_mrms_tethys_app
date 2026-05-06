import json
from django.http import JsonResponse
from pathlib import Path

from tethys_sdk.routing import controller
from ..app import App
from ..flood_alert_service import run_flood_alert_pipeline


STATES = [
    "TEXAS",
    "UTAH",
    "IOWA",
    "OKLAHOMA",
    "LOUISIANA",
    "ARKANSAS",
    "COLORADO",
]


@controller(name="flood_alert", url="flood-alert/", app_media=True)
def flood_alert(request, app_media):
    return App.render(request, "flood_alert.html", {"states": STATES})


@controller(name="run_flood_alert", url="flood-alert/run/", app_media=True)
def run_flood_alert(request, app_media):
    if request.method != "POST":
        return App.render(request, "flood_alert.html", {"states": STATES})

    state = request.POST.get("state", "").upper().strip()
    start_dt = request.POST.get("start_datetime", "").strip()
    end_dt = request.POST.get("end_datetime", "").strip()
    workers = int(request.POST.get("workers", "4"))

    try:
        result = run_flood_alert_pipeline(
            base_dir=Path(app_media.path),
            state=state,
            start=start_dt.replace("T", " ") + ":00" if "T" in start_dt else start_dt,
            end=end_dt.replace("T", " ") + ":00" if "T" in end_dt else end_dt,
            workers=workers,
        )

        context = {
            "status": "success",
            "result": result,
            "state": result["state"],
            "run_id": result["run_id"],
            "run_dir": result["run_dir"],
            "basin_geojson": result["exports"]["basin_geojson"],
            "pixel_geojson": result["exports"]["pixel_geojson"],
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
    pixel_geojson = run_dir / "pixel_alerts.geojson"

    context = {
        "state": state,
        "run_id": run_id,
        "run_dir": str(run_dir),
        "basin_geojson_exists": basin_geojson.exists(),
        "pixel_geojson_exists": pixel_geojson.exists(),
        "basin_geojson_path": str(basin_geojson),
        "pixel_geojson_path": str(pixel_geojson),
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

    # Keep only operationally relevant alerts for the map.
    # This avoids loading NORMAL basins and reduces memory usage.
    relevant_levels = {"WARNING", "SEVERE"}

    features = [
        feat
        for feat in obj.get("features", [])
        if feat.get("properties", {}).get("alert_level") in relevant_levels
    ]

    obj["features"] = features
    obj.setdefault("metadata", {})
    obj["metadata"]["filtered_to_relevant_alerts"] = True
    obj["metadata"]["included_alert_levels"] = sorted(relevant_levels)
    obj["metadata"]["filtered_n_features"] = len(features)

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

    fp = base_dir / "flood_alert_runs" / state / run_id / "pixel_alerts.geojson"

    if not fp.exists():
        return JsonResponse({"error": f"Missing pixel GeoJSON: {fp}"}, status=404)

    with open(fp, "r", encoding="utf-8") as f:
        obj = json.load(f)

    if site_id:
        features = [
            feat for feat in obj.get("features", [])
            if str(feat.get("properties", {}).get("site_id")) == str(site_id)
        ]
        obj["features"] = features
        obj["metadata"]["filtered_site_id"] = site_id
        obj["metadata"]["filtered_n_features"] = len(features)

    return JsonResponse(obj, safe=False)