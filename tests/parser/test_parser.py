"""
tests/test_parser.py
"""

import pytest

from cls.parser import CommandParser
from tests.parser import param_data


@pytest.mark.parametrize("input_args, expected_flags", param_data.flag_test_case_01)
def test_flag_commands(input_args, expected_flags):
    """1. フラグ系テスト"""
    parser = CommandParser()
    result = parser.analysis_argument(input_args.split())
    assert result.flags == expected_flags
    assert not result.unknown
    assert not result.search_range


@pytest.mark.parametrize("input_args, expected_flags", param_data.flag_test_case_02)
def test_command_with_argument_int(input_args, expected_flags):
    """2. 引数付きコマンド(数値)"""
    parser = CommandParser()
    result = parser.analysis_argument(input_args.split())

    print(f"\n  --> in: {input_args.split()} out: {result}")
    assert result.flags == expected_flags
    assert not result.unknown
    assert not result.search_range


@pytest.mark.parametrize("input_args, expected_flags", param_data.flag_test_case_03)
def test_command_with_argument_str(input_args, expected_flags):
    """3. 引数付きコマンド(文字)"""
    parser = CommandParser()
    result = parser.analysis_argument(input_args.split())

    print(f"\n  --> in: {input_args.split()} out: {result}")
    assert result.flags == expected_flags
    assert not result.unknown
    assert not result.search_range


def test_unknown_command():
    """4. 不明なコマンド"""
    input_args = "なんだこれ"
    parser = CommandParser()
    result = parser.analysis_argument(input_args.split())

    print(f"\n  --> in: {input_args.split()} out: {result}")
    assert not result.flags
    assert result.unknown == [input_args]


def test_member_name_validation():
    """5. 名前バリデーション"""
    parser = CommandParser()
    assert "比較" not in parser.analysis_argument(["比較"]).unknown
    assert "さきこ" in parser.analysis_argument(["さきこ"]).unknown


def test_multiple_keywords():
    """6. 複数キーワード"""
    parser = CommandParser()
    result = parser.analysis_argument(["比較", "直近5", "さきこ"])
    assert result.flags["score_comparisons"] is True
    assert result.flags["target_count"] == 5
    assert result.unknown == ["さきこ"]
