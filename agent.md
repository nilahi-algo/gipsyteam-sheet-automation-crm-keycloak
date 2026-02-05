# General Agent Instructions

These conditions and instructions apply to **all tasks** in this project. Follow them for every future task unless a task-specific document overrides them.

---

## 1. Before Starting Any Task

- [ ] Read any task-specific spec (e.g. `SUBSCRIPTION_AUTOMATION_SPEC.md`) if the task has one.
- [ ] Confirm scope with the user if the request is ambiguous.
- [ ] Reuse existing code and patterns in this repo instead of inventing new ones.

---

## 2. Code & Implementation

- **Language / stack**: This project uses **Google Apps Script** (`.gs`), plus markdown/docs. Match existing style and file layout.
- **Secrets**: Never commit API keys, tokens, or passwords. Use `PropertiesService.getScriptProperties()` (or env) and reference them in docs (e.g. `GRANT_ZOHO_ACCESS.md`).
- **Errors**: Use clear error handling (e.g. `try/catch`), log useful messages, and avoid swallowing errors.
- **Naming**: Use consistent, descriptive names for functions, variables, and files. Prefer existing naming in the project.

---

## 3. Documentation

- **Docs**: When adding or changing behavior that affects setup, tokens, or APIs, update or add the relevant `.md` file (e.g. `README.md`, `GRANT_ZOHO_ACCESS.md`).
- **Comments**: Add brief comments for non-obvious logic; avoid commenting the obvious.

---

## 4. Changes & Safety

- **Scope**: Only change what’s needed for the current task unless the user asks for more.
- **Existing behavior**: Don’t remove or alter working behavior without explicit approval.
- **Testing**: If the user can run tests or scripts, suggest a quick way to verify the change.

---

## 5. Task-Specific Specs

For large or long-lived features, keep a **separate spec file** (e.g. `SUBSCRIPTION_AUTOMATION_SPEC.md`) with:
- Triggers and conditions
- Step-by-step workflow
- API/integration details
- Role mappings, enums, or reference tables

Reference that file from here or from the task prompt so the agent follows it.

---

## 6. Agent & Project Boundaries

- **Separate agents = separate tasks**: Whenever a new agent is opened, treat it as a **new project**. Do not mix one agent's GitHub repo or local file locations with another. Each agent's context (repo, folder, files) stays scoped to that agent's task only.
- **Create files only when required**: Do not create or save files in GitHub or on disk unless the task actually needs them. For example, simple questions and answers do **not** require saving any files—respond in chat only.
- **New project = ask before creating**: When starting a new agent for a new project and the task **does** require saving files somewhere, create a **new folder** locally and a **new repository** on GitHub—but **ask the user for the folder/repository name** before creating either.

---

## 7. Your Instructions (Add Below)

Add your own conditions and instructions here. Examples:

- **Priorities**: e.g. “Prefer minimal changes,” “Optimize for readability.”
- **Conventions**: e.g. “Always add a one-line comment for new functions.”
- **Restrictions**: e.g. “Do not add new dependencies without asking.”
- **Communication**: e.g. “Summarize changes in a short list at the end.”

---

*Task-specific specs: see `SUBSCRIPTION_AUTOMATION_SPEC.md` for the Subscription Automation Script.*
