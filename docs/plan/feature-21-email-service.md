# Feature 21: Email Service

## Feature Overview

Email sending service using AgentMail API integration. Sends welcome emails with temporary passwords and password reset OTP codes. Includes HTML email templates with placeholder rendering.

## Purpose & Requirements

- Send welcome emails to newly created team accounts
- Send password reset OTP emails
- HTML email templates with dynamic content
- Graceful fallback if AgentMail credentials not configured
- Domain-validated email addresses only

## How the Feature Works Internally

### Email Service (`app/email/service.py`)
```python
class EmailService:
    def __init__(self):
        self.api_key = settings.AGENTMAIL_API_KEY
        self.inbox_id = settings.AGENTMAIL_INBOX_ID
        self.base_url = f"https://api.agentmail.to/v0/inboxes/{inbox_id}/messages/send"

    async def send_welcome_email(self, to_email, username, temp_password):
        template = self._load_template("welcome.html")
        html = template.replace("{{username}}", username).replace("{{temp_password}}", temp_password)
        await self._send(to_email, "Welcome to GOALGORITHM", html)

    async def send_password_reset_email(self, to_email, otp_code):
        template = self._load_template("reset_password_otp.html")
        html = template.replace("{{otp_code}}", otp_code)
        await self._send(to_email, "Password Reset Code", html)
```

### Templates
- `app/email/templates/welcome.html` — Welcome with temp password + login link
- `app/email/templates/reset_password_otp.html` — 6-digit OTP code (15-min expiry)

## Relevant Backend Implementation

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/email/service.py` | 86 | EmailService class |
| `app/email/templates/welcome.html` | ~50 | Welcome email template |
| `app/email/templates/reset_password_otp.html` | ~40 | OTP email template |

## Configuration/Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AGENTMAIL_API_KEY` | No* | AgentMail API key |
| `AGENTMAIL_INBOX_ID` | No* | Inbox identifier |

*Service gracefully degrades if not configured (logs warning, doesn't send).

## External Dependencies/Integrations

- AgentMail API (https://api.agentmail.to)
- httpx for HTTP requests

## Dependencies on Other Features

- **Authentication** — Registration triggers welcome email
- **Authentication** — Password reset triggers OTP email

## Step-by-Step Implementation Sequence

1. Create EmailService class with AgentMail API integration
2. Create HTML email templates
3. Implement template rendering (simple string replacement)
4. Add graceful fallback for missing credentials
5. Wire into AuthService for registration and password reset
6. Test with mock API responses
