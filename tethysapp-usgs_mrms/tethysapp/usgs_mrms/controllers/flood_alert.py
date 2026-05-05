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