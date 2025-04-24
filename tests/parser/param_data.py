"""
テスト用パラメータ
"""

from cls.timekit import ExtendedDatetime as ExtDt


# フラグ更新
flag_test_case_01 = {
    "guest": ("ゲストなし", {"guest_skip": False, "guest_skip2": False, "unregistered_replace": True}),
    "score comparisons": ("比較", {"score_comparisons": True}),
    "ratings": ("ratings", {"rating": True}),
    "individual": ("個人", {"individual": True}),
    "team": ("チーム", {"individual": False}),
    "individual (over ride)": ("チーム 個人", {"individual": True}),
    "team (over ride)": ("個人 チーム", {"individual": False}),
}

# 数値引数
flag_test_case_02 = {
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
flag_test_case_03 = {
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
flag_test_case_04 = {
    "undefined 01": ("未定義01", ["未定義01"]),
    "undefined 02": ("未定義02 未定義03", ["未定義02", "未定義03"]),
}

# 日付
flag_test_case_05 = {
    "keyword": ("今月", ExtDt.range("今月").format("sql")),
    "number only": ("20250101", ExtDt("20250101").format("sql")),
    "hyphen delimiter": ("2025-01-01", ExtDt("20250101").format("sql")),
    "slash delimiter": ("2025/01/01", ExtDt("20250101").format("sql")),
    "dot delimiter": ("2025.01.01", ExtDt("20250101").format("sql")),
}

# プレイヤーテスト
name_test_case_01 = {
    # input_args, player_name, player_list, competition_list
    # --- 半角数字→全角数字
    "Half -> Full": ("未定義01", "未定義０１", {"player_0": "未定義０１"}, {}),
    # --- 序列の維持
    "keep order 01": ("名前あ 名前い 名前う", "名前あ", {"player_0": "名前あ", "player_1": "名前い", "player_2": "名前う"}, {"competition_1": "名前い", "competition_2": "名前う"}),
    "keep order 02": ("名前い 名前う 名前あ", "名前い", {"player_0": "名前い", "player_1": "名前う", "player_2": "名前あ"}, {"competition_1": "名前う", "competition_2": "名前あ"}),
    "keep order 03": ("名前う 名前あ 名前い", "名前う", {"player_0": "名前う", "player_1": "名前あ", "player_2": "名前い"}, {"competition_1": "名前あ", "competition_2": "名前い"}),
    # --- 重複パターン
    "duplication 01": ("名前あ 名前あ 名前い", "名前あ", {"player_0": "名前あ", "player_1": "名前い"}, {"competition_1": "名前い"}),
    "duplication 02": ("名前う 名前あ 名前う", "名前う", {"player_0": "名前う", "player_1": "名前あ"}, {"competition_1": "名前あ"}),
}

# フラグ更新コマンドテスト
command_test_case_01 = {
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
    "all target": ("全員 all", "", {}, {}),
    "individual": ("個人 個人成績", "", {}, {}),
    "team": ("チーム チーム成績 team", "", {}, {}),
    "friendly fire": ("チーム同卓あり コンビあり 同士討ち チーム同卓なし コンビなし", "", {}, {}),
    "guest": ("ゲストあり ゲストなし ゲスト無効", "", {}, {}),
    "anonymous": ("匿名 anonymous", "", {}, {}),
}
