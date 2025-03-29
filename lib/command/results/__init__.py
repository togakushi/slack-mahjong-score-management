"""成績集計モジュール

Exports:
- slackpost
- detail
- ranking
- rating
- summary
- versus
"""

from lib.command.results import detail, ranking, rating, slackpost, summary, versus

__all__ = ["detail", "ranking", "rating", "slackpost", "summary", "versus"]
