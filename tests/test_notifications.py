import os
import unittest
from datetime import datetime
from unittest.mock import patch

from database.models import Opportunity
from notification import send_new_opportunities_email


class FakeSMTP:
    sent_messages = []

    def __init__(self, host, port, context):
        self.host = host
        self.port = port
        self.context = context

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def login(self, username, password):
        self.credentials = (username, password)

    def send_message(self, message):
        self.sent_messages.append(message)


class NotificationTests(unittest.TestCase):
    def test_sends_digest_to_configured_recipient(self):
        opportunity = Opportunity(
            title="Audit cybersécurité",
            description="Évaluation de sécurité",
            url="https://example.test/opportunity",
            submission_deadline=datetime(2026, 9, 30),
        )
        config = {
            "SMTP_HOST": "smtp.example.test",
            "SMTP_PORT": "465",
            "SMTP_USERNAME": "sender@example.test",
            "SMTP_PASSWORD": "secret",
            "SMTP_FROM": "sender@example.test",
            "OPPORTUNITIES_EMAIL_TO": "alerts@example.test",
        }

        with patch.dict(os.environ, config, clear=False), patch(
            "notification.notifications.smtplib.SMTP_SSL", FakeSMTP
        ):
            sent_count = send_new_opportunities_email([opportunity])

        message = FakeSMTP.sent_messages[-1]
        self.assertEqual(sent_count, 1)
        self.assertEqual(message["To"], "alerts@example.test")
        self.assertIn("Audit cybersécurité", message.get_content())

    def test_does_not_connect_when_batch_is_empty(self):
        with patch("notification.notifications.smtplib.SMTP_SSL") as smtp:
            self.assertEqual(send_new_opportunities_email([]), 0)
            smtp.assert_not_called()


if __name__ == "__main__":
    unittest.main()