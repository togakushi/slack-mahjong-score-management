"""slack連携

- `integrations.slack.adapter`: 抽象クラス
- `integrations.slack.api`: slack api
- `integrations.slack.functions`: slack専用関数群
- `integrations.slack.comparison`: 突合処理
"""

from integrations.slack import adapter, parser

__all__ = ["adapter", "parser"]
