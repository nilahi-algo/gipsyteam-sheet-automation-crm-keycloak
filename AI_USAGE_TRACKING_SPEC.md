# AI Usage Tracking: Daily & Monthly Reports in Slack + Dashboard

## What You Get

- **Daily**: Credit/token usage by user (where supported) for Manus, Cursor, Claude, ChatGPT → posted to Slack.
- **End of month**: Full monthly report (totals + by user) → posted to Slack.
- **Dashboard**: Google Sheet as single source of truth; optional Vercel app for a visual dashboard.

---

## Data Sources & “By User” / “Tokens”

| Platform   | Data available              | By user?              | Metric in API        | How we get it |
|-----------|-----------------------------|------------------------|----------------------|----------------|
| **Manus** | Credits per task            | By project (if 1 project = 1 user) | Credits (no raw tokens) | GET /v1/tasks with createdAfter/createdBefore, sum credit_usage |
| **Cursor**| Per-seat usage, spending    | Yes (per seat)        | Requests, spend; token-like in events | Admin API: daily usage, spending, usage events (Enterprise) |
| **Claude**| API / Claude Code usage     | Yes (by actor/email)   | Tokens, cost         | Anthropic Usage API / Claude Code Usage Report |
| **ChatGPT**| API usage                  | Yes if user_id set     | Tokens, cost         | OpenAI Usage API (organization usage) |

**Note:** Manus exposes **credits**, not token counts. Cursor exposes requests/spend (and possibly tokens in usage events). Claude and OpenAI expose **tokens** (and cost). The report will label each clearly (e.g. “Credits” for Manus, “Tokens” for Claude/ChatGPT).

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  SCHEDULED JOB (GitHub Actions: daily + 1st of month)                   │
│  → scripts/ai-usage/collect_usage.py                                    │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ├── Manus API (API key) ──────────┐
         ├── Cursor Admin API (API key) ───┤
         ├── Anthropic Usage API ──────────┼──► Aggregate by date + user
         └── OpenAI Usage API ─────────────┘
         │
         ▼
┌─────────────────────┐     ┌─────────────────────┐
│  Google Sheet        │     │  Slack               │
│  (raw + summary)     │     │  (daily + monthly    │
│  → Dashboard tab      │     │   report messages)  │
└─────────────────────┘     └─────────────────────┘
         │
         ▼ (optional)
┌─────────────────────┐
│  Vercel dashboard    │  Reads from Google Sheet API
│  (charts, filters)   │  or from exported CSV/JSON
└─────────────────────┘
```

- **Single source of truth**: Google Sheet (one tab = raw rows: date, platform, user, credits/tokens, cost; another = summary/dashboard).
- **Automation**: GitHub Actions runs `collect_usage.py` on a schedule (daily + end-of-month).
- **Slack**: Same script sends a formatted message (daily summary + full monthly report at month-end) to your existing Slack webhook.
- **Dashboard**: Sheet first (charts, pivots); optional Vercel app for a nicer UI.

---

## What You Need to Provide

### 1. API keys / access

- **Manus**: API key from [API Integration settings](https://manus.im/app?show_settings=integrations&app_name=api). Stored as `MANUS_API_KEY`.
- **Cursor**: Admin API key (Enterprise team). Dashboard → Settings → Advanced → Admin API Keys. Stored as `CURSOR_API_KEY`. (Uses Basic auth: `API_KEY:`.)
- **Claude**: Anthropic API key with access to Usage/Cost API (or org admin for Claude Code report). Stored as `ANTHROPIC_API_KEY` (and org id if required).
- **ChatGPT (OpenAI)**: **Organization** usage requires an **Admin API key** (not a normal API key). Stored as `OPENAI_ADMIN_API_KEY`. Used for `GET /v1/organization/usage/completions` (or current Usage API path).

### 2. Slack

- **Incoming Webhook URL** for the channel where reports should go. You already have `SLACK_WEBHOOK_URL` in Config/Script Properties; we’ll use the same or a dedicated one (e.g. `SLACK_AI_USAGE_WEBHOOK_URL`) for AI reports.

### 3. Google Sheet

- One **Google Sheet** for AI usage. The script will append rows and (optionally) update a summary tab.
- Access: **Service account** (recommended for GitHub Actions) with edit access to the sheet, or **API key + OAuth** if you prefer. Sheet ID stored as `AI_USAGE_SHEET_ID`.

### 4. Optional: Vercel dashboard

- If you want a Vercel dashboard: a small Next.js (or static) app that reads from the same Google Sheet via Sheets API and displays charts. No extra credentials beyond Sheet access.

---

## Schedule

- **Daily** (e.g. 23:00 UTC): Run collector for “yesterday” (or “today”); append to Sheet; post **daily summary** to Slack (by platform, by user if available, credits/tokens).
- **End of month** (e.g. 1st at 00:30 UTC): Run collector for the **full previous month**; append any missing data; post **monthly report** to Slack (totals + by user, by platform).

Implemented via GitHub Actions cron in this repo.

---

## Report Format in Slack

- **Daily**: Short summary: date, then for each platform (Manus, Cursor, Claude, ChatGPT): total credits/tokens, and per-user breakdown when available.
- **Monthly**: Same structure for the whole month: total credits/tokens per platform, per-user totals, optional cost if APIs provide it.

Blocks or plain text; link to the Google Sheet for full detail.

---

## Dashboard Options

1. **Google Sheet only**  
   - Raw data tab + Summary/Dashboard tab with charts (by date, by user, by platform).  
   - No extra infra; Diksha or anyone can refresh or the script can update it.

2. **Google Sheet + Vercel**  
   - Sheet remains source of truth; Vercel app (e.g. Next.js + Recharts) reads via Sheets API and shows filters (date range, user, platform).  
   - Requires deploying the app to Vercel and granting it read access to the sheet (e.g. service account or published sheet).

---

## File Layout (implementation)

- `scripts/ai-usage/README.md` – How to run, env vars, scheduling.
- `scripts/ai-usage/.env.example` – All variable names (no real secrets).
- `scripts/ai-usage/requirements.txt` – Python deps (requests, gspread or google-api-python-client, python-dotenv, openpyxl).
- `scripts/ai-usage/collect_usage.py` – Fetches from all four providers, aggregates, writes Sheet, sends Slack.
- `scripts/ai-usage/slack_report.py` – Formats daily/monthly payloads for Slack.
- `.github/workflows/ai-usage-report.yml` – Daily + end-of-month runs.

Credentials in GitHub Actions: store `MANUS_API_KEY`, `CURSOR_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_ADMIN_API_KEY`, `SLACK_WEBHOOK_URL` (or `SLACK_AI_USAGE_WEBHOOK_URL`), and Google Sheet credentials (e.g. `GCP_SERVICE_ACCOUNT_JSON` or sheet ID + OAuth) as repo secrets.

---

## Summary

- **Best approach**: One Python script (Manus + Cursor + Claude + ChatGPT) → Google Sheet + Slack; run daily and at end of month via GitHub Actions; use Sheet as dashboard, optionally add Vercel for a nicer UI.
- **Reports in Slack**: Daily summary + full monthly report, with “by user” and “tokens/credits” per platform as available.
- **You provide**: API keys (Manus, Cursor, Anthropic, OpenAI Admin), Slack webhook, one Google Sheet + access (e.g. service account). Optionally Vercel app for dashboard.
