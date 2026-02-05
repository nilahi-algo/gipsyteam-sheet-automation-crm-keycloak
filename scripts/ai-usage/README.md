# AI Usage Reporter (Slack only)

Sends **daily** and **monthly** AI usage reports to a Slack channel for Manus, Cursor, Claude, and ChatGPT.

- **Daily**: Every day at **18:00 Dubai time** (14:00 UTC) – report for the previous day.
- **Monthly**: On the **1st of each month** at **18:00 Dubai time** – full report for the **entire previous month** (e.g. March 1st → February’s report).

Data is **not** saved anywhere except Slack (the posted messages are the record).

---

## Setup

1. **Copy env example and add your keys**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set at least:
   - `SLACK_WEBHOOK_URL` – Incoming Webhook URL for the channel where reports should go.
   - One or more of: `MANUS_API_KEY`, `CURSOR_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_ADMIN_API_KEY`.

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run manually**
   - Daily (report for yesterday in UTC):
     ```bash
     python collect_usage.py
     ```
   - Daily for a specific date:
     ```bash
     python collect_usage.py 2025-02-15
     ```
   - Monthly (previous month by default):
     ```bash
     python collect_usage.py monthly
     ```
   - Monthly for a given month:
     ```bash
     python collect_usage.py monthly 2025 2
     ```

---

## Scheduling (GitHub Actions)

Use the workflow in `.github/workflows/ai-usage-report.yml`:

- **Daily** at 14:00 UTC (18:00 Dubai): runs daily report for yesterday.
- **Monthly** on the 1st at 14:00 UTC: runs monthly report for the full previous month.

Add these **repository secrets** in GitHub (Settings → Secrets and variables → Actions):

- `SLACK_WEBHOOK_URL` (required)
- `MANUS_API_KEY` (optional)
- `CURSOR_API_KEY` (optional)
- `ANTHROPIC_API_KEY` (optional)
- `OPENAI_ADMIN_API_KEY` (optional)

Only platforms with a set secret are queried; others are skipped.

---

## Connect the AIs (API keys)

See **[CONNECT_AI_PLATFORMS.md](CONNECT_AI_PLATFORMS.md)** for step-by-step: where to get each key, env var name, and what gets reported.

| Platform   | Env / secret name      | Where to get the key |
|-----------|------------------------|------------------------|
| Manus     | `MANUS_API_KEY`        | [API Integration](https://manus.im/app?show_settings=integrations&app_name=api) |
| Cursor    | `CURSOR_API_KEY`       | Dashboard → Settings → Advanced → Admin API Keys (Enterprise) |
| Claude    | `ANTHROPIC_API_KEY`    | Anthropic / Claude platform (Usage API access) |
| ChatGPT   | `OPENAI_ADMIN_API_KEY` | OpenAI – **Organization Admin** key (for usage API) |

---

## Report format in Slack

- **Daily**: One message per day with totals per platform (Manus credits, Cursor requests, Claude/ChatGPT tokens) and per-user breakdown when the API provides it.
- **Monthly**: Same structure for the full previous month.

Errors for a platform (e.g. bad key or API down) are shown in the message for that platform; other platforms still report.
