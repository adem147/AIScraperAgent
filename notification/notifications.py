import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Iterable

from dotenv import dotenv_values, load_dotenv, set_key

from database.models import Opportunity


load_dotenv()

SMTP_PROVIDERS = {
    "gmail": {"host": "smtp.gmail.com", "port": 465, "use_ssl": True},
    "outlook": {"host": "smtp.office365.com", "port": 587, "use_ssl": False},
    "sendgrid": {"host": "smtp.sendgrid.net", "port": 465, "use_ssl": True},
}
ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")


def _default_username_from_sender(sender: str) -> str:
    return sender.strip()


def get_smtp_settings() -> dict[str, str | int | bool]:
    values = dotenv_values(ENV_FILE)
    password = os.getenv("SMTP_PASSWORD", values.get("SMTP_PASSWORD", ""))
    provider = os.getenv("SMTP_PROVIDER", values.get("SMTP_PROVIDER", "gmail"))
    sender = os.getenv("SMTP_FROM", values.get("SMTP_FROM", ""))
    username = os.getenv("SMTP_USERNAME", values.get("SMTP_USERNAME") or sender)
    return {
        "provider": provider,
        "sender": sender,
        "recipient": os.getenv("OPPORTUNITIES_EMAIL_TO", values.get("OPPORTUNITIES_EMAIL_TO", "")),
        "username": username,
        "has_password": bool(password),
        "host": os.getenv("SMTP_HOST", values.get("SMTP_HOST", "")),
        "port": int(os.getenv("SMTP_PORT", values.get("SMTP_PORT", "465"))),
        "use_ssl": os.getenv("SMTP_USE_SSL", values.get("SMTP_USE_SSL", "true")).lower() in {"1", "true", "yes"},
    }


def save_smtp_settings(settings: dict[str, str | int | bool]) -> None:
    provider = str(settings["provider"])
    preset = SMTP_PROVIDERS[provider]
    host = str(settings.get("host") or preset["host"])
    port = int(settings.get("port") or preset["port"])
    use_ssl = bool(settings.get("use_ssl", preset["use_ssl"]))
    sender = str(settings["sender"]).strip()
    username = str(settings.get("username") or sender or "").strip()

    values = {
        "SMTP_PROVIDER": provider,
        "SMTP_HOST": host,
        "SMTP_PORT": str(port),
        "SMTP_USE_SSL": str(use_ssl).lower(),
        "SMTP_FROM": sender,
        "OPPORTUNITIES_EMAIL_TO": str(settings["recipient"]),
        "SMTP_USERNAME": username,
    }
    password = str(settings.get("password", ""))
    if password:
        values["SMTP_PASSWORD"] = password
    for key, value in values.items():
        set_key(ENV_FILE, key, value)
        os.environ[key] = value


def send_new_opportunities_email(opportunities: Iterable[Opportunity]) -> int:
    """Send one digest containing the opportunities inserted in the latest batch."""
    opportunities = list(opportunities)
    if not opportunities:
        return 0

    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    smtp_user = os.getenv("SMTP_USERNAME", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    sender = os.getenv("SMTP_FROM", smtp_user).strip()
    recipient = os.getenv("OPPORTUNITIES_EMAIL_TO", "").strip()
    use_ssl = os.getenv("SMTP_USE_SSL", "true").lower() in {"1", "true", "yes"}

    missing = [
        name for name, value in {
            "SMTP_HOST": smtp_host,
            "SMTP_USERNAME": smtp_user,
            "SMTP_PASSWORD": smtp_password,
            "SMTP_FROM": sender,
            "OPPORTUNITIES_EMAIL_TO": recipient,
        }.items() if not value
    ]
    if missing:
        print(
            "SMTP is not configured. Missing environment variable(s): "
            + ", ".join(missing)
            + ". Skipping email delivery."
        )
        return 0

    message = EmailMessage()
    message["Subject"] = f"{len(opportunities)} nouvelle(s) opportunité(s) CERT"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(_format_opportunities(opportunities))

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=ssl.create_default_context()) as smtp:
                smtp.login(smtp_user, smtp_password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(smtp_host, smtp_port) as smtp:
                smtp.starttls(context=ssl.create_default_context())
                smtp.login(smtp_user, smtp_password)
                smtp.send_message(message)
    except Exception as exc:
        print(f"SMTP delivery failed: {exc}. Continuing without blocking the scraper.")
        return 0

    return len(opportunities)


def _format_opportunities(opportunities: Iterable[Opportunity]) -> str:
    sections = []
    for index, opportunity in enumerate(opportunities, start=1):
        deadline = opportunity.submission_deadline or "Non précisée"
        sections.append(
            f"{index}. {opportunity.title or 'Sans titre'}\n"
            f"Description: {opportunity.description or 'Non disponible'}\n"
            f"Date limite: {deadline}\n"
            f"Lien: {opportunity.url or 'Non disponible'}"
        )
    return "Nouvelles opportunités détectées :\n\n" + "\n\n".join(sections)