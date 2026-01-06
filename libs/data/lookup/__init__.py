"""情報取得モジュール

Exports:
    - `libs.data.lookup.db`: DBから取得
    - `libs.data.lookup.internal`: 内部辞書から取得
"""

from libs.data.lookup import db, internal

__all__ = ["db", "internal"]
