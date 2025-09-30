"""
slack連携

- `integrations.slack.events`: イベント処理
- `integrations.slack.adapter`: 操作具体クラス
- `integrations.slack.api`: インターフェースAPI
- `integrations.slack.config`: 個別設定
- `integrations.slack.parser`: メッセージ解析クラス
- `integrations.slack.functions`: 専用関数群
"""

from integrations.slack import adapter, api, config, events, functions, parser

__all__ = ["adapter", "api", "config", "events", "functions", "parser"]
