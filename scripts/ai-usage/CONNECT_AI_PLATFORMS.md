# Connect the AIs to the usage reporter

Add one or more API keys so the script can fetch usage from each platform. Use the same names in **GitHub Actions secrets** if you want scheduled reports.

---

## 1. Manus

| Item | Value |
|------|--------|
| **Env / secret name** | `MANUS_API_KEY` |
| **Where to get it** | [Manus → API Integration](https://manus.im/app?show_settings=integrations&app_name=api) → Create new / copy key |
| **What we fetch** | Credit usage per day/month (no per-user in API; reported as “account”) |

**Add to `.env`:**
```env
MANUS_API_KEY=your_manus_api_key_here
```

---

## 2. Cursor

| Item | Value |
|------|--------|
| **Env / secret name** | `CURSOR_API_KEY` |
| **Where to get it** | [Cursor Dashboard](https://cursor.com/dashboard) → **Settings** → **Advanced** → **Admin API Keys** → Create New API Key. Requires **Enterprise** team. |
| **What we fetch** | Daily usage (requests) and per-seat breakdown when the API returns it |

**Add to `.env`:**
```env
CURSOR_API_KEY=key_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 3. Claude (Anthropic)

| Item | Value |
|------|--------|
| **Env / secret name** | `ANTHROPIC_API_KEY` |
| **Where to get it** | [Anthropic Console](https://console.anthropic.com) or [Claude platform](https://platform.claude.com) → API keys. Key must have access to **Usage / Cost API** (org admin or usage-enabled key). |
| **What we fetch** | Token usage (and cost if API provides it) by date; per-user when the Usage API returns it |

**Add to `.env`:**
```env
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx
```

---

## 4. ChatGPT (OpenAI)

| Item | Value |
|------|--------|
| **Env / secret name** | `OPENAI_ADMIN_API_KEY` |
| **Where to get it** | [OpenAI Platform](https://platform.openai.com) → **Organization** → **Settings** → **API keys** (or Admin). You need an **organization-level Admin** key that can access the **Usage API**. |
| **What we fetch** | Token usage by date; per-user when you pass `user_id` in API calls or the Usage API returns it |

**Add to `.env`:**
```env
OPENAI_ADMIN_API_KEY=sk-xxxxxxxxxxxxxxxx
```

---

## After adding keys

- **Local:** Edit `scripts/ai-usage/.env` and add the lines above (one per platform you use). Do **not** commit `.env`.
- **GitHub Actions:** Repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret** for each name above (`MANUS_API_KEY`, `CURSOR_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_ADMIN_API_KEY`) and paste the same values.

The reporter only calls platforms for which a key is set; others are skipped. You can start with one platform (e.g. Manus) and add the rest later.
