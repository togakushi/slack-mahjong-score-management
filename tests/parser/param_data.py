"""
テスト用パラメータ
"""

from cls.timekit import ExtendedDatetime as ExtDt


# フラグ更新
flag_test_case_01 = [
    ("ゲストなし", {"guest_skip": False, "guest_skip2": False, "unregistered_replace": True}),
    ("比較", {"score_comparisons": True}),
    ("ratings", {"rating": True}),
]

flag_test_ids_01 = [
    "guest_skip",
    "score_comparisons",
    "ratings",
]

# 数値引数
flag_test_case_02 = [
    ("トップ0", {"ranked": 0}),
    ("上位5", {"ranked": 5}),
    ("top10", {"ranked": 10}),
    ("top", {}),

    ("規定数0", {"stipulated": 0}),
    ("規定打数10", {"stipulated": 10}),

    ("直近0", {"target_count": 0}),
    ("直近10", {"target_count": 10}),
    ("上位3 規定数20", {"stipulated": 20, "ranked": 3, }),
    ("区切25", {"interval": 25}),
]

# 文字列引数
flag_test_case_03 = [
    ("text", {"format": "text"}),
    ("txt", {"format": "txt"}),
    ("ファイル名ほげ", {"filename": "ほげ"}),
    ("ファイル名", {}),
    ("filename:hoge", {"filename": "hoge"}),
    ("filename:***", {}),
    ("ルール９９９", {"rule_version": "９９９"}),
    ("ルール0", {"rule_version": "0"}),
    ("コメントひらがな", {"search_word": "%ひらがな%"}),
    ("こめんとかたかな", {"search_word": "%カタカナ%"}),
    ("コメント数字９９９", {"search_word": "%数字９９９%"}),
]

# 未定義
flag_test_case_04 = [
    ("未定義01", ["未定義01"]),
    ("未定義02 未定義03", ["未定義02", "未定義03"]),
]

# 日付
flag_test_case_05 = [
    ("今月", ExtDt.range("今月").format("sql")),
    ("20250101", ExtDt("20250101").format("sql")),
    ("2025-01-01", ExtDt("20250101").format("sql")),
    ("2025/01/01", ExtDt("20250101").format("sql")),
    ("2025.01.01", ExtDt("20250101").format("sql")),]
