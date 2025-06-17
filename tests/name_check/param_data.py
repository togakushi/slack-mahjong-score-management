"""
テスト用パラメータ
"""

from typing import Any

# 名前チェック
flag_name_pattern_01: dict[str, tuple[Any, ...]] = {
    # input_args, expected_flags
    "kana": ("カタカナ", True),
    "hira": ("ひらがな", True),
    "alphabet": ("ｘｙｚ", True),
}

flag_name_pattern_02: dict[str, tuple[Any, ...]] = {
    # input_args, expected_flags
    "guest kana": ("ゲスト", False),
    "guest hira": ("げすと", False),
    "guest mix": ("げスと", False),
    "prohibited character 01": ("<名前>", False),
    "prohibited character 02": ("****", False),
    "over number": ("0123456789", False),
    "registered name 01": ("宮永咲", False),
    "registered name 02": ("宮永咲ちゃん", False),
    "registered team": ("清澄高校", False),
}
