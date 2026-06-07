# Login Troubleshooting

This guide covers the most common login issues and their solutions.

## Password reset
1. Go to the login page and click **Forgot Password?**
2. Enter your registered email address.
3. You'll receive a password reset link within 5 minutes. It expires after 1 hour.
4. Click the link and enter a new password (minimum 8 characters, must include a number and a special character).
5. Log in with your new password.

If you don't receive the reset email, check your spam folder. Still missing? Contact support@flowdesk.com.

## 2FA lockout
If you've lost access to your authenticator app or hardware key:

1. Try using a **recovery code** — these were provided when you enabled 2FA.
2. If you don't have recovery codes, go to **Login → Need help? → Lost 2FA device**.
3. Complete identity verification (we'll send a code to your registered email).
4. After verification, 2FA is temporarily disabled. Re-enable it immediately from **Settings → Security**.
5. If email verification also fails, escalate to Tier-2 per escalation-guide.md.

**Important:** Recovery codes are one-time use. Generate new ones after using any.

## SSO issues
FlowDesk supports SSO via Google Workspace, Microsoft Entra ID, and Okta.

### SSO login fails
1. Confirm SSO is enabled for your domain (ask your IT admin).
2. Try clearing browser cookies and cache, then retry.
3. Check that your email domain matches the one configured in FlowDesk's SSO settings.
4. If you see "Email not linked to any FlowDesk account," you may need a workspace invite first.

### SSO setup for IT admins
See integrations.md for SSO configuration steps.

## "Invalid session" errors
- **Expired session:** Sessions expire after 24 hours. Log out and log back in.
- **Multiple logins:** Logging in on a new device may invalidate the old session token.
- **Browser issue:** Try incognito/private mode. If it works, clear your browser cache and cookies.

## Account locked
After 5 failed login attempts, your account is locked for 15 minutes. Wait or contact support@flowdesk.com for manual unlock.

## Still stuck?
Run through account-settings.md for profile troubleshooting, or escalate via escalation-guide.md.
