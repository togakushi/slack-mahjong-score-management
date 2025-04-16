"""情報取得モジュール

Exports:
    - api: slack_apiを使用
    - db: DBから取得
    - internal: 内部辞書から取得
    - textdata: プレーンテキスト形式で取得(slackポスト用)
"""

from . import api, db, internal, textdata

__all__ = ["api", "db", "internal", "textdata"]
