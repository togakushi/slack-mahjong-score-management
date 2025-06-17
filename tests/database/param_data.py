"""
テスト用パラメータ
"""

from typing import Any

# ユーザ追加
user_add_case_01: dict[str, tuple[Any, ...]] = {
    # user_name, ret_meg, registered
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

# チーム追加
team_add_case_01: dict[str, tuple[Any, ...]] = {
    # team_name, ret_meg, registered
    "append 01": ("ちーむ１", "登録しました", True),
    "duplication": ("清澄高校", "存在するチーム", True),
    "same member": ("宮永咲", "存在するメンバー", False),
    "invalid char": ("***", "使用できない記号", False),
    "long name": ("a" * 100, "登録可能文字数", False),
    "defined range word": ("今月", "検索範囲指定に使用される単語", False),
    "defined option word": ("ゲスト無効", "オプションに使用される単語", False),
}

# スコア登録
score_insert_case_01: dict[str, tuple[Any, ...]] = {
    # draw split, game_result, get_point, get_rank
    "game 01": (
        False, "終局ひと250いぬ250さる250とり250",
        {"p1_point": 45.0, "p2_point": 5.0, "p3_point": -15.0, "p4_point": -35.0},
        {"p1_rank": 1, "p2_rank": 2, "p3_rank": 3, "p4_rank": 4},
    ),
    "game 02": (
        False, "終局ひと450いぬ250さる200とり100",
        {"p1_point": 65.0, "p2_point": 5.0, "p3_point": -20.0, "p4_point": -50.0},
        {"p1_rank": 1, "p2_rank": 2, "p3_rank": 3, "p4_rank": 4},
    ),
    "game 03": (
        False, "終局ひと250+480いぬ250さる250-480とり250",
        {"p1_point": 93.0, "p2_point": 5.0, "p3_point": -83.0, "p4_point": -15.0},
        {"p1_rank": 1, "p2_rank": 2, "p3_rank": 4, "p4_rank": 3},
    ),
    # 順位点山分け
    "game 01(draw split)": (
        True, "終局ひと250いぬ250さる250とり250",
        {"p1_point": 0.0, "p2_point": 0.0, "p3_point": 0.0, "p4_point": 0.0},
        {"p1_rank": 1, "p2_rank": 1, "p3_rank": 1, "p4_rank": 1},
    ),
    "game 02(draw split)": (
        True, "終局ひと310いぬ310さる310とり70",
        {"p1_point": 19.0, "p2_point": 17.0, "p3_point": 17.0, "p4_point": -53.0},
        {"p1_rank": 1, "p2_rank": 1, "p3_rank": 1, "p4_rank": 4},
    ),
    "game 03(draw split)": (
        True, "終局ひと310いぬ310さる200とり180",
        {"p1_point": 31.0, "p2_point": 31.0, "p3_point": -20.0, "p4_point": -42.0},
        {"p1_rank": 1, "p2_rank": 1, "p3_rank": 3, "p4_rank": 4},
    ),
    "game 04(draw split)": (
        True, "終局ひと300いぬ300さる200とり200",
        {"p1_point": 30.0, "p2_point": 30.0, "p3_point": -30.0, "p4_point": -30.0},
        {"p1_rank": 1, "p2_rank": 1, "p3_rank": 3, "p4_rank": 3},
    ),
    "game 05(draw split)": (
        True, "終局ひと310いぬ230さる230とり230",
        {"p1_point": 51.0, "p2_point": -17.0, "p3_point": -17.0, "p4_point": -17.0},
        {"p1_rank": 1, "p2_rank": 2, "p3_rank": 2, "p4_rank": 2},
    ),
    "game 06(draw split)": (
        True, "終局ひと300いぬ250さる250とり200",
        {"p1_point": 50.0, "p2_point": -5.0, "p3_point": -5.0, "p4_point": -40.0},
        {"p1_rank": 1, "p2_rank": 2, "p3_rank": 2, "p4_rank": 4},
    ),
    "game 07(draw split)": (
        True, "終局ひと350いぬ250さる200とり200",
        {"p1_point": 55.0, "p2_point": 5.0, "p3_point": -30.0, "p4_point": -30.0},
        {"p1_rank": 1, "p2_rank": 2, "p3_rank": 3, "p4_rank": 3},
    ),
}
