from pathlib import Path

from tethys_sdk.routing import controller
from ..app import App
from ..flood_alert_utils import build_run_directory, build_run_id


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
    context = {
        "states": STATES,
    }
    return App.render(request, "flood_alert.html", context)


@controller(name="run_flood_alert", url="flood-alert/run/", app_media=True)
def run_flood_alert(request, app_media):
    if request.method != "POST":
        return App.render(request, "flood_alert.html", {"states": STATES})

    state = request.POST.get("state", "").upper().strip()
    start_dt = request.POST.get("start_datetime", "").strip()
    end_dt = request.POST.get("end_datetime", "").strip()
    workers = int(request.POST.get("workers", "4"))

    base_dir = Path(app_media.path)
    run_id = build_run_id(start_dt, end_dt)
    run_dir = build_run_directory(base_dir, state, start_dt, end_dt)

    context = {
        "state": state,
        "start_datetime": start_dt,
        "end_datetime": end_dt,
        "workers": workers,
        "base_dir": str(base_dir),
        "run_id": run_id,
        "run_dir": str(run_dir),
    }

    return App.render(request, "flood_alert_run_status.html", context)