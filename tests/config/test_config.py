"""
tests/test_parser.py
"""

import pytest

import libs.global_value as g
from cls.config import Config
from cls.search import SearchRange
from cls.subcom import SubCommand
from libs.functions import configuration


def test_empty_config():
    """空設定チェック"""
    with pytest.raises(RuntimeError):
        Config("./tests/testdata/empty.ini")
        raise ValueError("must be positive")


def test_minimal_config():
    """最小構成"""
    configuration.set_loglevel()
    cfg = Config("./tests/testdata/minimal.ini")

    assert cfg.mahjong.origin_point == 250
    assert cfg.mahjong.return_point == 300

    assert not cfg.alias.results
    assert not cfg.alias.graph
    assert not cfg.alias.ranking
    assert not cfg.alias.report
    assert not cfg.alias.check
    assert not cfg.alias.download
    assert not cfg.alias.member
    assert not cfg.alias.add
    assert not cfg.alias.delete



@pytest.mark.parametrize(
    "input_args",
    ["results", "graph", "ranking", "report"]
)
def test_config_subcommand_default(input_args):
    """サブコマンドデフォルト値チェック"""
    configuration.set_loglevel()
    g.cfg = Config("./tests/testdata/minimal.ini")
    g.search_word = SearchRange()

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
