"""
Claude Code Skill: /news [project] [days]

Fetches latest crypto news, filters by AADS/MAADS/Slise/Welldone keywords,
matches items to upcoming content calendar slots, and returns ranked
post recommendations with suggested formats and angles.

Usage:
  /news              — top news for all projects, next 14 days
  /news MAADS        — only MAADS-relevant news
  /news AADS 3       — AADS news from last 3 days
  /news check        — show upcoming post schedule
"""

import sys
from datetime import date, timedelta

from content_calendar import build_calendar, format_calendar_summary, posts_this_week
from news_monitor import NewsItem, format_report, run_monitor


# ---------------------------------------------------------------------------
# Formatter with calendar integration
# ---------------------------------------------------------------------------

def _render_item(
    idx: int,
    item: NewsItem,
    calendar: dict,
) -> list[str]:
    lines: list[str] = []
    proj = item.matched_projects[0] if item.matched_projects else "—"

    # Find next matching date in calendar
    today = date.today()
    horizon = today + timedelta(days=14)
    next_date_str = "—"
    next_format = "—"
    for iso, entry in sorted(calendar.items()):
        d = date.fromisoformat(iso)
        if entry["project"] == proj and today <= d <= horizon:
            next_date_str = d.strftime("%d %b (%a)")
            next_format = entry["format"]
            break

    lines.append(f"**{idx}. {item.title}**")
    lines.append(f"   → Project: `{proj}` | Source: {item.source}")
    lines.append(f"   → Next post slot: **{next_date_str}** | Format: *{next_format}*")
    lines.append(f"   → Angle: {item.post_angle}")
    lines.append(f"   → {item.summary[:220]}{'…' if len(item.summary) > 220 else ''}")
    lines.append("")
    return lines


def build_report(
    project_filter: str | None,
    days_back: int,
) -> str:
    calendar = build_calendar()

    print(f"  Fetching news (last {days_back} day(s))…")
    items = run_monitor(days_back=days_back, top_n=15)

    if project_filter:
        pf = project_filter.upper()
        items = [i for i in items if pf in [p.upper() for p in i.matched_projects]]

    if not items:
        name = project_filter or "any project"
        return (
            f"No relevant news found for **{name}** in the last {days_back} day(s).\n\n"
            "Try:\n"
            "  `/news MAADS 5` — widen to 5 days\n"
            "  `/news` — check all projects\n"
        )

    # Header
    today = date.today()
    lines = [
        f"# 📰 News Monitor — {today.strftime('%d %b %Y')}\n",
        f"Found **{len(items)}** relevant items",
        f"(last {days_back} day(s), "
        f"{'all projects' if not project_filter else project_filter})\n",
        "---\n",
    ]

    # Group by project for readability
    project_order = ["MAADS", "AADS", "Slise", "Welldone"]
    by_project: dict[str, list[NewsItem]] = {}
    for item in items:
        if item.matched_projects:
            p = item.matched_projects[0]
            by_project.setdefault(p, []).append(item)

    overall_idx = 1
    for proj in project_order:
        proj_items = by_project.get(proj, [])
        if not proj_items:
            continue
        lines.append(f"## {proj} ({len(proj_items)} items)\n")
        for item in proj_items[:4]:
            lines.extend(_render_item(overall_idx, item, calendar))
            overall_idx += 1

    # Upcoming posts this week
    lines.append("---\n")
    lines.append("## 📅 Posts this week\n")
    this_week = posts_this_week()
    if this_week:
        for d, entry in this_week:
            lines.append(
                f"- **{d.strftime('%d %b (%a)')}** — "
                f"`{entry['project']}` — *{entry['format']}*"
            )
    else:
        lines.append("No posts scheduled in the next 7 days.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Command handler
# ---------------------------------------------------------------------------

class NewsSkillHandler:
    def handle_command(self, args: list[str]) -> str:
        if not args or args[0].lower() == "help":
            return self._help()

        if args[0].lower() == "check":
            return format_calendar_summary(days=14)

        # Parse optional project and days args
        project_filter: str | None = None
        days_back = 2

        for arg in args:
            if arg.upper() in ("MAADS", "AADS", "SLISE", "WELLDONE"):
                project_filter = arg.upper()
            else:
                try:
                    days_back = max(1, min(int(arg), 7))
                except ValueError:
                    pass

        return build_report(project_filter, days_back)

    @staticmethod
    def _help() -> str:
        return (
            "**News Monitor** — daily crypto news matched to your content calendar\n\n"
            "**Commands:**\n"
            "  `/news` — top news for all projects\n"
            "  `/news MAADS` — only MAADS-relevant items\n"
            "  `/news AADS 3` — AADS news from last 3 days\n"
            "  `/news check` — show upcoming post schedule (14 days)\n\n"
            "**Sources monitored:**\n"
            "  - Crypto Integrated (cryptointegrat.com) — daily digest\n"
            "  - The Block (theblock.co) — breaking news\n\n"
            "**Projects & keyword sets:**\n"
            "  - MAADS: regulation, iGaming, marketing strategy\n"
            "  - AADS: ad networks, CPM, crypto advertising restrictions\n"
            "  - Slise: dApp sessions, Etherscan, wallet targeting\n"
            "  - Welldone: security, EU AI Act, FinTech compliance\n"
        )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    handler = NewsSkillHandler()
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    result = handler.handle_command(args)
    print(result)


if __name__ == "__main__":
    main()
