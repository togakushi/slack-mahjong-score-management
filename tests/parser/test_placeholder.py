"""
tests/parser/test_placeholder.py
"""

import sys

import pytest

import libs.global_value as g
from libs.functions import configuration
from libs.utils import dictutil
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

    g.msg.argument = input_args.split()
    param1 = dictutil.placeholder(g.cfg.results)
    param2 = dictutil.placeholder2(g.cfg.results)

    print(f"\n  --> in: {input_args.split()} out: {param2}")
    assert param2.get("player_name") == player_name
    assert param2.get("player_list") == player_list
    assert param2.get("competition_list") == competition_list
    assert param1.get("player_name") == param2.get("player_name")
    assert param1.get("player_list") == param2.get("player_list")
    assert param1.get("competition_list") == param2.get("competition_list")


@pytest.mark.parametrize(
    "input_args, player_name, player_list, competition_list",
    list(param_data.name_test_case_01.values()),
    ids=list(param_data.name_test_case_01.keys())
)
def test_player_check(input_args, player_name, player_list, competition_list, monkeypatch):
    """プレイヤー名"""
    monkeypatch.setattr(sys, "argv", TEST_ARGS)
    configuration.setup()

    g.msg.argument = input_args.split()
    # param1 = dictutil.placeholder(g.cfg.results)
    param2 = dictutil.placeholder2(g.cfg.results)

    print(f"\n  --> in: {input_args.split()} out: {param2}")
    assert param2.get("player_name") == player_name
    assert param2.get("player_list") == player_list
    assert param2.get("competition_list") == competition_list
    # assert param1.get("player_name") == param2.get("player_name")
    # assert param1.get("player_list") == param2.get("player_list")
    # assert param1.get("competition_list") == param2.get("competition_list")
