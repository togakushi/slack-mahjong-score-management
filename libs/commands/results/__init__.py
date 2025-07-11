"""成績集計モジュール

Exports:
- `libs.commands.results.detail`: 個人/チーム成績詳細集計
- `libs.commands.results.summary`: 成績サマリ集計
- `libs.commands.results.versus`: 直接対戦成績集計
"""

from libs.commands.results import detail, summary, versus

__all__ = ["detail", "summary", "versus"]
