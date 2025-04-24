"""
tests/test_parser.py
"""

import sys

import pytest

from libs.functions import configuration
from libs.utils import dictutil
from tests.parser import param_data

TEST_ARGS = ["progname", "--config=tests/test_data/saki.ini"]


@pytest.mark.parametrize(
    "input_args, expected_flags",
    list(param_data.flag_test_case_01.values()),
    ids=list(param_data.flag_test_case_01.keys()),
)
def test_flag_commands(input_args, expected_flags, monkeypatch):
    """1. フラグ系テスト"""
    monkeypatch.setattr(sys, "argv", TEST_ARGS)

    configuration.setup()
    result = dictutil.analysis_argument(input_args.split())
    result.pop("search_range")  # 置き換え予定のメソッドで扱わない
    result.pop("unknown_command")

    print(f"\n  --> in: {input_args.split()} out: {result}")
    assert result == expected_flags


@pytest.mark.parametrize(
    "input_args, expected_flags",
    list(param_data.flag_test_case_02.values()),
    ids=list(param_data.flag_test_case_02.keys()),
)
def test_command_with_argument_int(input_args, expected_flags, monkeypatch):
    """2. 引数付きコマンド(数値)"""
    monkeypatch.setattr(sys, "argv", TEST_ARGS)

    configuration.setup()
    result = dictutil.analysis_argument(input_args.split())
    result.pop("search_range")  # 置き換え予定のメソッドで扱わない
    result.pop("unknown_command")

    print(f"\n  --> in: {input_args.split()} out: {result}")
    assert result == expected_flags


@pytest.mark.parametrize(
    "input_args, expected_flags",
    list(param_data.flag_test_case_03.values()),
    ids=list(param_data.flag_test_case_03.keys()),
)
def test_command_with_argument_str(input_args, expected_flags, monkeypatch):
    """3. 引数付きコマンド(文字)"""
    monkeypatch.setattr(sys, "argv", TEST_ARGS)

    configuration.setup()
    result = dictutil.analysis_argument(input_args.split())
    result.pop("search_range")  # 置き換え予定のメソッドで扱わない
    result.pop("unknown_command")

    print(f"\n  --> in: {input_args.split()} out: {result}")
    assert result == expected_flags


@pytest.mark.parametrize(
    "input_args, expected_flags",
    list(param_data.flag_test_case_04.values()),
    ids=list(param_data.flag_test_case_04.keys()),
)
def test_command_unknown_str(input_args, expected_flags, monkeypatch):
    """4. 不明なコマンド"""
    monkeypatch.setattr(sys, "argv", TEST_ARGS)

    configuration.setup()
    result = dictutil.analysis_argument(input_args.split())
    result.pop("search_range")  # 置き換え予定のメソッドで扱わない
    result.pop("unknown_command")

    print(f"\n  --> in: {input_args.split()} out: {result}")
    assert result == expected_flags


@pytest.mark.parametrize(
    "input_args, expected_flags",
    list(param_data.flag_test_case_05.values()),
    ids=list(param_data.flag_test_case_05.keys()),
)
def test_command_date_range_str(input_args, expected_flags, monkeypatch):
    """5. 日付"""
    monkeypatch.setattr(sys, "argv", TEST_ARGS)

    configuration.setup()
    result = dictutil.analysis_argument(input_args.split())
    result.pop("search_range")  # 置き換え予定のメソッドで扱わない
    result.pop("unknown_command")

    print(f"\n  --> in: {input_args.split()} out: {result}")
    assert not result == expected_flags
