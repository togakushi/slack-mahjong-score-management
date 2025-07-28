"""
slack連携

- `integrations.slack.events`: イベント
- `integrations.slack.adapter`: AIP操作具体クラス
- `integrations.slack.api`: slack api
- `integrations.slack.parser`: メッセージ解析クラス
- `integrations.slack.functions`: slack専用関数群
- `integrations.slack.comparison`: 突合処理
"""

from integrations.slack import adapter, api, comparison, functions, parser

__all__ = ["adapter", "api", "comparison", "functions", "parser"]
