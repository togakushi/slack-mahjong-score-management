"""
tests/test_parser.py
"""

import sys

import pytest

from libs.functions import configuration
from libs.utils import dictutil
from tests.parser import parameter

TEST_ARGS = ["progname", "--config=tests/test_data/saki.ini"]


@pytest.mark.parametrize("input_args, expected_flags", parameter.flag_test_case_01, ids=parameter.flag_test_ids_01)
def test_flag_commands(input_args, expected_flags, monkeypatch):
    """1. フラグ系テスト"""
    monkeypatch.setattr(sys, "argv", TEST_ARGS)

    configuration.setup()
    result = dictutil.analysis_argument(input_args.split())
    result.pop("search_range")  # 置き換え予定のメソッドで扱わない
    result.pop("unknown_command")

    print(f"\n  --> in: {input_args.split()} out: {result}")
    assert result == expected_flags


@pytest.mark.parametrize("input_args, expected_flags", parameter.flag_test_case_02)
def test_command_with_argument_int(input_args, expected_flags, monkeypatch):
    """2. 引数付きコマンド(数値)"""
    monkeypatch.setattr(sys, "argv", TEST_ARGS)

    configuration.setup()
    result = dictutil.analysis_argument(input_args.split())
    result.pop("search_range")  # 置き換え予定のメソッドで扱わない
    result.pop("unknown_command")

    print(f"\n  --> in: {input_args.split()} out: {result}")
    assert result == expected_flags


@pytest.mark.parametrize("input_args, expected_flags", parameter.flag_test_case_03)
def test_command_with_argument_str(input_args, expected_flags, monkeypatch):
    """3. 引数付きコマンド(文字)"""
    monkeypatch.setattr(sys, "argv", TEST_ARGS)

    configuration.setup()
    result = dictutil.analysis_argument(input_args.split())
    result.pop("search_range")  # 置き換え予定のメソッドで扱わない
    result.pop("unknown_command")

    print(f"\n  --> in: {input_args.split()} out: {result}")
    assert result == expected_flags
