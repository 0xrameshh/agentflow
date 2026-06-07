# Integrations Guide

FlowDesk integrates with popular tools to streamline your workflow.

## Slack integration

### Setup
1. Go to **Settings → Integrations → Slack**.
2. Click **Connect to Slack**.
3. Authorize FlowDesk in the Slack OAuth window.
4. Select which Slack channel receives FlowDesk notifications.
5. Configure notification triggers: new tasks, comments, status changes, @mentions.

### Troubleshooting
- **Integration disconnected:** Re-authorize from Settings → Integrations → Slack → Reconnect.
- **Notifications not appearing:** Check that the bot is invited to the target channel (`/invite @FlowDesk`).
- **Permission errors:** Your Slack workspace admin may need to approve the OAuth app.

### Webhook failures
If you receive a "Webhook failed" notification:
1. Check the webhook URL is still valid (Slack workspace admins may rotate URLs).
2. Verify the channel hasn't been deleted or archived.
3. Re-test the webhook from **Settings → Integrations → Slack → Test**.

## GitHub integration

### Setup
1. Go to **Settings → Integrations → GitHub**.
2. Click **Connect to GitHub**.
3. Authorize FlowDesk for the repositories you want to link.
4. Configure auto-linking: commit messages containing task IDs (e.g., `PROJ-123`) auto-link in FlowDesk.
5. Select which events sync: PR creation, merge status, branch updates.

### Troubleshooting
- **Commits not linking:** Ensure commit messages include the task ID in format `PROJ-123`.
- **Repo not found:** The connected GitHub account needs at least "Read" access to the repository.
- **Sync delay:** GitHub changes may take up to 2 minutes to reflect in FlowDesk.

## Webhook setup (custom)
1. Go to **Settings → Integrations → Webhooks**.
2. Click **Create Webhook**.
3. Enter a **Name** and **Payload URL** (your endpoint).
4. Select **Events** to subscribe to (task created, updated, deleted; comment added).
5. FlowDesk sends a **signing secret** — validate webhook payloads against this secret for security.
6. Click **Save**. FlowDesk sends a test payload — confirm your endpoint responds with 200.

### Webhook payload format
```json
{
  "event": "task.created",
  "task_id": "PROJ-123",
  "title": "Fix login flow",
  "workspace": "acme-corp",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

## API keys
1. Go to **Settings → Integrations → API Keys**.
2. Click **Generate API Key**.
3. Provide a label (e.g., "Automation Script") and select scopes.
4. Copy the key immediately — it's shown **only once**.
5. Revoke keys at any time from the same page.

**Rate limits:** 100 requests per minute per API key.

## Still having integration issues?
Check known-issues.md for current bugs, or escalate via escalation-guide.md.
