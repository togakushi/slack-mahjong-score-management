"""成績集計モジュール

Exports:
- `libs.commands.results.detail`: 個人/チーム成績詳細集計
- `libs.commands.results.ranking`: ランキング集計
- `libs.commands.results.rating`: レーティング集計
- `libs.commands.results.summary`: 成績サマリ集計
- `libs.commands.results.versus`: 直接対戦成績集計
"""

from . import detail, ranking, rating, summary, versus

__all__ = ["detail", "ranking", "rating", "summary", "versus"]
