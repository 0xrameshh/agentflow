# Known Issues and Workarounds

This page lists current known bugs and their workarounds. Updated weekly.

## Mobile sync delay
**Status:** In progress (fix expected in v2.4.1)

**Issue:** Changes made on mobile (iOS/Android) can take up to 5 minutes to sync to the web dashboard.

**Workaround:** Pull-to-refresh on mobile immediately forces a sync. On web, click the refresh icon in the top-right corner.

## Calendar integration sync delay
**Status:** Under investigation

**Issue:** After updating a task due date, the change may not reflect in connected calendars (Google Calendar, Outlook) for up to 1 hour.

**Workaround:** Manually trigger a sync from **Settings → Integrations → Calendar → Sync Now**.

## CSV export truncation
**Status:** Resolved in v2.3.5 (workaround still available)

**Issue:** Before v2.3.5, CSV exports with more than 10,000 rows were truncated.

**Workaround:** Use JSON format for large exports, or filter by date range to keep exports under 10,000 rows.

## API rate limit counter glitch
**Status:** Confirmed, fix scheduled for v2.4.2

**Issue:** The `X-RateLimit-Remaining` header may show 0 for 1–2 seconds after a request is processed, even though requests are still being accepted.

**Workaround:** Do not rely on the header for hard rate limit enforcement. Actual enforcement uses server-side counters. Contact us at support@flowdesk.com if you encounter real 429 responses.

## Webhook delivery duplicates
**Status:** Fix in QA (v2.4.0)

**Issue:** During periods of high traffic, webhook endpoints may receive duplicate delivery of the same event within a 5-minute window.

**Workaround:** Webhook consumers should deduplicate by `event_id` (unique per event). We recommend idempotent webhook handling per integrations.md.

## Browser compatibility note
FlowDesk officially supports the latest two versions of Chrome, Firefox, Safari, and Edge. Some UI glitches may appear in Safari if GPU acceleration is disabled.

**Workaround:** Enable "Use GPU acceleration" in Safari's Advanced settings.

For all other issues, check escalation-guide.md or contact support@flowdesk.com.
