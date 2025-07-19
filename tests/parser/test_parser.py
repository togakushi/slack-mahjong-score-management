"""
tests/test_parser.py
"""

import sys

import pytest

import libs.global_value as g
from cls.command import CommandParser
from integrations import factory
from libs.functions import configuration
from libs.utils import dictutil
from tests.parser import param_data

TEST_ARGS = ["progname", "--config=tests/test_data/saki.ini"]


@pytest.mark.parametrize(
    "input_args, expected_flags",
    list(param_data.flag_test_case_01.values()),
    ids=list(param_data.flag_test_case_01.keys()),
)
def test_flag_commands(input_args, expected_flags):
    """1. フラグ系テスト"""
    parser = CommandParser()
    result = parser.analysis_argument(input_args.split())
    assert result.flags == expected_flags
    assert not result.unknown
    assert not result.search_range


@pytest.mark.parametrize(
    "input_args, expected_flags",
    list(param_data.flag_test_case_02.values()),
    ids=list(param_data.flag_test_case_02.keys()),
)
def test_command_with_argument_int(input_args, expected_flags):
    """2. 引数付きコマンド(数値)"""
    parser = CommandParser()
    result = parser.analysis_argument(input_args.split())

    print(f"\n  --> in: {input_args.split()} out: {result}")
    assert result.flags == expected_flags
    assert not result.unknown
    assert not result.search_range


@pytest.mark.parametrize(
    "input_args, expected_flags",
    list(param_data.flag_test_case_03.values()),
    ids=list(param_data.flag_test_case_03.keys()),
)
def test_command_with_argument_str(input_args, expected_flags):
    """3. 引数付きコマンド(文字)"""
    parser = CommandParser()
    result = parser.analysis_argument(input_args.split())

    print(f"\n  --> in: {input_args.split()} out: {result}")
    assert result.flags == expected_flags
    assert not result.unknown
    assert not result.search_range


@pytest.mark.parametrize(
    "input_args, expected_flags",
    list(param_data.flag_test_case_04.values()),
    ids=list(param_data.flag_test_case_04.keys()),
)
def test_command_unknown_str(input_args, expected_flags):
    """4. 不明なコマンド"""
    parser = CommandParser()
    result = parser.analysis_argument(input_args.split())

    print(f"\n  --> in: {input_args.split()} out: {result}")
    assert not result.flags
    assert result.unknown == expected_flags
    assert not result.search_range


@pytest.mark.parametrize(
    "input_args, expected_flags",
    list(param_data.flag_test_case_05.values()),
    ids=list(param_data.flag_test_case_05.keys()),
)
def test_command_date_range_str(input_args, expected_flags):
    """5. 日付"""
    parser = CommandParser()
    result = parser.analysis_argument(input_args.split())

    print(f"\n  --> in: {input_args.split()} out: {result}")
    assert not result.flags
    assert not result.unknown
    assert not result.search_range == expected_flags


@pytest.mark.parametrize(
    "keyword, search_range",
    list(param_data.search_range.values()),
    ids=list(param_data.search_range.keys())
)
def test_search_range(keyword, search_range, monkeypatch):
    """検索範囲"""
    monkeypatch.setattr(sys, "argv", TEST_ARGS)
    configuration.setup()
    m = factory.select_parser("test")
    m.parser({"event": {"text": keyword}})

    ret_range = [v for k, v in dictutil.placeholder(g.cfg.results, m).items() if k in ["starttime", "endtime"]]

    print(f"\n  --> in: {keyword.split()} out: {ret_range}")
    assert ret_range == search_range
