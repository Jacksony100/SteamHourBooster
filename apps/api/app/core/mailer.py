"""Transactional email abstraction.

A pluggable mailer so password-reset / verification emails are actually delivered
in non-test environments. Defaults to a console mailer (logs + in-memory outbox)
so dev/test never depend on a live SMTP server and tokens are never logged in full
beyond the dev console. Provider is selected by ``EMAIL_PROVIDER`` (console|smtp).
"""

from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.message import EmailMessage as MimeMessage

from app.core.config import get_settings
from app.core.observability import get_logger

logger = get_logger("app.mailer")


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    text: str
    html: str | None = None


class Mailer:
    def send(self, message: EmailMessage) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class ConsoleMailer(Mailer):
    """Dev/test mailer. Records messages in an outbox and logs that one was sent.

    The message body (which contains the one-time link) is NOT logged; only the
    recipient + subject, so tokens never leak into logs.
    """

    def __init__(self) -> None:
        self.outbox: list[EmailMessage] = []

    def send(self, message: EmailMessage) -> None:
        self.outbox.append(message)
        logger.info("Email queued (console)", extra={"extra_fields": {"to": message.to, "subject": message.subject}})


class SmtpMailer(Mailer):
    def send(self, message: EmailMessage) -> None:
        settings = get_settings()
        if not settings.smtp_host:
            raise RuntimeError("SMTP_HOST is not configured")
        mime = MimeMessage()
        mime["From"] = settings.email_from
        mime["To"] = message.to
        mime["Subject"] = message.subject
        mime.set_content(message.text)
        if message.html:
            mime.add_alternative(message.html, subtype="html")
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(mime)
        logger.info("Email sent (smtp)", extra={"extra_fields": {"to": message.to, "subject": message.subject}})


_mailer: Mailer | None = None


def set_mailer(mailer: Mailer | None) -> None:
    global _mailer
    _mailer = mailer


def get_mailer() -> Mailer:
    global _mailer
    if _mailer is None:
        provider = get_settings().email_provider.lower()
        _mailer = SmtpMailer() if provider == "smtp" else ConsoleMailer()
    return _mailer


# --- Message builders -------------------------------------------------------

def _link(path: str) -> str:
    base = get_settings().web_base_url.rstrip("/")
    return f"{base}{path}"


def send_password_reset_email(to: str, token: str) -> None:
    link = _link(f"/reset-password?token={token}")
    get_mailer().send(
        EmailMessage(
            to=to,
            subject="Reset your DeckPilot password",
            text=(
                "We received a request to reset your DeckPilot password.\n\n"
                f"Reset it here (valid 30 minutes): {link}\n\n"
                "If you didn't request this, you can ignore this email."
            ),
            html=(
                "<p>We received a request to reset your DeckPilot password.</p>"
                f'<p><a href="{link}">Reset your password</a> (valid 30 minutes).</p>'
                "<p>If you didn't request this, you can ignore this email.</p>"
            ),
        )
    )


def send_email_verification_email(to: str, token: str) -> None:
    link = _link(f"/verify-email?token={token}")
    get_mailer().send(
        EmailMessage(
            to=to,
            subject="Verify your DeckPilot email",
            text=f"Confirm your email for DeckPilot (valid 24 hours): {link}",
            html=f'<p>Confirm your email for DeckPilot (valid 24 hours): <a href="{link}">Verify email</a></p>',
        )
    )
