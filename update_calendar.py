import requests
from pathlib import Path
from datetime import datetime, timezone, timedelta

DATA_URL = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"
OUT = Path("docs/mundial2026.ics")


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


def parse_datetime(match):
    date = match.get("date")
    time = str(match.get("time") or "00:00")

    if not date:
        return None

    time = time.replace(" UTC", "")

    if "-" in time[5:] or "+" in time[5:]:
        base = time[:5]
        offset = time[5:]
        sign = offset[0]
        hours = offset[1:].split(":")[0].zfill(2)
        minutes = offset[1:].split(":")[1] if ":" in offset[1:] else "00"
        time = f"{base}{sign}{hours}:{minutes}"
        return datetime.fromisoformat(f"{date}T{time}")

    return datetime.fromisoformat(f"{date}T{time}:00+00:00")


def team_name(team):
    if isinstance(team, dict):
        return team.get("name") or team.get("code") or "Por definir"
    if isinstance(team, str):
        return team
    return "Por definir"


def score_text(match):
    score = match.get("score")

    if not score:
        return None

    ft = score.get("ft")
    if isinstance(ft, list) and len(ft) == 2:
        return f"{ft[0]}-{ft[1]}"

    return None


def build_event(match):
    num = match.get("num") or match.get("match") or match.get("id")
    round_name = match.get("round") or match.get("stage") or "Mundial 2026"
    group = match.get("group")

    team1 = team_name(match.get("team1"))
    team2 = team_name(match.get("team2"))
    score = score_text(match)

    title = f"{team1} {score} {team2}" if score else f"{team1} vs {team2}"
    summary = f"{title} · {round_name}"

    dt_start = parse_datetime(match)
    if dt_start is None:
        return ""

    dt_end = dt_start + timedelta(hours=2)

    start = dt_start.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    end = dt_end.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    stadium = match.get("stadium") or {}
    if isinstance(stadium, dict):
        location = ", ".join(x for x in [stadium.get("name"), stadium.get("city")] if x)
    else:
        location = stadium or ""

    description = (
        f"Mundial 2026\\n"
        f"Fase: {round_name}\\n"
        f"Grupo: {group or '-'}\\n"
        f"Partido: {team1} vs {team2}\\n"
        f"Marcador: {score or 'Pendiente'}\\n"
        f"Fuente: openfootball/worldcup.json\\n"
        f"Actualizado automáticamente por GitHub Actions."
    )

    uid = f"wc2026-{num}@diego-calendar"

    return f"""BEGIN:VEVENT
UID:{esc(uid)}
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


def extract_matches(data):
    matches = []

    if isinstance(data, dict):
        if "matches" in data:
            matches.extend(data["matches"])
        if "rounds" in data:
            for r in data["rounds"]:
                for m in r.get("matches", []):
                    m["round"] = r.get("name", m.get("round"))
                    matches.append(m)

    return matches


def build_calendar(matches):
    events = "\n".join(build_event(m) for m in matches if build_event(m))

    return f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Diego//Mundial2026OpenFootball//ES
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Mundial 2026 Auto
X-WR-TIMEZONE:America/Guayaquil
REFRESH-INTERVAL;VALUE=DURATION:PT1H
X-PUBLISHED-TTL:PT1H

{events}
END:VCALENDAR
"""


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(DATA_URL, timeout=30)
    response.raise_for_status()

    data = response.json()
    matches = extract_matches(data)

    if not matches:
        raise RuntimeError("No se encontraron partidos en el JSON de openfootball.")

    calendar = build_calendar(matches)
    OUT.write_text(calendar, encoding="utf-8")

    print(f"Calendario generado con {len(matches)} partidos en {OUT}")


if __name__ == "__main__":
    main()
