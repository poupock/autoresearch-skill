"""
Content calendar for AADS/MAADS/Slise/Welldone posts.

Stores the full publishing schedule with project, format, and status.
Used by news_monitor to match fresh news to the nearest upcoming post slot.
"""

from datetime import date, timedelta
from typing import Literal

PostFormat = Literal[
    "Hot take (light)",
    "Market Insight",
    "Results breakdown",
    "Mistakes & Patterns",
    "Case study (numbers-first)",
    "Problem → DM CTA",
    "Mini offer / checklist",
    "Contrarian take",
    "Step-by-step logic",
]

Project = Literal["MAADS", "AADS", "Slise", "Welldone"]


def build_calendar() -> dict[str, dict]:
    """
    Returns the full content calendar as {iso_date: {project, format, status}}.

    MAADS: odd days (19, 21, 23 … Apr → May 11)
    AADS:  even days (20, 22, 24 … Apr → May 12)
    """
    calendar: dict[str, dict] = {}

    # ── April / May 2026 mini-post schedule ────────────────────────────────
    maads_dates = [
        date(2026, 4, 19), date(2026, 4, 21), date(2026, 4, 23),
        date(2026, 4, 25), date(2026, 4, 27), date(2026, 4, 29),
        date(2026, 5,  1), date(2026, 5,  3), date(2026, 5,  5),
        date(2026, 5,  7), date(2026, 5,  9), date(2026, 5, 11),
    ]

    maads_formats: list[PostFormat] = [
        "Hot take (light)",       # 19 Apr
        "Hot take (light)",       # 21 Apr
        "Market Insight",         # 23 Apr
        "Market Insight",         # 25 Apr
        "Contrarian take",        # 27 Apr
        "Hot take (light)",       # 29 Apr
        "Market Insight",         # 01 May
        "Market Insight",         # 03 May
        "Hot take (light)",       # 05 May
        "Market Insight",         # 07 May
        "Market Insight",         # 09 May
        "Hot take (light)",       # 11 May
    ]

    aads_dates = [
        date(2026, 4, 20), date(2026, 4, 22), date(2026, 4, 24),
        date(2026, 4, 26), date(2026, 4, 28), date(2026, 4, 30),
        date(2026, 5,  2), date(2026, 5,  4), date(2026, 5,  6),
        date(2026, 5,  8), date(2026, 5, 10), date(2026, 5, 12),
    ]

    aads_formats: list[PostFormat] = [
        "Market Insight",            # 20 Apr
        "Market Insight",            # 22 Apr
        "Market Insight",            # 24 Apr
        "Results breakdown",         # 26 Apr
        "Market Insight",            # 28 Apr
        "Mini offer / checklist",    # 30 Apr
        "Market Insight",            # 02 May
        "Problem → DM CTA",          # 04 May
        "Market Insight",            # 06 May
        "Market Insight",            # 08 May
        "Mini offer / checklist",    # 10 May
        "Market Insight",            # 12 May
    ]

    for d, fmt in zip(maads_dates, maads_formats):
        calendar[d.isoformat()] = {
            "project": "MAADS",
            "format": fmt,
            "status": "pending",
            "text": None,
        }

    for d, fmt in zip(aads_dates, aads_formats):
        calendar[d.isoformat()] = {
            "project": "AADS",
            "format": fmt,
            "status": "pending",
            "text": None,
        }

    return calendar


def next_posts(project: Project, n: int = 3) -> list[tuple[date, dict]]:
    """Return the next n upcoming post slots for a project."""
    today = date.today()
    cal = build_calendar()
    upcoming = sorted([
        (date.fromisoformat(d), v)
        for d, v in cal.items()
        if v["project"] == project and date.fromisoformat(d) >= today
    ])
    return upcoming[:n]


def posts_this_week(project: Project | None = None) -> list[tuple[date, dict]]:
    """Return all posts in the next 7 days, optionally filtered by project."""
    today = date.today()
    end = today + timedelta(days=7)
    cal = build_calendar()
    results = sorted([
        (date.fromisoformat(d), v)
        for d, v in cal.items()
        if date.fromisoformat(d) >= today
        and date.fromisoformat(d) <= end
        and (project is None or v["project"] == project)
    ])
    return results


def format_calendar_summary(days: int = 14) -> str:
    """Print a human-readable schedule for the next N days."""
    today = date.today()
    end = today + timedelta(days=days)
    cal = build_calendar()

    lines = [f"## Content Calendar — next {days} days\n"]
    lines.append(f"{'Date':<14} {'Project':<10} {'Format'}")
    lines.append("-" * 55)

    for iso, entry in sorted(cal.items()):
        d = date.fromisoformat(iso)
        if today <= d <= end:
            lines.append(
                f"{d.strftime('%d %b (%a)'):<14} "
                f"{entry['project']:<10} "
                f"{entry['format']}"
            )

    return "\n".join(lines)


if __name__ == "__main__":
    print(format_calendar_summary(days=14))
