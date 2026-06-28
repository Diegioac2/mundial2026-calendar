import os
import requests
from pathlib import Path
from datetime import datetime, timezone

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io/fixtures"
OUT = Path("docs/mundial2026.ics")

LEAGUE_ID = 1
SEASON = 2026
TIMEZONE = "America/Guayaquil"


def esc(text):
    if text is None:
        return ""
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace(",", "\\,")
        .replace(";", "\\;")
        .replace("\n", "\\n")
    )


def dt_ics(date_text):
    dt = datetime.fromisoformat(date_text.replace("Z", "+00:00"))
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def get_fixtures():
    if not API_KEY:
        raise RuntimeError("Falta el secreto API_FOOTBALL_KEY en GitHub Actions.")

    headers = {"x-apisports-key": API_KEY}
    params = {
        "league": LEAGUE_ID,
        "season": SEASON,
        "timezone": TIMEZONE,
    }

    r = requests.get(BASE_URL, headers=headers, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    if data.get("errors"):
        raise RuntimeError(f"Error API-FOOTBALL: {data['errors']}")

    return data.get("response", [])


def build_event(match):
    fixture = match["fixture"]
    teams = match["teams"]
    goals = match["goals"]
    league = match["league"]

    fixture_id = fixture["id"]
    date = fixture["date"]
    venue = fixture.get("venue", {}) or {}
    status = fixture.get("status", {}) or {}

    home = teams["home"]["name"]
    away = teams["away"]["name"]

    home_goals = goals.get("home")
    away_goals = goals.get("away")

    status_short = status.get("short", "")
    status_long = status.get("long", "")

    if home_goals is not None and away_goals is not None:
        title = f"{home} {home_goals}-{away_goals} {away}"
    else:
        title = f"{home} vs {away}"

    round_name = league.get("round", "Mundial 2026")
    summary = f"{title} · {round_name}"

    description = (
        f"Mundial 2026\\n"
        f"Estado: {status_long}\\n"
        f"Marcador: {home_goals if home_goals is not None else '-'} - {away_goals if away_goals is not None else '-'}\\n"
        f"Actualizado automáticamente desde API-FOOTBALL."
    )

    location = ", ".join(
        x for x in [venue.get("name"), venue.get("city")] if x
    )

    start = dt_ics(date)
    end_dt = datetime.fromisoformat(date.replace("Z", "+00:00")).timestamp() + 2 * 60 * 60
    end = datetime.fromtimestamp(end_dt, tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    return f"""BEGIN:VEVENT
UID:wc2026-{fixture_id}@diego-calendar
DTSTAMP:{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")}
DTSTART:{start}
DTEND:{end}
SUMMARY:{esc(summary)}
LOCATION:{esc(location)}
DESCRIPTION:{esc(description)}
BEGIN:VALARM
ACTION:DISPLAY
TRIGGER:-PT1H
DESCRIPTION:{esc(summary)}
END:VALARM
END:VEVENT
"""


def build_calendar(fixtures):
    events = "\n".join(build_event(m) for m in fixtures)

    return f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Diego//Mundial2026Auto//ES
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Mundial 2026 Auto
X-WR-TIMEZONE:{TIMEZONE}
REFRESH-INTERVAL;VALUE=DURATION:PT1H
X-PUBLISHED-TTL:PT1H
{events}
END:VCALENDAR
"""


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fixtures = get_fixtures()
    calendar = build_calendar(fixtures)
    OUT.write_text(calendar, encoding="utf-8")
    print(f"Calendario generado con {len(fixtures)} partidos: {OUT}")


if __name__ == "__main__":
    main()
