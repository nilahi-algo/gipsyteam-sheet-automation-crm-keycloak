#!/usr/bin/env python3
"""
AI Usage Reporter: fetch usage from Manus, Cursor, Claude, ChatGPT;
aggregate by platform and user; post daily or monthly report to Slack only.
"""

import os
import sys
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict

# Load .env from script directory or parent
try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(_env_path)
    load_dotenv()
except ImportError:
    pass

from slack_report import build_slack_payload


# --- Manus --------------------------------------------------------------------

MANUS_BASE = "https://api.manus.ai/v1"


def fetch_manus_usage(api_key: str, start_ts: int, end_ts: int) -> Dict[str, Any]:
    """Fetch Manus credit usage for date range. No per-user in API; report as account."""
    total = 0
    after = None
    while True:
        params = {
            "createdAfter": start_ts,
            "createdBefore": end_ts,
            "limit": 1000,
        }
        if after:
            params["after"] = after
        r = requests.get(
            f"{MANUS_BASE}/tasks",
            headers={"API_KEY": api_key, "Accept": "application/json"},
            params=params,
            timeout=60,
        )
        r.raise_for_status()
        data = r.json()
        for task in data.get("data", []):
            total += task.get("credit_usage") or 0
        if not data.get("has_more"):
            break
        after = data.get("last_id")
        if not after:
            break
    return {"total": total, "unit": "credits", "by_user": [{"user": "account", "value": total}] if total else []}


# --- Cursor -------------------------------------------------------------------

CURSOR_BASE = "https://api.cursor.com"


def _cursor_auth_headers(api_key: str) -> Dict[str, str]:
    """Cursor Admin API: Bearer token (Admin API key from dashboard)."""
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def fetch_cursor_usage(api_key: str, start_dt: datetime, end_dt: datetime) -> Dict[str, Any]:
    """Fetch Cursor usage: daily usage and/or usage events, aggregate by user."""
    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = int(end_dt.timestamp() * 1000)
    headers = _cursor_auth_headers(api_key)

    # Try team members first (some Cursor APIs use /teams/ prefix)
    members = []
    for path in ["/teams/members", "/v1/team/members"]:
        try:
            r = requests.get(f"{CURSOR_BASE}{path}", headers=headers, timeout=30)
            if r.status_code == 200:
                data = r.json()
                members = data.get("members", data) if isinstance(data, dict) else data
                if isinstance(members, list):
                    break
        except Exception:
            members = []

    # Daily usage (team-level or per user)
    by_user: Dict[str, int] = defaultdict(int)
    total = 0
    for path in ["/teams/daily-usage-data", "/v1/usage/daily"]:
        try:
            r = requests.get(
                f"{CURSOR_BASE}{path}",
                headers=headers,
                params={"startDate": start_ms, "endDate": end_ms},
                timeout=30,
            )
            if r.status_code != 200:
                continue
            data = r.json()
            # Handle list of daily records
            if isinstance(data, list):
                for day in data:
                    total += (
                        day.get("subscriptionIncludedReqs", 0)
                        + day.get("apiKeyReqs", 0)
                        + day.get("usageBasedReqs", 0)
                    )
                    uid = day.get("userId") or day.get("email") or "account"
                    by_user[uid] += (
                        day.get("subscriptionIncludedReqs", 0)
                        + day.get("apiKeyReqs", 0)
                        + day.get("usageBasedReqs", 0)
                    )
            elif isinstance(data, dict):
                total = data.get("total", data.get("totalRequests", 0))
                break
            break
        except Exception:
            continue

    # If we have members but no per-user usage, show one "team" row
    if not by_user and total:
        by_user["team"] = total
    by_user_list = [{"user": str(u), "value": v} for u, v in sorted(by_user.items(), key=lambda x: -x[1])]
    return {"total": total, "unit": "requests", "by_user": by_user_list}


# --- Anthropic (Claude) ------------------------------------------------------

ANTHROPIC_BASE = "https://api.anthropic.com"


def fetch_anthropic_usage(api_key: str, start_dt: datetime, end_dt: datetime) -> Dict[str, Any]:
    """Fetch Anthropic usage if Usage API is available. Else return empty."""
    # Usage report may be under platform or org API; try common pattern
    start_rfc = start_dt.strftime("%Y-%m-%dT00:00:00Z")
    end_rfc = end_dt.strftime("%Y-%m-%dT23:59:59Z")
    by_user: Dict[str, int] = defaultdict(int)
    total = 0
    for path in [
        "/v1/organizations/usage_report/messages",
        "/v1/usage_report/messages",
    ]:
        try:
            r = requests.get(
                f"{ANTHROPIC_BASE}{path}",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                params={"starting_at": start_rfc, "ending_at": end_rfc, "bucket_width": "1d"},
                timeout=30,
            )
            if r.status_code != 200:
                continue
            data = r.json()
            # Parse buckets / usage; shape varies by API
            for bucket in data.get("usage", data.get("data", data.get("buckets", []))):
                if isinstance(bucket, dict):
                    total += bucket.get("input_tokens", 0) + bucket.get("output_tokens", 0)
                    uid = bucket.get("user_id") or bucket.get("actor") or "account"
                    by_user[uid] += bucket.get("input_tokens", 0) + bucket.get("output_tokens", 0)
            if isinstance(data, list):
                for item in data:
                    total += item.get("input_tokens", 0) + item.get("output_tokens", 0)
            break
        except Exception:
            continue
    if not by_user and total:
        by_user["account"] = total
    by_user_list = [{"user": str(u), "value": v} for u, v in sorted(by_user.items(), key=lambda x: -x[1])]
    return {"total": total, "unit": "tokens", "by_user": by_user_list}


# --- OpenAI (ChatGPT) ---------------------------------------------------------

OPENAI_BASE = "https://api.openai.com"


def fetch_openai_usage(api_key: str, start_ts: int, end_ts: int) -> Dict[str, Any]:
    """Fetch OpenAI org usage (Admin API). Requires organization-level admin key."""
    by_user: Dict[str, int] = defaultdict(int)
    total = 0
    # Usage API: GET /v1/organization/usage/completions or /v1/usage
    for path in ["/v1/organization/usage/completions", "/v1/usage"]:
        try:
            r = requests.get(
                f"{OPENAI_BASE}{path}",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                params={"start_time": start_ts, "end_time": end_ts, "bucket_width": "1d"},
                timeout=30,
            )
            if r.status_code != 200:
                continue
            data = r.json()
            for bucket in data.get("data", data.get("usage", [])):
                if isinstance(bucket, dict):
                    t = bucket.get("n_tokens", 0) or bucket.get("total_tokens", 0)
                    total += t
                    uid = bucket.get("user_id") or bucket.get("user") or "account"
                    by_user[uid] += t
            if isinstance(data, dict) and "total_usage" in data:
                total = data["total_usage"].get("total_tokens", total)
            break
        except Exception:
            continue
    if not by_user and total:
        by_user["account"] = total
    by_user_list = [{"user": str(u), "value": v} for u, v in sorted(by_user.items(), key=lambda x: -x[1])]
    return {"total": total, "unit": "tokens", "by_user": by_user_list}


# --- Aggregate & Slack --------------------------------------------------------

def get_env(key: str, default: str = "") -> str:
    return (os.getenv(key) or os.getenv(key.replace("_", "")) or default).strip()


def send_to_slack(webhook_url: str, payload: Dict[str, Any]) -> None:
    if not webhook_url:
        print("Slack webhook URL not set; skipping send.")
        return
    r = requests.post(webhook_url, json=payload, timeout=10)
    if r.status_code != 200:
        print(f"Slack POST failed: {r.status_code} {r.text}")
    else:
        print("Slack report sent.")


def run_report(
    report_date: str,
    is_monthly: bool = False,
    year: int = 0,
    month: int = 0,
) -> None:
    """Run usage fetch for date (YYYY-MM-DD) or month, aggregate, post to Slack."""
    if is_monthly and year and month:
        start_dt = datetime(year, month, 1)
        if month == 12:
            end_dt = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_dt = datetime(year, month + 1, 1) - timedelta(seconds=1)
        start_ts = int(start_dt.timestamp())
        end_ts = int(end_dt.timestamp())
        label = f"{year}-{month:02d}"
    else:
        start_dt = datetime.strptime(report_date, "%Y-%m-%d")
        end_dt = start_dt + timedelta(days=1) - timedelta(seconds=1)
        start_ts = int(start_dt.timestamp())
        end_ts = int(end_dt.timestamp())
        label = report_date

    by_platform: Dict[str, Dict[str, Any]] = {}

    if get_env("MANUS_API_KEY"):
        try:
            by_platform["Manus"] = fetch_manus_usage(get_env("MANUS_API_KEY"), start_ts, end_ts)
        except Exception as e:
            by_platform["Manus"] = {"total": 0, "unit": "credits", "by_user": [], "error": str(e)}

    if get_env("CURSOR_API_KEY"):
        try:
            by_platform["Cursor"] = fetch_cursor_usage(
                get_env("CURSOR_API_KEY"), start_dt.replace(hour=0, minute=0, second=0, microsecond=0), end_dt
            )
        except Exception as e:
            by_platform["Cursor"] = {"total": 0, "unit": "requests", "by_user": [], "error": str(e)}

    if get_env("ANTHROPIC_API_KEY"):
        try:
            by_platform["Claude"] = fetch_anthropic_usage(
                get_env("ANTHROPIC_API_KEY"),
                start_dt.replace(hour=0, minute=0, second=0, microsecond=0),
                end_dt,
            )
        except Exception as e:
            by_platform["Claude"] = {"total": 0, "unit": "tokens", "by_user": [], "error": str(e)}

    if get_env("OPENAI_ADMIN_API_KEY"):
        try:
            by_platform["ChatGPT"] = fetch_openai_usage(
                get_env("OPENAI_ADMIN_API_KEY"), start_ts, end_ts
            )
        except Exception as err:
            by_platform["ChatGPT"] = {"total": 0, "unit": "tokens", "by_user": [], "error": str(err)}

    if not by_platform:
        print("No API keys set (MANUS_API_KEY, CURSOR_API_KEY, ANTHROPIC_API_KEY, OPENAI_ADMIN_API_KEY).")
        return

    payload = build_slack_payload(
        label,
        by_platform,
        is_monthly=is_monthly,
        year=year,
        month=month,
    )
    webhook = get_env("SLACK_AI_USAGE_WEBHOOK_URL") or get_env("SLACK_WEBHOOK_URL")
    send_to_slack(webhook, payload)


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "monthly":
        # monthly YYYY MM  -> report for that month (e.g. run on March 1 for February)
        if len(sys.argv) < 4:
            # Default: previous month
            now = datetime.utcnow()
            if now.month == 1:
                year, month = now.year - 1, 12
            else:
                year, month = now.year, now.month - 1
        else:
            year, month = int(sys.argv[2]), int(sys.argv[3])
        run_report("", is_monthly=True, year=year, month=month)
        return
    # Daily: default yesterday (UTC)
    if len(sys.argv) > 1:
        report_date = sys.argv[1]  # YYYY-MM-DD
    else:
        report_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    run_report(report_date, is_monthly=False)


if __name__ == "__main__":
    main()
