"""
テスト用パラメータ
"""

from typing import Any, Tuple

from cls.timekit import ExtendedDatetime as ExtDt

# フラグ更新
flag_test_case_01: dict[str, Tuple[Any, ...]] = {
    # input_args, expected_flags
    "guest": ("ゲストなし", {"guest_skip": False, "guest_skip2": False, "unregistered_replace": True}),
    "score comparisons": ("比較", {"score_comparisons": True}),
    "ratings": ("ratings", {"rating": True}),
    # --- 個人戦/チーム戦切替
    "individual": ("個人", {"individual": True}),
    "team": ("チーム", {"individual": False}),
    # --- 上書きチェック
    "individual (over ride)": ("チーム 個人", {"individual": True}),
    "team (over ride)": ("個人 チーム", {"individual": False}),
}

# 数値引数
flag_test_case_02: dict[str, Tuple[Any, ...]] = {
    "ranked 0 (kata)": ("トップ0", {"ranked": 0}),
    "ranked 5 (kan)": ("上位5", {"ranked": 5}),
    "ranked 10 (alp)": ("top10", {"ranked": 10}),
    "ranked NaN": ("top", {}),

    "stipulated 0": ("規定数0", {"stipulated": 0}),
    "stipulated 10": ("規定打数10", {"stipulated": 10}),

    "target_count 0": ("直近0", {"target_count": 0}),
    "target_count 10": ("直近10", {"target_count": 10}),
    "stipulated & ranked": ("上位3 規定数20", {"stipulated": 20, "ranked": 3, }),
    "over ride": ("top10 top20 top30", {"ranked": 30}),
    "interval 25": ("区切25", {"interval": 25}),
}

# 文字列引数
flag_test_case_03: dict[str, Tuple[Any, ...]] = {
    "format type (text)": ("text", {"format": "text"}),
    "format type (txt)": ("txt", {"format": "txt"}),
    "format type (CSV)": ("CSV", {"format": "csv"}),
    "filename (full)": ("ファイル名ほげ", {"filename": "ほげ"}),
    "filename (half)": ("filename:hoge", {"filename": "hoge"}),
    "filename (empty)": ("ファイル名", {}),
    "filename (invalid)": ("filename:***", {}),
    "rule version (full)": ("ルール９９９", {"rule_version": "９９９"}),
    "rule version (half)": ("ルール0", {"rule_version": "0"}),
    "comment (hira)": ("コメントひらがな", {"search_word": "%ひらがな%"}),
    "comment (kata)": ("こめんとかたかな", {"search_word": "%カタカナ%"}),
    "comment (num)": ("コメント数字９９９", {"search_word": "%数字９９９%"}),
}

# 未定義
flag_test_case_04: dict[str, Tuple[Any, ...]] = {
    "undefined 01": ("未定義01", ["未定義01"]),
    "undefined 02": ("未定義02 未定義03", ["未定義02", "未定義03"]),
    "undefined Full Char": ("未定義０４", ["未定義０４"]),
}

# 日付
flag_test_case_05: dict[str, Tuple[Any, ...]] = {
    "keyword": ("今月", ExtDt.range("今月").format("sql")),
    "number only": ("20250101", ExtDt("20250101").format("sql")),
    "hyphen delimiter": ("2025-01-01", ExtDt("20250101").format("sql")),
    "slash delimiter": ("2025/01/01", ExtDt("20250101").format("sql")),
    "dot delimiter": ("2025.01.01", ExtDt("20250101").format("sql")),
}

# プレイヤーテスト
name_test_case_01: dict[str, Tuple[Any, ...]] = {
    # input_args, player_name, player_list, competition_list
    # --- 序列の維持
    "keep order 01": ("名前あ 名前い 名前う", "名前あ", {"player_0": "名前あ", "player_1": "名前い", "player_2": "名前う"}, {"competition_1": "名前い", "competition_2": "名前う"}),
    "keep order 02": ("名前い 名前う 名前あ", "名前い", {"player_0": "名前い", "player_1": "名前う", "player_2": "名前あ"}, {"competition_1": "名前う", "competition_2": "名前あ"}),
    "keep order 03": ("名前う 名前あ 名前い", "名前う", {"player_0": "名前う", "player_1": "名前あ", "player_2": "名前い"}, {"competition_1": "名前あ", "competition_2": "名前い"}),
    # --- 重複パターン
    "duplication 01": ("名前あ 名前あ 名前い", "名前あ", {"player_0": "名前あ", "player_1": "名前い"}, {"competition_1": "名前い"}),
    "duplication 02": ("名前う 名前あ 名前う", "名前う", {"player_0": "名前う", "player_1": "名前あ"}, {"competition_1": "名前あ"}),
}

# チーム名テスト
team_saki_test_case: dict[str, Tuple[Any, ...]] = {
    # input_args, player_name, player_list, competition_list
    "case 01": ("チーム 清澄高校", "清澄高校", {'player_0': "清澄高校"}, {}),
    "case 02": ("チーム 清澄高校 宮永咲", "清澄高校", {'player_0': "清澄高校"}, {}),
    "case 03": ("チーム 宮永咲 清澄高校", "清澄高校", {'player_0': "清澄高校"}, {}),
}

# ゲストテスト
guest_test_case: dict[str, Tuple[Any, ...]] = {
    # input_args, player_name, replace_name
    "case 1-01": ("ゲストあり 名前あ", "名前あ", "ゲスト"),
    "case 1-02": ("ゲストあり 宮永咲", "宮永咲", "宮永咲"),
    "case 1-03": ("ゲストあり 清澄高校", "原村和", "原村和"),
    "case 2-01": ("ゲスト無効 名前あ", "名前あ", "名前あ"),
    "case 2-02": ("ゲスト無効 宮永咲", "宮永咲", "宮永咲"),
    "case 2-03": ("ゲスト無効 清澄高校", "原村和", "原村和"),
    "case team 1-01": ("チーム ゲストあり 清澄高校", "清澄高校", "清澄高校"),
    "case team 1-02": ("チーム ゲストあり 清澄高校 宮永咲", "清澄高校", "清澄高校"),
    "case team 1-03": ("チーム ゲストあり 宮永咲 清澄高校", "清澄高校", "清澄高校"),

}

# フラグ更新コマンドテスト
command_test_case_01: dict[str, Tuple[Any, ...]] = {
    # input_args, player_name, player_list, competition_list
    # --- フラグ更新コマンドが誤って認識されていないか
    "verbose": ("詳細 verbose", "", {}, {}),
    "versus": ("対戦 対戦結果", "", {}, {}),
    "results": ("戦績", "", {}, {}),
    "statistics": ("統計", "", {}, {}),
    "most recent": ("直近", "", {}, {}),
    "score comparisons": ("比較 点差 差分", "", {}, {}),
    "interval": ("期間 区間 区切リ 区切 interval", "", {}, {}),
    "rating": ("rate rating ratings レート レーティング", "", {}, {}),
    "collecting": ("daily monthly yearly デイリー マンスリー イヤーリー 日次 月次 年次 全体", "", {}, {}),
    "format type": ("csv text txt", "", {}, {}),
    "filename": ("filename:ほげ ファイル名ふが", "", {}, {}),
    "comment": ("コメントふー commentばー 集約", "", {}, {}),
    "ranked": ("トップ 上位 top", "", {}, {}),
    "stipulated": ("規定数 規定打数", "", {}, {}),
    "rule": ("ルール rule", "", {}, {}),
    "order": ("順位", "", {}, {}),
    "individual": ("個人 個人成績", "", {}, {}),
    "team": ("チーム チーム成績 team", "", {}, {}),
    "friendly fire": ("チーム同卓あり コンビあり 同士討ち チーム同卓なし コンビなし", "", {}, {}),
    "guest": ("ゲストあり ゲストなし ゲスト無効", "", {}, {}),
    "anonymous": ("匿名 anonymous", "", {}, {}),
}

# 検索日付範囲
search_range: dict[str, Tuple[Any, ...]] = {
    # keyword, [start, end]
    "1 day": ("20250101", [ExtDt("2025-01-01 12:00:00.000000"), ExtDt("2025-01-02 11:59:59.999999")]),
    "2 days": ("20250101 20250102", [ExtDt("2025-01-01 12:00:00.000000"), ExtDt("2025-01-03 11:59:59.999999")]),
    "today": ("今日", (ExtDt().range("今日") + {"hours": 12}).period),
    "yesterday": ("昨日", (ExtDt().range("昨日") + {"hours": 12}).period),
    "single word": ("今月", ExtDt().range("今月") + {"hours": 12}),
    "double words": ("今月 先月", (ExtDt().range("今月 先月") + {"hours": 12}).period),
    "triple words": ("20250301 20250301 20250101", [ExtDt("2025-01-01 12:00:00.000000"), ExtDt("2025-03-02 11:59:59.999999")]),
    "mix words": ("20250101 今月", [ExtDt("2025-01-01 12:00:00.000000"), ExtDt().range("今月")[1] + {"hours": 12}]),
    "inclusive": ("今月 先月 今年", ExtDt().range("今年") + {"hours": 12}),
    "duplication": ("今月 先月 今月", (ExtDt().range("今月 先月") + {"hours": 12}).period),
}
