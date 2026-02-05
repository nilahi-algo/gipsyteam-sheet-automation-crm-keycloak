# Connect Outlook to Cursor via Himalaya CLI

This uses **Himalaya CLI** (terminal email client) with your **Outlook (MS 365)** account so you can **review and reply to email** from Cursor’s terminal and from the AI (by running Himalaya commands).

- **Email:** nilahi@algosoftware.io  
- **Auth:** Your Azure AD app (Client ID + Client Secret) is already in the Himalaya config.

---

## What’s already done

- **Himalaya config** is at:  
  `%APPDATA%\himalaya\config.toml`  
  (e.g. `C:\Users\YourName\AppData\Roaming\himalaya\config.toml`)

  It’s set up for Outlook with OAuth2 using your Azure app. No MCP or Node.js required for this approach.

---

## Step 1: Install Himalaya CLI on Windows

**Option A – Download from GitHub (recommended)**

1. Open: **https://github.com/pimalaya/himalaya/releases**
2. In the latest release (e.g. v1.1.0), under **Assets**, download:
   - **himalaya-windows-x86_64.zip** (or the ARM64 build if you use an ARM PC)
3. Unzip it and put `himalaya.exe` somewhere on your PATH, for example:
   - `C:\Users\YourName\bin\`  
   and add that folder to your system **PATH**, or
   - `C:\Program Files\himalaya\`  
   and add that folder to your system **PATH**
4. Open a **new** terminal and run: `himalaya --version`  
   You should see a version number.

**Option B – Scoop (if you use Scoop)**

```powershell
scoop install himalaya
```

---

## Step 2: First-time OAuth (if needed)

The config already has your Client ID and Client Secret. Himalaya may still need to complete OAuth once to get access/refresh tokens.

1. In Cursor, open the **terminal** (Ctrl+`).
2. Run:
   ```bash
   himalaya account doctor --fix
   ```
   or:
   ```bash
   himalaya account configure
   ```
3. If it opens a browser or shows a URL/code, sign in with **nilahi@algosoftware.io** and complete the flow.

If `himalaya list` (or `himalaya envelope list -f inbox`) works without prompting, you can skip this step.

---

## Step 3: Use email from Cursor

**From the terminal**

- List inbox:
  ```bash
  himalaya list
  ```
  or:
  ```bash
  himalaya envelope list -f inbox
  ```
- Read a message (e.g. message 1):
  ```bash
  himalaya read 1
  ```
- Reply to a message (e.g. 1):
  ```bash
  himalaya reply 1
  ```
  Then edit the draft in your editor (Himalaya will open it) and save/send as instructed.
- Folders:
  ```bash
  himalaya folder list
  ```

**From Cursor AI**

You can ask the AI to run these commands for you, for example:

- *“Run himalaya list and show me the last 10 emails.”*
- *“Run himalaya read 1 and summarize it.”*
- *“Run himalaya reply 1 and draft a short reply saying [your text].”*

The AI can run `himalaya` in the terminal and use the output to review or prepare replies.

---

## Config location (reference)

| Item        | Value |
|------------|--------|
| Config file | `%APPDATA%\himalaya\config.toml` |
| Account name | `outlook` (default) |
| Email      | nilahi@algosoftware.io |

---

## Troubleshooting

- **“himalaya: command not found”**  
  Install Himalaya (Step 1) and ensure the folder containing `himalaya.exe` is on your PATH. Use a new terminal after changing PATH.

- **OAuth / login errors**  
  Run `himalaya account doctor --fix` or `himalaya account configure` and complete the browser sign-in with nilahi@algosoftware.io.

- **“Insufficient privileges” or Mail errors**  
  In Azure Portal, ensure your app has **Mail.Read**, **Mail.ReadWrite**, **Mail.Send**, and **User.Read** (Delegated) and that **admin consent** is granted.

- **Config path**  
  Himalaya on Windows uses:  
  `C:\Users\<YourUsername>\AppData\Roaming\himalaya\config.toml`
