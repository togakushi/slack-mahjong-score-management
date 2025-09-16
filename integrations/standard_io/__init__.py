"""
標準出力

- `integrations.standard_io.adapter`: 操作具体クラス
- `integrations.standard_io.parser`: メッセージ解析クラス
- `integrations.standard_io.functions`: 専用関数群
- `integrations.standard_io.config`: 個別設定
"""

from integrations.standard_io import adapter, config, parser

__all__ = ["adapter", "config", "parser"]
