from .notifications import (
    SMTP_PROVIDERS,
    get_smtp_settings,
    save_smtp_settings,
    send_new_opportunities_email,
)
from .schemas import SMTPSettings

__all__ = [
    "SMTP_PROVIDERS",
    "get_smtp_settings",
    "save_smtp_settings",
    "send_new_opportunities_email",
    "SMTPSettings",
]