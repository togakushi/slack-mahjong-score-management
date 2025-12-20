"""
tests/config/test_config.py
"""

import sys

import pytest

import libs.global_value as g
from libs import configuration


def test_empty_config(monkeypatch):
    """空設定チェック"""
    monkeypatch.setattr(sys, "argv", ["progname", "--config=tests/testdata/empty.ini"])
    with pytest.raises(SystemExit) as e:
        configuration.setup()
    assert e.type is SystemExit
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
    assert "download" in g.cfg.alias.download
    assert "member" in g.cfg.alias.member
    assert "add" in g.cfg.alias.add
    assert "del" in g.cfg.alias.delete


@pytest.mark.parametrize("input_args", ["results", "graph", "ranking", "report"])
def test_subcommand_default(input_args, monkeypatch):
    """サブコマンドデフォルト値チェック"""
    monkeypatch.setattr(sys, "argv", ["progname", "--config=tests/testdata/minimal.ini"])

    # fixme
    _ = input_args
    configuration.setup()
