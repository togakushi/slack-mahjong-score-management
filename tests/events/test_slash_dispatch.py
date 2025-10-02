"""
tests/events/test_slash_dispatch.py
"""

import sys
from typing import cast
from unittest.mock import patch

import pytest

import libs.dispatcher
import libs.global_value as g
from integrations import factory
from integrations.standard_io.parser import MessageParser
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

    with (
        # patch("integrations.slack.events.slash.command_help") as mock_help_slash_command,
        patch("libs.dispatcher.by_keyword") as mock_help_slash_command,  # fixme
    ):
        g.selected_service = "standard_io"
        configuration.setup()
        adapter = factory.select_adapter("standard_io", g.cfg)

        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m = adapter.parser()
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.dispatcher.by_keyword(m)
        mock_help_slash_command.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_results.values()),
    ids=list(param_data.slash_results.keys()),
)
def test_results(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(results)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])

    with (
        patch("libs.functions.configuration.libs.commands.results.entry.main") as mock_slash_results,
    ):
        g.selected_service = "standard_io"
        configuration.setup()
        adapter = factory.select_adapter("standard_io", g.cfg)

        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m = adapter.parser()
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.dispatcher.by_keyword(m)
        mock_slash_results.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_graph.values()),
    ids=list(param_data.slash_graph.keys()),
)
def test_graph(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(graph)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])

    with (
        patch("libs.functions.configuration.libs.commands.graph.entry.main") as mock_slash_graph,
    ):
        g.selected_service = "standard_io"
        configuration.setup()
        adapter = factory.select_adapter("standard_io", g.cfg)

        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m = adapter.parser()
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.dispatcher.by_keyword(m)
        mock_slash_graph.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_ranking.values()),
    ids=list(param_data.slash_ranking.keys()),
)
def test_ranking(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(ranking)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])

    with (
        patch("libs.functions.configuration.libs.commands.ranking.entry.main") as mock_slash_ranking,
    ):
        g.selected_service = "standard_io"
        configuration.setup()
        adapter = factory.select_adapter("standard_io", g.cfg)

        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m = adapter.parser()
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.dispatcher.by_keyword(m)
        mock_slash_ranking.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_report.values()),
    ids=list(param_data.slash_report.keys()),
)
def test_report(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(report)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])

    with (
        patch("libs.functions.configuration.libs.commands.report.entry.main") as mock_slash_report,
    ):
        g.selected_service = "standard_io"
        configuration.setup()
        adapter = factory.select_adapter("standard_io", g.cfg)

        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m = adapter.parser()
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.dispatcher.by_keyword(m)
        mock_slash_report.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_check.values()),
    ids=list(param_data.slash_check.keys()),
)
def test_check(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(check)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])

    with (
        patch("libs.dispatcher.by_keyword") as mock_slash_check,  # fixme
    ):
        g.selected_service = "standard_io"
        configuration.setup()
        adapter = factory.select_adapter("standard_io", g.cfg)
        m = cast(MessageParser, adapter.parser())
        m.set_command_flag(True)

        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.dispatcher.by_keyword(m)
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
    adapter = factory.select_adapter("standard_io", g.cfg)

    m = cast(MessageParser, adapter.parser())
    m.set_command_flag(True)

    param_data.FAKE_BODY["event"].update(text=f"{keyword}")
    m.parser(cast(dict, param_data.FAKE_BODY))
    libs.dispatcher.by_keyword(m)
    assert m.post.file_list[0].get("成績記録DB")


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_member_list.values()),
    ids=list(param_data.slash_member_list.keys()),
)
def test_member_list(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(member)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])

    with (
        patch("libs.functions.configuration.lookup.textdata.get_members_list") as mock_slash_member_list,
    ):
        g.selected_service = "standard_io"
        configuration.setup()
        adapter = factory.select_adapter("standard_io", g.cfg)
        m = cast(MessageParser, adapter.parser())
        m.set_command_flag(True)

        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.dispatcher.by_keyword(m)
        mock_slash_member_list.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_member_add.values()),
    ids=list(param_data.slash_member_add.keys()),
)
def test_member_add(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(add)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])

    with (
        patch("libs.functions.configuration.member.append") as mock_slash_member_add,
    ):
        g.selected_service = "standard_io"
        configuration.setup()

        adapter = factory.select_adapter("standard_io", g.cfg)
        m = cast(MessageParser, adapter.parser())
        m.set_command_flag(True)

        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.dispatcher.by_keyword(m)
        mock_slash_member_add.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_member_del.values()),
    ids=list(param_data.slash_member_del.keys()),
)
def test_member_del(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(del)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])

    with (
        patch("libs.functions.configuration.member.remove") as mock_slash_member_del,
    ):
        g.selected_service = "standard_io"
        configuration.setup()
        adapter = factory.select_adapter("standard_io", g.cfg)
        m = cast(MessageParser, adapter.parser())
        m.set_command_flag(True)

        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.dispatcher.by_keyword(m)
        mock_slash_member_del.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_team_create.values()),
    ids=list(param_data.slash_team_create.keys()),
)
def test_team_create(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(team_create)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])

    with (
        patch("libs.functions.configuration.team.create") as mock_slash_team_create,
    ):
        g.selected_service = "standard_io"
        configuration.setup()
        adapter = factory.select_adapter("standard_io", g.cfg)
        m = cast(MessageParser, adapter.parser())
        m.set_command_flag(True)

        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.dispatcher.by_keyword(m)
        mock_slash_team_create.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_team_del.values()),
    ids=list(param_data.slash_team_del.keys()),
)
def test_team_del(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(team_del)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])

    with (
        patch("libs.functions.configuration.team.delete") as mock_slash_team_del,
    ):
        g.selected_service = "standard_io"
        configuration.setup()
        adapter = factory.select_adapter("standard_io", g.cfg)
        m = cast(MessageParser, adapter.parser())
        m.set_command_flag(True)

        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.dispatcher.by_keyword(m)
        mock_slash_team_del.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_team_add.values()),
    ids=list(param_data.slash_team_add.keys()),
)
def test_team_add(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(team_add)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])

    with (
        patch("libs.functions.configuration.team.append") as mock_slash_team_add,
    ):
        g.selected_service = "standard_io"
        configuration.setup()
        adapter = factory.select_adapter("standard_io", g.cfg)
        m = cast(MessageParser, adapter.parser())
        m.set_command_flag(True)

        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.dispatcher.by_keyword(m)
        mock_slash_team_add.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_team_remove.values()),
    ids=list(param_data.slash_team_remove.keys()),
)
def test_team_remove(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(team_remove)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])

    with (
        patch("libs.functions.configuration.team.remove") as mock_slash_team_remove,
    ):
        g.selected_service = "standard_io"
        configuration.setup()
        adapter = factory.select_adapter("standard_io", g.cfg)
        m = cast(MessageParser, adapter.parser())
        m.set_command_flag(True)

        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.dispatcher.by_keyword(m)
        mock_slash_team_remove.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_team_list.values()),
    ids=list(param_data.slash_team_list.keys()),
)
def test_team_list(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(team_list)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])

    with (
        patch("libs.functions.configuration.lookup.textdata.get_team_list") as mock_slash_team_list,
    ):
        g.selected_service = "standard_io"
        configuration.setup()
        adapter = factory.select_adapter("standard_io", g.cfg)
        m = cast(MessageParser, adapter.parser())
        m.set_command_flag(True)

        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.dispatcher.by_keyword(m)
        mock_slash_team_list.assert_called_once()


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.slash_team_clear.values()),
    ids=list(param_data.slash_team_clear.keys()),
)
def test_team_clear(config, keyword, monkeypatch):
    """スラッシュコマンドイベントテスト(team_clear)"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])

    with (
        patch("libs.functions.configuration.team.clear") as mock_slash_team_clear,
    ):
        g.selected_service = "standard_io"
        configuration.setup()
        adapter = factory.select_adapter("standard_io", g.cfg)
        m = cast(MessageParser, adapter.parser())
        m.set_command_flag(True)

        param_data.FAKE_BODY["event"].update(text=f"{keyword}")
        m.parser(cast(dict, param_data.FAKE_BODY))
        libs.dispatcher.by_keyword(m)
        mock_slash_team_clear.assert_called_once()
