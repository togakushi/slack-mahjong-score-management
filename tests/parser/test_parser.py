# tests/test_parser.py

import pytest

from cls.parser import CommandParser
from tests.parser import parameter


# 1. フラグ系テスト
@pytest.mark.parametrize("input_args, expected_flags", parameter.flag_test_case_01)
def test_flag_commands(input_args, expected_flags):
    parser = CommandParser()
    result = parser.parse_user_input(input_args.split())
    assert result.flags == expected_flags
    assert result.unknown == []


# 2. 引数付きコマンド(数値)
@pytest.mark.parametrize("input_args, expected_flags", parameter.flag_test_case_02)
def test_command_with_argument_int(input_args, expected_flags):
    parser = CommandParser()
    result = parser.parse_user_input(input_args.split())

    print(f"\n  --> in: {input_args.split()} out: {result}")
    assert result.flags == expected_flags


# 3. 引数付きコマンド(文字)
@pytest.mark.parametrize("input_args, expected_flags", parameter.flag_test_case_03)
def test_command_with_argument_str(input_args, expected_flags):
    parser = CommandParser()
    result = parser.parse_user_input(input_args.split())

    print(f"\n  --> in: {input_args.split()} out: {result}")
    assert result.flags == expected_flags


# 4. 不明なコマンド
def test_unknown_command():
    input_args = "なんだこれ"
    parser = CommandParser()
    result = parser.parse_user_input(input_args.split())

    print(f"\n  --> in: {input_args.split()} out: {result}")
    assert result.flags == {}
    assert result.unknown == [input_args]


# 5. 名前バリデーション
def test_member_name_validation():
    parser = CommandParser()
    assert "比較" not in parser.parse_user_input(["比較"]).unknown
    assert "さきこ" in parser.parse_user_input(["さきこ"]).unknown


# 6. 複数キーワード
def test_multiple_keywords():
    parser = CommandParser()
    result = parser.parse_user_input(["比較", "直近5", "さきこ"])
    assert result.flags["score_comparisons"] is True
    assert result.flags["target_count"] == 5
    assert result.unknown == ["さきこ"]
