"""
テスト用パラメータ
"""

from typing import Any, Tuple


message_help: dict[str, Tuple[Any, ...]] = {
    # config, keyword
    "default": ("minimal.ini", "ヘルプ"),
    "command word": ("commandword.ini", "ヘルプの別名"),
    "regex 01": ("regex.ini", "ヘルプの正規表現その１"),
    "regex 02": ("regex.ini", "ヘルプの正規表現その２"),
    "double": ("minimal.ini", "ヘルプ 未定義ワード"),
}

message_results: dict[str, Tuple[Any, ...]] = {
    # config, keyword
    "default": ("minimal.ini", "麻雀成績"),
    "command word": ("commandword.ini", "麻雀成績の別名"),
    "regex 01": ("regex.ini", "麻雀成績の正規表現その１"),
    "regex 02": ("regex.ini", "麻雀成績の正規表現その２"),
    "double": ("minimal.ini", "麻雀成績 未定義ワード"),
}

message_graph: dict[str, Tuple[Any, ...]] = {
    # config, keyword
    "default": ("minimal.ini", "麻雀グラフ"),
    "command word": ("commandword.ini", "麻雀グラフの別名"),
    "regex 01": ("regex.ini", "麻雀グラフの正規表現その１"),
    "regex 02": ("regex.ini", "麻雀グラフの正規表現その２"),
    "double": ("minimal.ini", "麻雀グラフ 未定義ワード"),
}

message_ranking: dict[str, Tuple[Any, ...]] = {
    # config, keyword
    "default": ("minimal.ini", "麻雀ランキング"),
    "command word": ("commandword.ini", "麻雀ランキングの別名"),
    "regex 01": ("regex.ini", "麻雀ランキングの正規表現その１"),
    "regex 02": ("regex.ini", "麻雀ランキングの正規表現その２"),
    "double": ("minimal.ini", "麻雀ランキング 未定義ワード"),
}

message_report: dict[str, Tuple[Any, ...]] = {
    # config, keyword
    "default": ("minimal.ini", "麻雀成績レポート"),
    "command word": ("commandword.ini", "麻雀成績レポートの別名"),
    "regex 01": ("regex.ini", "麻雀成績レポートの正規表現その１"),
    "regex 02": ("regex.ini", "麻雀成績レポートの正規表現その２"),
    "double": ("minimal.ini", "麻雀成績レポート 未定義ワード"),
}
