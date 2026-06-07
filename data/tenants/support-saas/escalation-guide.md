# Escalation Guide

This guide defines when and how to escalate support tickets to Tier-2.

## Severity definitions

| Severity | Definition | Response SLA | Update Frequency |
|----------|-----------|-------------|-----------------|
| **P1 — Critical** | Service outage, data loss, security breach | 1 hour | Every 2 hours until resolved |
| **P2 — High** | Feature broken for many users, no workaround | 4 hours | Once daily |
| **P3 — Medium** | Feature broken with workaround available | 24 hours | Every 2 business days |
| **P4 — Low** | Cosmetic issue, feature request, documentation | 5 business days | Weekly |

## When to escalate to Tier-2

### Automatically escalate (no debate)
- Customer reports **data loss** (missing projects, tasks, or files).
- The issue involves **security** (suspected breach, unauthorized access).
- Multiple customers report the **same P1/P2 issue** within 1 hour.
- Customer explicitly requests escalation.

### Escalate after first-line triage
- Issue requires **code-level debugging** or database query.
- Billing issue that the billing team cannot resolve (see billing-faq.md for common billing scenarios).
- **SSO / identity provider** configuration problem not resolved by login-troubleshooting.md steps.
- Refund request outside standard 30-day window (see refund-policy.md for exceptions).
- The fix requires a **code deployment** or feature flag change.

### Do NOT escalate
- Standard FAQ questions with answers in this knowledge base.
- Password resets, email changes, or other self-service account actions (see account-settings.md).
- Feature requests — route to `feedback@flowdesk.com` instead.

## How to escalate

1. In the ticket, set severity using the definitions above.
2. Add tag `tier-2` to the ticket.
3. Include in the escalation note:
   - Summary of troubleshooting already performed
   - KB articles referenced
   - Specific error messages, screenshots, or HAR files
4. Submit. Tier-2 is paged automatically based on severity:
   - P1: Page immediately (SMS + phone call)
   - P2: Page within 30 minutes during business hours
   - P3/P4: Queued for next business day

## SLA tiers

| Plan | Support Hours | P1 Response | Channels |
|------|--------------|-------------|----------|
| Free | Business hours (Mon–Fri, 9–5 ET) | N/A | Email only |
| Pro | Business hours + weekend chat | 2 hours | Chat + Email |
| Team | 24/7 | 1 hour | Chat + Email + Phone |
| Enterprise | 24/7 with dedicated AM | 30 minutes | All channels |

## Escalation contacts
- **P1 only:** +1-555-FLOWDESK (phone)
- **All severities:** support@flowdesk.com
- **Enterprise:** Your account manager's direct line
