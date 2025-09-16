"""
Web出力

- `integrations.web.adapter`: 操作具体クラス
- `integrations.web.parser`: メッセージ解析クラス
- `integrations.web.config`: 個別設定
- `integrations.web.functions`: 専用関数
"""

from integrations.web import adapter, config, functions, parser

__all__ = ["adapter", "config", "functions", "parser"]
