"""
tests/config/test_keyword.py
"""

import sys
from typing import cast

import pytest

import libs.global_value as g
from cls.config import SubCommand
from libs.functions import configuration
from tests.config import param_data


@pytest.mark.parametrize(
    "parameter, config, word",
    list(param_data.keyword_test.values()),
    ids=list(param_data.keyword_test.keys()),
)
def test_keyword(parameter, config, word, monkeypatch):
    """呼び出しキーワード取り込みチェック"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    configuration.setup()

    conf = cast(SubCommand, getattr(g.cfg, parameter, ""))
    assert word in conf.commandword


@pytest.mark.parametrize(
    "config, word",
    list(param_data.help_word.values()),
    ids=list(param_data.help_word.keys()),
)
def test_help(config, word, monkeypatch):
    """ヘルプキーワード取り込みチェック"""
    monkeypatch.setattr(sys, "argv", ["progname", f"--config=tests/testdata/{config}"])
    configuration.setup()

    assert g.cfg.setting.help == word
