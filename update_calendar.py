from pathlib import Path
from datetime import datetime, timezone

OUT = Path("mundial2026.ics")

calendar = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Diego//Mundial2026Auto//ES
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Mundial 2026 Auto
X-WR-TIMEZONE:America/Guayaquil
REFRESH-INTERVAL;VALUE=DURATION:PT1H
X-PUBLISHED-TTL:PT1H

BEGIN:VEVENT
UID:wc2026-test-update@diego
DTSTAMP:{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")}
DTSTART:20260629T170000Z
DTEND:20260629T190000Z
SUMMARY:Brasil vs Japón · Dieciseisavos
DESCRIPTION:Calendario generado automáticamente por GitHub Actions.
END:VEVENT

END:VCALENDAR
"""

OUT.write_text(calendar, encoding="utf-8")
print("Calendario generado:", OUT)
