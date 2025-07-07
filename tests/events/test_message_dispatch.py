"""
tests/events/test_message_dispatch.py
"""

import sys
from unittest.mock import patch

import pytest

import libs.global_value as g
from libs.functions import configuration, events
from tests.events import param_data


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.message_help.values()),
    ids=list(param_data.message_help.keys()),
)
def test_help(config, keyword, monkeypatch):
    """メッセージイベントテスト(help)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    configuration.setup()
    g.selected_service = "test"

    with (
        patch("libs.functions.compose.msg_help.event_message") as mock_help_event_message,
        patch("cls.parser.lookup.api.get_dm_channel_id", return_value="dummy"),
    ):
        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        events.message_event.main(param_data.FAKE_CLIENT, param_data.FAKE_BODY)
        mock_help_event_message.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.message_results.values()),
    ids=list(param_data.message_results.keys()),
)
def test_results(config, keyword, monkeypatch):
    """メッセージイベントテスト(results)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    configuration.setup()
    g.selected_service = "test"

    with (
        patch("libs.commands.results.slackpost.main") as mock_results,
        patch("cls.parser.lookup.api.get_dm_channel_id", return_value="dummy"),
    ):
        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        events.message_event.main(param_data.FAKE_CLIENT, param_data.FAKE_BODY)
        mock_results.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.message_graph.values()),
    ids=list(param_data.message_graph.keys()),
)
def test_graph(config, keyword, monkeypatch):
    """メッセージイベントテスト(graph)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    configuration.setup()
    g.selected_service = "test"


    with (
        patch("libs.commands.graph.slackpost.main") as mock_graph,
        patch("cls.parser.lookup.api.get_dm_channel_id", return_value="dummy"),
    ):
        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        events.message_event.main(param_data.FAKE_CLIENT, param_data.FAKE_BODY)
        mock_graph.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.message_ranking.values()),
    ids=list(param_data.message_ranking.keys()),
)
def test_ranking(config, keyword, monkeypatch):
    """メッセージイベントテスト(ranking)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    configuration.setup()
    g.selected_service = "test"

    with (
        patch("libs.commands.ranking.slackpost.main") as mock_ranking,
        patch("cls.parser.lookup.api.get_dm_channel_id", return_value="dummy"),
    ):
        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        events.message_event.main(param_data.FAKE_CLIENT, param_data.FAKE_BODY)
        mock_ranking.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.message_report.values()),
    ids=list(param_data.message_report.keys()),
)
def test_report(config, keyword, monkeypatch):
    """メッセージイベントテスト(report)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    configuration.setup()
    g.selected_service = "test"

    with (
        patch("libs.commands.report.slackpost.main") as mock_report,
        patch("cls.parser.lookup.api.get_dm_channel_id", return_value="dummy"),
    ):
        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        events.message_event.main(param_data.FAKE_CLIENT, param_data.FAKE_BODY)
        mock_report.assert_called_once()
