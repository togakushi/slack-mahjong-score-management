"""
tests/test_parser.py
"""

import sys

import pytest

import libs.global_value as g
from cls.subcom import SubCommand
from libs.functions import configuration


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

    assert not g.cfg.alias.results
    assert not g.cfg.alias.graph
    assert not g.cfg.alias.ranking
    assert not g.cfg.alias.report
    assert not g.cfg.alias.check
    assert not g.cfg.alias.download
    assert not g.cfg.alias.member
    assert not g.cfg.alias.add
    assert not g.cfg.alias.delete


@pytest.mark.parametrize(
    "input_args",
    ["results", "graph", "ranking", "report"]
)
def test_config_subcommand_default(input_args, monkeypatch):
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
