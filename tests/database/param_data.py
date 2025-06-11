"""
テスト用パラメータ
"""

from typing import Any, Tuple

# ユーザ追加
user_add_case_01: dict[str, Tuple[Any, ...]] = {
    # username, ret_meg, registered
    "append 01": ("めんばー１", "登録しました", True),
    "append 02": ("めんばー２", "登録しました", True),
    "unregistered member alias": ("めんばー３ 三人目", "登録されていません", False),
    "duplication": ("宮永咲", "存在するメンバー", True),
    "same team": ("清澄高校", "存在するチーム", False),
    "invalid char": ("***", "使用できない記号", False),
    "long name": ("a" * 100, "登録可能文字数", False),
    "guest(kana)": ("ゲスト", "使用できない名前", True),
    "guest(hira)": ("げすと", "使用できない名前", False),
    "guest(mix)": ("げスと", "使用できない名前", False),
    "defined range word": ("今月", "検索範囲指定に使用される単語", False),
    "defined option word": ("ゲスト無効", "オプションに使用される単語", False),
}
