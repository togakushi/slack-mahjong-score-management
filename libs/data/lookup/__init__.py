"""情報取得モジュール

Exports:
    - `libs.data.lookup.db`: DBから取得
    - `libs.data.lookup.internal`: 内部辞書から取得
    - `libs.data.lookup.textdata`: プレーンテキスト形式で取得(slackポスト用)
"""

from libs.data.lookup import db, internal, textdata

__all__ = ["db", "internal", "textdata"]
