"""
テスト用パラメータ
"""

# フラグ更新
flag_test_case_01 = [
    ("ゲストナシ", {"guest_skip": False, "guest_skip2": False, "unregistered_replace": True}),
    ("比較", {"score_comparisons": True}),

]

flag_test_ids_01 = [
    "guest_skip",
    "score_comparisons",
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
]

# 文字列引数
flag_test_case_03 = [
    ("text", {"format": "text"}),
    ("txt", {"format": "txt"}),
    ("ファイル名ほげ", {"filename": "ホゲ"}),
    ("ファイル名", {}),
    ("filename:hoge", {"filename": "hoge"}),
]
