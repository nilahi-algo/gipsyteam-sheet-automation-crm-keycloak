# Connect Cursor AI to MS 365 Email (nilahi@algosoftware.io)

**Prefer using the terminal email client?** See **[HIMALAYA_CLI_EMAIL_SETUP.md](HIMALAYA_CLI_EMAIL_SETUP.md)** for the **Himalaya CLI** approach (no MCP, no Node.js—just install Himalaya and use it from Cursor’s terminal).

---

This guide uses your **Azure AD app** (Client ID + Client Secret) with the **Microsoft 365 MCP server** so Cursor’s AI can read/send mail via MCP tools.

---

## Security notice

If you shared your **client secret** in chat or anywhere else:

1. **Rotate it** after setup: Azure Portal → App registrations → Your app → Certificates & secrets → Revoke the old secret and create a new one.
2. **Never commit** the secret to git or store it in project files. The MCP config with the secret lives only in your user folder: `%USERPROFILE%\.cursor\config\mcp.json`.

---

## What you need

- **Email:** nilahi@algosoftware.io  
- **Azure AD app:** Client ID and Client Secret (from your app registration)  
- **Node.js 20+** (required to run the Microsoft 365 MCP server)

---

## Step 1: Install Node.js (if needed)

1. Download **Node.js LTS** from https://nodejs.org (Windows Installer .msi).
2. Run the installer and accept the defaults (including “Add to PATH”).
3. Close and reopen Cursor/terminal, then run: `node -v` (you should see e.g. `v22.x.x` or `v24.x.x`).

---

## Step 2: Azure AD app permissions

Your app must have **delegated** permissions so Cursor can act as you (read/send mail):

1. Go to [Azure Portal](https://portal.azure.com) → **Microsoft Entra ID** (or Azure Active Directory) → **App registrations** → your app (Client ID: `892e3f18-7f5b-4195-974a-6ad84c758d8c`).
2. Open **API permissions** → **Add a permission** → **Microsoft Graph** → **Delegated**.
3. Add at least:
   - **Mail.Read**
   - **Mail.ReadWrite**
   - **Mail.Send**
   - **User.Read**
4. Click **Grant admin consent** (you have admin, so you can do this).

---

## Step 3: MCP config in Cursor

The Microsoft 365 MCP server is configured in your **user** Cursor config (not in this repo):

- **Path:** `%USERPROFILE%\.cursor\config\mcp.json`  
  (e.g. `C:\Users\YourName\.cursor\config\mcp.json`)

The config uses your Azure app so Cursor can talk to your mailbox:

- **Client ID:** `892e3f18-7f5b-4195-974a-6ad84c758d8c`
- **Client Secret:** (stored only in `mcp.json` in your user folder; use a placeholder in any doc)
- **Tenant:** `common` (or your tenant ID if you use a single-tenant app)

If the file or folder doesn’t exist, create `config` under `.cursor` and create `mcp.json` with the structure shown in **Step 4**.

---

## Step 4: Example `mcp.json`

Contents of `%USERPROFILE%\.cursor\config\mcp.json`:

```json
{
  "mcpServers": {
    "ms365": {
      "command": "npx",
      "args": ["-y", "@softeria/ms-365-mcp-server", "--org-mode"],
      "env": {
        "MS365_MCP_CLIENT_ID": "892e3f18-7f5b-4195-974a-6ad84c758d8c",
        "MS365_MCP_CLIENT_SECRET": "<your-client-secret>",
        "MS365_MCP_TENANT_ID": "common"
      }
    }
  }
}
```

Replace `<your-client-secret>` with your real client secret.  
Use `--org-mode` for work/school accounts (e.g. nilahi@algosoftware.io).

---

## Step 5: Restart Cursor and sign in

1. Save `mcp.json` and **restart Cursor**.
2. Open the **AI chat** (Composer or Chat).
3. Ask the agent to **log you in**, e.g.:  
   *“Use the Microsoft 365 login tool to sign me in.”*
4. When the agent shows a **URL and code**, open the URL in your browser, enter the code, and sign in with **nilahi@algosoftware.io**.
5. After success, the agent can use your mailbox (list mail, get message, create draft, send).

---

## Step 6: Use Cursor to review and reply

Once logged in, you can say things like:

- *“List my last 10 emails in the Inbox.”*
- *“Get the full content of the email with subject …”*
- *“Draft a reply to the email from [sender] saying: …”*
- *“Create a draft reply to my latest email.”*

Drafts are created in your Outlook mailbox; you can send them from Outlook or ask the agent to send (if you use the send tool).

---

## Troubleshooting

- **“Login required”:** Run the login tool again (device code flow) and complete the browser sign-in.
- **“Insufficient privileges”:** In Azure, add the Mail permissions above and grant admin consent.
- **MCP server not starting:** Ensure Node.js is installed and `node -v` / `npx` work in a new terminal; check Cursor’s MCP logs (e.g. Output panel → MCP).

---

## Summary

| Item            | Value / action                                      |
|-----------------|-----------------------------------------------------|
| Email           | nilahi@algosoftware.io                              |
| Client ID       | 892e3f18-7f5b-4195-974a-6ad84c758d8c                |
| Config file     | `%USERPROFILE%\.cursor\config\mcp.json`             |
| One-time login  | Use the MCP “login” tool in Cursor (device code)    |
| Rotate secret   | After setup, revoke old secret and create new one   |
