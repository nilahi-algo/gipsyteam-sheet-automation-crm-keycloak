"""
Format AI usage data for Slack (daily summary and monthly report).
"""

from typing import List, Dict, Any
from datetime import datetime


def _block_section(text: str) -> Dict[str, Any]:
    return {"type": "section", "text": {"type": "mrkdwn", "text": text}}


def _block_divider() -> Dict[str, Any]:
    return {"type": "divider"}


def format_daily_report(
    date: str,
    by_platform: Dict[str, Dict[str, Any]],
    report_type: str = "daily",
) -> Dict[str, Any]:
    """
    Build Slack Block Kit payload for a daily usage summary.
    by_platform: { "Manus": { "total": N, "unit": "credits", "by_user": [{"user": "...", "value": N}] }, ... }
    """
    lines = [f"*AI usage – {date}*"]
    for platform, data in by_platform.items():
        total = data.get("total") or 0
        unit = data.get("unit", "credits/tokens")
        err = data.get("error")
        if err:
            lines.append(f"• *{platform}*: _error: {err}_")
        else:
            lines.append(f"• *{platform}*: {total:,} {unit}")
        by_user = data.get("by_user") or []
        for u in by_user[:10]:  # cap per platform
            lines.append(f"  – {u.get('user', '?')}: {u.get('value', 0):,}")
        if by_user and len(by_user) > 10:
            lines.append(f"  _... and {len(by_user) - 10} more_")
    blocks = [
        _block_section("\n".join(lines)),
        _block_divider(),
    ]
    return {"blocks": blocks, "text": f"AI usage report – {date}"}


def format_monthly_report(
    year: int,
    month: int,
    by_platform: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build Slack Block Kit payload for end-of-month report.
    by_platform: same shape as format_daily_report.
    """
    month_name = datetime(year, month, 1).strftime("%B %Y")
    lines = [f"*AI usage – monthly report ({month_name})*"]
    for platform, data in by_platform.items():
        total = data.get("total") or 0
        unit = data.get("unit", "credits/tokens")
        err = data.get("error")
        if err:
            lines.append(f"• *{platform}*: _error: {err}_")
        else:
            lines.append(f"• *{platform}*: {total:,} {unit}")
        by_user = data.get("by_user") or []
        for u in by_user[:15]:
            lines.append(f"  – {u.get('user', '?')}: {u.get('value', 0):,}")
        if by_user and len(by_user) > 15:
            lines.append(f"  _... and {len(by_user) - 15} more_")
    blocks = [
        _block_section("\n".join(lines)),
        _block_divider(),
    ]
    return {"blocks": blocks, "text": f"AI usage monthly report – {month_name}"}


def build_slack_payload(
    date: str,
    by_platform: Dict[str, Dict[str, Any]],
    is_monthly: bool = False,
    year: int = 0,
    month: int = 0,
) -> Dict[str, Any]:
    """Choose daily vs monthly format and return full payload for webhook."""
    if is_monthly and year and month:
        return format_monthly_report(year, month, by_platform)
    return format_daily_report(date, by_platform, "daily")
