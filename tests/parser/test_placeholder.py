"""
tests/parser/test_placeholder.py
"""

import sys

import pytest

import libs.global_value as g
from integrations import factory
from libs.functions import configuration
from libs.utils import dictutil, formatter
from tests.parser import param_data

TEST_ARGS = ["progname", "--config=tests/test_data/saki.ini"]


@pytest.mark.parametrize(
    "input_args, player_name, player_list, competition_list",
    list(param_data.command_test_case_01.values()),
    ids=list(param_data.command_test_case_01.keys())
)
def test_command_check(input_args, player_name, player_list, competition_list, monkeypatch):
    """コマンド認識状態チェック"""
    monkeypatch.setattr(sys, "argv", TEST_ARGS)
    configuration.setup()
    configuration.read_memberslist()
    m = factory.select_parser("test")

    param = dictutil.placeholder(g.cfg.results, m)

    print(f"\n  --> in: {input_args.split()} out: {param}")
    assert param.get("player_name") == player_name
    assert param.get("player_list") == player_list
    assert param.get("competition_list") == competition_list


@pytest.mark.parametrize(
    "input_args, player_name, player_list, competition_list",
    list(param_data.name_test_case_01.values()),
    ids=list(param_data.name_test_case_01.keys())
)
def test_player_check(input_args, player_name, player_list, competition_list, monkeypatch):
    """プレイヤー名"""
    monkeypatch.setattr(sys, "argv", TEST_ARGS)
    configuration.setup()
    configuration.read_memberslist()

    m = factory.select_parser("text")
    m.parser({"event": {"text": f"{g.cfg.search.keyword} {input_args}"}})
    g.cfg.results.always_argument.extend(m.argument)
    param = dictutil.placeholder(g.cfg.results, m)

    print(f"\n  --> in: {input_args.split()} out: {param}")
    assert param.get("player_name") == player_name
    assert param.get("player_list") == player_list
    assert param.get("competition_list") == competition_list


@pytest.mark.parametrize(
    "input_args, player_name, player_list, competition_list",
    list(param_data.team_saki_test_case.values()),
    ids=list(param_data.team_saki_test_case.keys())
)
def test_team_check(input_args, player_name, player_list, competition_list, monkeypatch):
    """チーム名"""
    monkeypatch.setattr(sys, "argv", TEST_ARGS)
    configuration.setup()
    configuration.read_memberslist()

    m = factory.select_parser("text")
    m.parser({"event": {"text": f"{g.cfg.search.keyword} {input_args}"}})
    g.cfg.results.always_argument.extend(m.argument)
    param = dictutil.placeholder(g.cfg.results, m)

    print(f"\n  --> in: {input_args.split()} out: {param}")
    assert param.get("player_name") == player_name
    assert param.get("player_list") == player_list
    assert param.get("competition_list") == competition_list


@pytest.mark.parametrize(
    "input_args, player_name, replace_name",
    list(param_data.guest_test_case.values()),
    ids=list(param_data.guest_test_case.keys())
)
def test_guest_check(input_args, player_name, replace_name, monkeypatch):
    """ゲストチェック"""
    monkeypatch.setattr(sys, "argv", TEST_ARGS)
    configuration.setup()
    configuration.read_memberslist()

    m = factory.select_parser("text")
    m.parser({"event": {"text": f"{g.cfg.search.keyword} {input_args}"}})
    g.cfg.results.always_argument.extend(m.argument)
    param = dictutil.placeholder(g.cfg.results, m)

    check_name = formatter.name_replace(param.get("player_name", ""))

    assert g.params.get("player_name") == player_name
    assert check_name == replace_name
