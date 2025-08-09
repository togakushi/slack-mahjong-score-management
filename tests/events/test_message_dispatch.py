"""
tests/events/test_message_dispatch.py
"""

import sys
from unittest.mock import patch

import pytest

import libs.event_dispatcher
import libs.global_value as g
from integrations import factory
from libs.functions import configuration
from tests.events import param_data


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.message_help.values()),
    ids=list(param_data.message_help.keys()),
)
def test_help(config, keyword, monkeypatch):
    """メッセージイベントテスト(help)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    g.selected_service = "standard_io"
    configuration.setup()

    with (
        patch("libs.functions.compose.msg_help.event_message") as mock_help_event_message,
    ):
        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m = factory.select_parser(g.selected_service, **g.cfg.setting.to_dict())
        m.parser(param_data.FAKE_BODY)
        libs.event_dispatcher.dispatch_by_keyword(m)
        mock_help_event_message.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.message_results.values()),
    ids=list(param_data.message_results.keys()),
)
def test_results(config, keyword, monkeypatch):
    """メッセージイベントテスト(results)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    g.selected_service = "standard_io"
    configuration.setup()

    with (
        patch("libs.commands.dispatcher.main") as mock_results,
    ):
        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m = factory.select_parser(g.selected_service, **g.cfg.setting.to_dict())
        m.parser(param_data.FAKE_BODY)
        libs.event_dispatcher.dispatch_by_keyword(m)
        mock_results.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.message_graph.values()),
    ids=list(param_data.message_graph.keys()),
)
def test_graph(config, keyword, monkeypatch):
    """メッセージイベントテスト(graph)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    g.selected_service = "standard_io"
    configuration.setup()

    with (
        patch("libs.commands.dispatcher.main") as mock_graph,
    ):
        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m = factory.select_parser(g.selected_service, **g.cfg.setting.to_dict())
        m.parser(param_data.FAKE_BODY)
        libs.event_dispatcher.dispatch_by_keyword(m)
        mock_graph.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.message_ranking.values()),
    ids=list(param_data.message_ranking.keys()),
)
def test_ranking(config, keyword, monkeypatch):
    """メッセージイベントテスト(ranking)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    g.selected_service = "standard_io"
    configuration.setup()

    with (
        patch("libs.commands.dispatcher.main") as mock_ranking,
    ):
        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m = factory.select_parser(g.selected_service, **g.cfg.setting.to_dict())
        m.parser(param_data.FAKE_BODY)
        libs.event_dispatcher.dispatch_by_keyword(m)
        mock_ranking.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.message_report.values()),
    ids=list(param_data.message_report.keys()),
)
def test_report(config, keyword, monkeypatch):
    """メッセージイベントテスト(report)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    g.selected_service = "standard_io"
    configuration.setup()

    with (
        patch("libs.commands.dispatcher.main") as mock_report,
    ):
        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m = factory.select_parser(g.selected_service, **g.cfg.setting.to_dict())
        m.parser(param_data.FAKE_BODY)
        libs.event_dispatcher.dispatch_by_keyword(m)
        mock_report.assert_called_once()
