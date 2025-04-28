import sys
from unittest.mock import patch

import pytest
from slack_bolt import App

from libs.functions import configuration, events

from . import param_data


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.message_help.values()),
    ids=list(param_data.message_help.keys()),
)
def test_help(config, keyword, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    configuration.setup()

    with (
        patch("libs.functions.message.help_message") as mock_help_message,
        patch("libs.functions.events.message_event.slack_api") as mock_slack_api
    ):

        fake_client = App.client
        fake_body: dict = {}
        fake_body["event"] = {
            "user": "U9999999999",
            "type": "message",
            "ts": "1744685284.472179",
            "text": f"{keyword}",
            "thread_ts": "1744685284.472179",
        }

        events.message_event.main(fake_client, fake_body)
        mock_slack_api.assert_not_called()
        mock_help_message.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.message_results.values()),
    ids=list(param_data.message_results.keys()),
)
def test_results(config, keyword, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    configuration.setup()

    with (patch("libs.commands.results.slackpost.main") as mock_results):

        fake_client = App.client
        fake_body: dict = {}
        fake_body["event"] = {
            "user": "U9999999999",
            "type": "message",
            "ts": "1744685284.472179",
            "text": f"{keyword}",
            "thread_ts": "1744685284.472179",
        }

        events.message_event.main(fake_client, fake_body)
        mock_results.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.message_graph.values()),
    ids=list(param_data.message_graph.keys()),
)
def test_graph(config, keyword, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    configuration.setup()

    with (patch("libs.commands.graph.slackpost.main") as mock_graph):

        fake_client = App.client
        fake_body: dict = {}
        fake_body["event"] = {
            "user": "U9999999999",
            "type": "message",
            "ts": "1744685284.472179",
            "text": f"{keyword}",
            "thread_ts": "1744685284.472179",
        }

        events.message_event.main(fake_client, fake_body)
        mock_graph.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.message_ranking.values()),
    ids=list(param_data.message_ranking.keys()),
)
def test_ranking(config, keyword, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    configuration.setup()

    with (patch("libs.commands.results.ranking.main") as mock_ranking):

        fake_client = App.client
        fake_body: dict = {}
        fake_body["event"] = {
            "user": "U9999999999",
            "type": "message",
            "ts": "1744685284.472179",
            "text": f"{keyword}",
            "thread_ts": "1744685284.472179",
        }

        events.message_event.main(fake_client, fake_body)
        mock_ranking.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.message_report.values()),
    ids=list(param_data.message_report.keys()),
)
def test_report(config, keyword, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    configuration.setup()

    with (patch("libs.commands.report.slackpost.main") as mock_report):

        fake_client = App.client
        fake_body: dict = {}
        fake_body["event"] = {
            "user": "U9999999999",
            "type": "message",
            "ts": "1744685284.472179",
            "text": f"{keyword}",
            "thread_ts": "1744685284.472179",
        }

        events.message_event.main(fake_client, fake_body)
        mock_report.assert_called_once()
