"""
テスト用パラメータ
"""

from typing import Any


# チャンネル内呼び出しキーワードデフォルト値
command_word_default: dict[str, tuple[Any, ...]] = {
    # parameter, default_word
    "results": ("results", "麻雀成績"),
    "graph": ("graph", "麻雀グラフ"),
    "ranking": ("ranking", "麻雀ランキング"),
    "report": ("report", "麻雀成績レポート"),
}

# チャンネル内呼び出しキーワード設定
command_word_override: dict[str, tuple[Any, ...]] = {
    # parameter, word
    "results": ("results", "麻雀成績の別名"),
    "graph": ("graph", "麻雀グラフの別名"),
    "ranking": ("ranking", "麻雀ランキングの別名"),
    "report": ("report", "麻雀成績レポートの別名"),
    "help": ("help", "ヘルプの別名"),
}
