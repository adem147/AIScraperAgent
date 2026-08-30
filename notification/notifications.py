import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Iterable

from dotenv import dotenv_values, load_dotenv, set_key

from database.models import Opportunity


def _pretty_date(value):
    if value is None:
        return "Not specified"
    if hasattr(value, "strftime"):
        return value.strftime("%d/%m/%Y")
    return str(value)


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
    message["Subject"] = f"New CERT opportunities detected ({len(opportunities)})"
    message["From"] = sender
    message["To"] = recipient
    plain_text = _format_opportunities(opportunities)
    html_body = _format_opportunities_html(opportunities)
    message.set_content(plain_text)
    message.add_alternative(html_body, subtype="html")

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
    opportunities = list(opportunities)
    if not opportunities:
        return "No new opportunity detected."

    sections = []
    for index, opportunity in enumerate(opportunities, start=1):
        deadline = _pretty_date(opportunity.submission_deadline)
        title = opportunity.title or "Untitled opportunity"
        description = opportunity.description or "No description available."
        url = opportunity.url or "Not available"
        source = opportunity.source_id or "Unknown source"

        sections.append(
            f"{index}. {title}\n"
            f"   Source: {source}\n"
            f"   Description: {description}\n"
            f"   Deadline: {deadline}\n"
            f"   Link: {url}\n"
        )

    header = (
        "CERT Opportunity Monitor\n"
        "========================\n"
        f"{len(opportunities)} new opportunity(ies) detected\n\n"
    )
    return header + "\n".join(sections)


def _format_opportunities_html(opportunities: Iterable[Opportunity]) -> str:
    opportunities = list(opportunities)
    if not opportunities:
        return "<p>No new opportunity detected.</p>"

    items = []
    for index, opportunity in enumerate(opportunities, start=1):
        deadline = _pretty_date(opportunity.submission_deadline)
        title = opportunity.title or "Untitled opportunity"
        description = opportunity.description or "No description available."
        url = opportunity.url or "#"
        source = opportunity.source_id or "Unknown source"
        items.append(
            f"""
            <div style="margin-bottom: 20px; padding: 16px 18px; border: 1px solid #dfe7e2; border-radius: 8px; background: #f8faf8;">
              <div style="font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: #1f6f52; font-weight: 700; margin-bottom: 8px;">Opportunity {index}</div>
              <div style="font-size: 22px; font-weight: 700; color: #1b2b28; margin-bottom: 8px;">{title}</div>
              <div style="font-size: 13px; color: #4c5d59; margin-bottom: 6px;"><strong>Source:</strong> {source}</div>
              <div style="font-size: 13px; color: #4c5d59; margin-bottom: 6px;"><strong>Deadline:</strong> {deadline}</div>
              <div style="font-size: 13px; color: #4c5d59; line-height: 1.5; margin-bottom: 10px;">{description}</div>
              <a href="{url}" style="display: inline-block; padding: 8px 12px; background: #176b4d; color: #ffffff; text-decoration: none; border-radius: 6px; font-size: 12px; font-weight: 700;">View opportunity</a>
            </div>
            """
        )

    return f"""
    <html>
      <body style="margin: 0; padding: 0; font-family: Arial, Helvetica, sans-serif; background-color: #f3f5f1; color: #1b2b28;">
        <div style="max-width: 700px; margin: 30px auto; background: #ffffff; border: 1px solid #e2e8e4; border-radius: 12px; overflow: hidden;">
          <div style="background: #176b4d; color: #ffffff; padding: 20px 24px; font-size: 24px; font-weight: 700;">
            CERT Opportunity Monitor
          </div>
          <div style="padding: 20px 24px 8px;">
            <div style="font-size: 14px; letter-spacing: 0.08em; text-transform: uppercase; color: #5d6a65; font-weight: 700; margin-bottom: 8px;">New opportunities</div>
            <div style="font-size: 18px; font-weight: 600; color: #1b2b28; margin-bottom: 20px;">{len(opportunities)} new opportunity(ies) detected</div>
            {''.join(items)}
          </div>
        </div>
      </body>
    </html>
    """