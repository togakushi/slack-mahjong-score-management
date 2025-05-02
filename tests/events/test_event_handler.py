import hashlib
import hmac
import json
import sys
import time
from unittest.mock import patch

from slack_bolt import App
from slack_bolt.request import BoltRequest

from libs import event, handler_registry
from libs.functions import configuration

__all__ = ["event"]


def generate_signature(signing_secret: str, timestamp: str, body: str) -> str:
    sig_basestring = f"v0:{timestamp}:{body}"
    digest = hmac.new(signing_secret.encode(), sig_basestring.encode(), hashlib.sha256).hexdigest()
    return f"v0={digest}"


def test_message_event_called(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["progname", "--config=tests/testdata/minimal.ini"])
    configuration.setup()

    timestamp = str(int(time.time()))
    signing_secret = "signing_secret"
    app = App(signing_secret=signing_secret)
    handler_registry.register_all(app)

    fake_body = json.dumps({
        "type": "event_callback",
        "event": {
            "type": "message",
            "ts": "1234567890.123456",
        }
    })

    signature = generate_signature(signing_secret, timestamp, fake_body)

    bolt_request = BoltRequest(
        body=fake_body,
        headers={
            "Content-Type": "application/json",
            "X-Slack-Request-Timestamp": timestamp,
            "X-Slack-Signature": signature,
        }
    )

    print(bolt_request.body)
    with (
        patch("libs.event.events.message_event.main", return_value=None) as mock_message_event,
        patch("libs.event.events.slash_command.main", return_value=None) as mock_slash_command,
        patch("libs.event.events.home_tab.main", return_value=None) as mock_home_tab,
    ):
        app.dispatch(bolt_request)
        mock_message_event.assert_called()
        mock_slash_command.assert_not_called()
        mock_home_tab.assert_not_called()


def test_slash_command_called(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["progname", "--config=tests/testdata/minimal.ini"])
    configuration.setup()

    timestamp = str(int(time.time()))
    signing_secret = "signing_secret"
    app = App(signing_secret=signing_secret)
    handler_registry.register_all(app)

    fake_body = json.dumps({
        "command": "/mahjong",
        "event": {
            "type": "message",
            "ts": "1234567890.123456",
        }
    })

    signature = generate_signature(signing_secret, timestamp, fake_body)

    bolt_request = BoltRequest(
        body=fake_body,
        headers={
            "Content-Type": "application/json",
            "X-Slack-Request-Timestamp": timestamp,
            "X-Slack-Signature": signature,
        }
    )

    print(bolt_request.body)
    with (
        patch("libs.event.events.message_event.main", return_value=None) as mock_message_event,
        patch("libs.event.events.slash_command.main", return_value=None) as mock_slash_command,
        patch("libs.event.events.home_tab.main", return_value=None) as mock_home_tab,
    ):
        app.dispatch(bolt_request)
        mock_message_event.assert_not_called()
        mock_slash_command.assert_called()
        mock_home_tab.assert_not_called()


def test_home_tab_event_called(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["progname", "--config=tests/testdata/minimal.ini"])
    configuration.setup()

    timestamp = str(int(time.time()))
    signing_secret = "signing_secret"
    app = App(signing_secret=signing_secret)
    handler_registry.register_all(app)

    fake_body = json.dumps({
        "type": "event_callback",
        "event": {
            "type": "app_home_opened",
            "ts": "1234567890.123456",
        }
    })

    signature = generate_signature(signing_secret, timestamp, fake_body)

    bolt_request = BoltRequest(
        body=fake_body,
        headers={
            "Content-Type": "application/json",
            "X-Slack-Request-Timestamp": timestamp,
            "X-Slack-Signature": signature,
        }
    )

    print(bolt_request.body)
    with (
        patch("libs.event.events.message_event.main", return_value=None) as mock_message_event,
        patch("libs.event.events.slash_command.main", return_value=None) as mock_slash_command,
        patch("libs.event.events.home_tab.main", return_value=None) as mock_home_tab,
    ):
        app.dispatch(bolt_request)
        mock_message_event.assert_not_called()
        mock_slash_command.assert_not_called()
        mock_home_tab.assert_called()
