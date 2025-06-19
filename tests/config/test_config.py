"""
tests/test_parser.py
"""

import sys

import pytest

import libs.global_value as g
from cls.config import SubCommand
from libs.functions import configuration
from tests.config import param_data


def test_empty_config(monkeypatch):
    """空設定チェック"""
    monkeypatch.setattr(sys, "argv", ["progname", "--config=tests/testdata/empty.ini"])
    with pytest.raises(SystemExit) as e:
        configuration.setup()
    assert e.type == SystemExit
    assert e.value.code == 255


def test_minimal_config(monkeypatch):
    """最小構成"""
    monkeypatch.setattr(sys, "argv", ["progname", "--config=tests/testdata/minimal.ini"])
    configuration.setup()

    assert g.cfg.mahjong.origin_point == 250
    assert g.cfg.mahjong.return_point == 300

    # default alias
    assert "results" in g.cfg.alias.results
    assert "graph" in g.cfg.alias.graph
    assert "ranking" in g.cfg.alias.ranking
    assert "report" in g.cfg.alias.report
    assert "check" in g.cfg.alias.check
    assert "download" in g.cfg.alias.download
    assert "member" in g.cfg.alias.member
    assert "add" in g.cfg.alias.add
    assert "delete" in g.cfg.alias.delete


@pytest.mark.parametrize(
    "input_args",
    ["results", "graph", "ranking", "report"]
)
def test_subcommand_default(input_args, monkeypatch):
    """サブコマンドデフォルト値チェック"""
    monkeypatch.setattr(sys, "argv", ["progname", "--config=tests/testdata/minimal.ini"])

    configuration.setup()

    test_subcommand = getattr(g.cfg, input_args)
    assert test_subcommand.aggregation_range == SubCommand.aggregation_range
    assert test_subcommand.individual == SubCommand.individual
    assert test_subcommand.all_player == SubCommand.all_player
    assert test_subcommand.daily == SubCommand.daily
    assert test_subcommand.fourfold == SubCommand.fourfold
    assert test_subcommand.game_results == SubCommand.game_results
    assert test_subcommand.guest_skip == SubCommand.guest_skip
    assert test_subcommand.guest_skip2 == SubCommand.guest_skip2
    assert test_subcommand.ranked == SubCommand.ranked
    assert test_subcommand.score_comparisons == SubCommand.score_comparisons
    assert test_subcommand.statistics == SubCommand.statistics
    assert test_subcommand.stipulated == SubCommand.stipulated
    assert test_subcommand.stipulated_rate == SubCommand.stipulated_rate
    assert test_subcommand.unregistered_replace == SubCommand.unregistered_replace
    assert test_subcommand.anonymous == SubCommand.anonymous
    assert test_subcommand.verbose == SubCommand.verbose
    assert test_subcommand.versus_matrix == SubCommand.versus_matrix
    assert test_subcommand.collection == SubCommand.collection
    assert test_subcommand.search_word == SubCommand.search_word
    assert test_subcommand.group_length == SubCommand.group_length
    # assert test_subcommand.always_argument == SubCommand.always_argument


@pytest.mark.parametrize(
    "parameter, default_word",
    list(param_data.command_word_default.values()),
    ids=list(param_data.command_word_default.keys()),
)
def test_command_word_default(parameter, default_word, monkeypatch):
    """チャンネル内呼び出しキーワードデフォルト値チェック"""
    monkeypatch.setattr(sys, "argv", ["progname", "--config=tests/testdata/minimal.ini"])
    configuration.setup()

    assert getattr(g.cfg.cw, parameter, "") == default_word


@pytest.mark.parametrize(
    "parameter, word",
    list(param_data.command_word_override.values()),
    ids=list(param_data.command_word_override.keys()),
)
def test_command_word_override(parameter, word, monkeypatch):
    """チャンネル内呼び出しキーワード設定値チェック"""
    monkeypatch.setattr(sys, "argv", ["progname", "--config=tests/testdata/commandword.ini"])
    configuration.setup()

    assert getattr(g.cfg.cw, parameter, "") == word
