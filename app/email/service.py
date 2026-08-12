import logging
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def _render_template(template_name: str, **kwargs: str) -> str:
    path = TEMPLATES_DIR / template_name
    content = path.read_text(encoding="utf-8")
    for key, value in kwargs.items():
        content = content.replace("{" + key + "}", value)
    return content


class EmailService:
    def __init__(self) -> None:
        self.api_key = settings.agentmail_api_key
        self.inbox_id = settings.agentmail_inbox_id

    def _send(self, to: str, subject: str, html: str) -> bool:
        if not self.api_key or not self.inbox_id:
            logger.warning("AgentMail credentials not configured — skipping email to %s", to)
            return False
        try:
            import httpx
            url = f"https://api.agentmail.to/v0/inboxes/{self.inbox_id}/messages/send"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "to": to,
                "subject": subject,
                "html": html
            }
            response = httpx.post(url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info("Email sent to %s — subject: %s", to, subject)
            return True
        except Exception:
            logger.exception("Failed to send email to %s", to)
            return False

    def send_welcome_email(
        self,
        to_email: str,
        name: str,
        username: str,
        temporary_password: str,
    ) -> bool:
        html = _render_template(
            "welcome.html",
            name=name,
            email=to_email,
            temporary_password=temporary_password,
            login_url="https://fifa-scoring.com/login",
        )
        return self._send(
            to=to_email,
            subject="Welcome to FIFA Scoring System",
            html=html,
        )

    def send_reset_password_otp(
        self,
        to_email: str,
        name: str,
        otp_code: str,
        expiry_minutes: int = 15,
    ) -> bool:
        html = _render_template(
            "reset_password_otp.html",
            name=name,
            email=to_email,
            otp_code=otp_code,
            expiry_minutes=str(expiry_minutes),
        )
        return self._send(
            to=to_email,
            subject="GOALGORITHM Password Reset OTP",
            html=html,
        )
