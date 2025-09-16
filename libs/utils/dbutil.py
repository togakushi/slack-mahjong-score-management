"""
libs/utils/dbutil.py
"""

import sqlite3

import libs.global_value as g


def get_connection() -> sqlite3.Connection:
    """DB接続共通処理

    Returns:
        sqlite3.Connection: オブジェクト
    """

    conn = sqlite3.connect(
        "file:" + g.cfg.setting.database_file,
        detect_types=sqlite3.PARSE_DECLTYPES,
        uri=True
    )
    conn.row_factory = sqlite3.Row

    return conn
