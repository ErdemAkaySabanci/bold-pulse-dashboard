"""Release and live-event timeline used as markers on the review timeline.

Run:  python -m src.events
Output: data/events.csv  (date, version, event, note, source)

The App Store version-history page is rate-limited (HTTP 429) for scripts, so only what
the public Lookup API exposes is filled automatically (store release + current version).
Event rows are a template: dates are entered by hand from the App Store version history
and keep source="manual". Re-running never overwrites hand-entered rows.
"""
from __future__ import annotations

import sys

import pandas as pd
import requests

from src import config

EVENTS_CSV = config.DATA_DIR / "events.csv"
COLUMNS = ["date", "version", "event", "note", "source"]
KNOWN_EVENTS = ["Weekly Contest", "Pool Party", "Super Lightning", "Order Journey",
                "Scanner Booster", "Cupcake Time", "Scooter Race"]


def lookup_rows() -> list[dict]:
    r = requests.get("https://itunes.apple.com/lookup",
                     params={"id": config.APP_STORE_ID, "country": "us"}, timeout=20)
    res = r.json().get("results", [])
    if not res:
        return []
    a = res[0]
    rows = []
    if a.get("releaseDate"):
        rows.append({"date": a["releaseDate"][:10], "version": "", "event": "App Store çıkışı",
                     "note": "", "source": "app_store_lookup"})
    if a.get("currentVersionReleaseDate"):
        rows.append({"date": a["currentVersionReleaseDate"][:10], "version": a.get("version", ""),
                     "event": f"Sürüm {a.get('version', '')}", "note": (a.get("releaseNotes") or "")[:120],
                     "source": "app_store_lookup"})
    return rows


def main() -> None:
    existing = (pd.read_csv(EVENTS_CSV, dtype=str, keep_default_na=False)
                if EVENTS_CSV.exists() else pd.DataFrame(columns=COLUMNS))
    manual = existing[existing["source"] != "app_store_lookup"]
    template = [{"date": "", "version": "", "event": e, "note": "tarih App Store sürüm geçmişinden girilecek",
                 "source": "manual"} for e in KNOWN_EVENTS if e not in set(manual["event"])]
    try:
        auto = lookup_rows()
    except Exception as exc:  # noqa: BLE001
        print(f"[EV] lookup failed ({exc}); keeping existing automatic rows")
        auto = existing[existing["source"] == "app_store_lookup"].to_dict("records")
    out = pd.DataFrame(auto + manual.to_dict("records") + template, columns=COLUMNS)
    out.to_csv(EVENTS_CSV, index=False, encoding="utf-8")
    dated = out[out["date"].str.len() > 0]
    print(f"[EV] {len(out)} rows · {len(dated)} with a date · "
          f"{len(out) - len(dated)} waiting for a date -> {EVENTS_CSV.relative_to(config.ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
