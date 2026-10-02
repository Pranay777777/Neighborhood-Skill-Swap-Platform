import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from .config import settings

log = logging.getLogger("mailer")


@dataclass
class Mail:
    to: str
    subject: str
    body: str


# Filled when SWAP_MAIL_BACKEND=memory; the tests read verification and reset links from here.
outbox: list[Mail] = []


def send_mail(to: str, subject: str, body: str) -> None:
    backend = settings.mail_backend
    if backend == "memory":
        outbox.append(Mail(to, subject, body))
    elif backend == "console":
        log.info("mail to %s: %s\n%s", to, subject, body)
    else:
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = settings.mail_from, to, subject
        msg.set_content(body)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            smtp.send_message(msg)
