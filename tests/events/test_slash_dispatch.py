"""
tests/events/test_slash_dispatch.py
"""

import sys
from unittest.mock import patch
from typing import cast
import pytest

import libs.event_dispatcher
import libs.global_value as g
from integrations import factory
from libs.functions import configuration
from tests.events import param_data


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_help.values()),
    ids=list(param_data.slash_help.keys()),
)
def test_help(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(help)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    g.selected_service = "standard_io"
    configuration.setup()

    with (
        patch("libs.functions.compose.msg_help.slash_command") as mock_help_slash_command,
    ):
        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m = factory.select_parser(g.selected_service)
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.event_dispatcher.dispatch_by_keyword(m)
        mock_help_slash_command.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_results.values()),
    ids=list(param_data.slash_results.keys()),
)
def test_results(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(results)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    g.selected_service = "standard_io"
    configuration.setup()

    with (
        patch("libs.commands.dispatcher.main") as mock_slash_results,
    ):
        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m = factory.select_parser(g.selected_service)
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.event_dispatcher.dispatch_by_keyword(m)
        mock_slash_results.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_graph.values()),
    ids=list(param_data.slash_graph.keys()),
)
def test_graph(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(graph)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    g.selected_service = "standard_io"
    configuration.setup()

    with (
        patch("libs.commands.dispatcher.main") as mock_slash_graph,
    ):
        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m = factory.select_parser(g.selected_service)
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.event_dispatcher.dispatch_by_keyword(m)
        mock_slash_graph.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_ranking.values()),
    ids=list(param_data.slash_ranking.keys()),
)
def test_ranking(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(ranking)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    g.selected_service = "standard_io"
    configuration.setup()

    with (
        patch("libs.commands.dispatcher.main") as mock_slash_ranking,
    ):
        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m = factory.select_parser(g.selected_service)
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.event_dispatcher.dispatch_by_keyword(m)
        mock_slash_ranking.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_report.values()),
    ids=list(param_data.slash_report.keys()),
)
def test_report(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(report)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    g.selected_service = "standard_io"
    configuration.setup()

    with (
        patch("libs.commands.dispatcher.main") as mock_slash_report,
    ):
        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m = factory.select_parser(g.selected_service)
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.event_dispatcher.dispatch_by_keyword(m)
        mock_slash_report.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_check.values()),
    ids=list(param_data.slash_check.keys()),
)
def test_check(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(check)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    g.selected_service = "standard_io"
    configuration.setup()

    with (
        patch("libs.event_dispatcher.comparison.main") as mock_slash_check,
    ):
        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m = factory.select_parser(g.selected_service)
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.event_dispatcher.dispatch_by_keyword(m)
        mock_slash_check.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_download.values()),
    ids=list(param_data.slash_download.keys()),
)
def test_download(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(download)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    g.selected_service = "standard_io"
    configuration.setup()

    param_data.FAKE_BODY["event"].update(text=f"{keyword}")
    m = factory.select_parser(g.selected_service)
    m.parser(cast(dict, param_data.FAKE_BODY))
    libs.event_dispatcher.dispatch_by_keyword(m)


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_member_list.values()),
    ids=list(param_data.slash_member_list.keys()),
)
def test_member_list(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(member)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    g.selected_service = "standard_io"
    configuration.setup()

    with (
        patch("libs.event_dispatcher.lookup.textdata.get_members_list", return_value={}) as mock_slash_member_list,
    ):
        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m = factory.select_parser(g.selected_service)
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.event_dispatcher.dispatch_by_keyword(m)
        mock_slash_member_list.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_member_add.values()),
    ids=list(param_data.slash_member_add.keys()),
)
def test_member_add(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(add)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    g.selected_service = "standard_io"
    configuration.setup()

    with (
        patch("libs.event_dispatcher.member.append", return_value=None) as mock_slash_member_add,
    ):
        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m = factory.select_parser(g.selected_service)
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.event_dispatcher.dispatch_by_keyword(m)
        mock_slash_member_add.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_member_del.values()),
    ids=list(param_data.slash_member_del.keys()),
)
def test_member_del(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(del)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    g.selected_service = "standard_io"
    configuration.setup()

    with (
        patch("libs.event_dispatcher.member.remove", return_value=None) as mock_slash_member_del,
    ):
        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m = factory.select_parser(g.selected_service)
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.event_dispatcher.dispatch_by_keyword(m)
        mock_slash_member_del.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_team_create.values()),
    ids=list(param_data.slash_team_create.keys()),
)
def test_team_create(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(team_create)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    g.selected_service = "standard_io"
    configuration.setup()

    with (
        patch("libs.event_dispatcher.team.create", return_value=None) as mock_slash_team_create,
    ):
        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m = factory.select_parser(g.selected_service)
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.event_dispatcher.dispatch_by_keyword(m)
        mock_slash_team_create.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_team_del.values()),
    ids=list(param_data.slash_team_del.keys()),
)
def test_team_del(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(team_del)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    g.selected_service = "standard_io"
    configuration.setup()

    with (
        patch("libs.event_dispatcher.team.delete", return_value=None) as mock_slash_team_del,
    ):
        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m = factory.select_parser(g.selected_service)
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.event_dispatcher.dispatch_by_keyword(m)
        mock_slash_team_del.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_team_add.values()),
    ids=list(param_data.slash_team_add.keys()),
)
def test_team_add(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(team_add)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    g.selected_service = "standard_io"
    configuration.setup()

    with (
        patch("libs.event_dispatcher.team.append", return_value=None) as mock_slash_team_add,
    ):
        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m = factory.select_parser(g.selected_service)
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.event_dispatcher.dispatch_by_keyword(m)
        mock_slash_team_add.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_team_remove.values()),
    ids=list(param_data.slash_team_remove.keys()),
)
def test_team_remove(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(team_remove)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    g.selected_service = "standard_io"
    configuration.setup()

    with (
        patch("libs.event_dispatcher.team.remove", return_value=None) as mock_slash_team_remove,
    ):
        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m = factory.select_parser(g.selected_service)
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.event_dispatcher.dispatch_by_keyword(m)
        mock_slash_team_remove.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_team_list.values()),
    ids=list(param_data.slash_team_list.keys()),
)
def test_team_list(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(team_list)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    g.selected_service = "standard_io"
    configuration.setup()

    with (
        patch("libs.event_dispatcher.lookup.textdata.get_team_list", return_value="") as mock_slash_team_list,
    ):
        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m = factory.select_parser(g.selected_service)
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.event_dispatcher.dispatch_by_keyword(m)
        mock_slash_team_list.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_team_clear.values()),
    ids=list(param_data.slash_team_clear.keys()),
)
def test_team_clear(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(team_clear)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    g.selected_service = "standard_io"
    configuration.setup()

    with (
        patch("libs.event_dispatcher.team.clear", return_value="") as mock_slash_team_clear,
    ):
        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m = factory.select_parser(g.selected_service)
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.event_dispatcher.dispatch_by_keyword(m)
        mock_slash_team_clear.assert_called_once()
