"""
lib/function/tools/vacuum.py
"""

import logging
import os
import sqlite3
from contextlib import closing

import lib.global_value as g
from lib.data import modify


def main():
    """vacuum実行"""
    modify.db_backup()
    before_size = os.path.getsize(g.cfg.db.database_file)

    with closing(sqlite3.connect(g.cfg.db.database_file)) as cur:
        before_page = db_info(cur, "page_count")
        before_freelist = db_info(cur, "freelist_count")
        cur.execute("vacuum;")
        after_page = db_info(cur, "page_count")
        after_freelist = db_info(cur, "freelist_count")

    after_size = os.path.getsize(g.cfg.db.database_file)

    logging.notice("file size: %s -> %s", before_size, after_size)  # type: ignore
    logging.notice("page_count: %s -> %s", before_page, after_page)  # type: ignore
    logging.notice("freelist_count: %s -> %s", before_freelist, after_freelist)  # type: ignore


def db_info(cur, kind):
    """page_countを取得

    Args:
        cur (sqlite3.Cursor): カーソルオブジェクト
        kind (str): 取得する内容

    Returns:
        int: page_count / freelist_count
    """

    match kind:
        case "page_count":
            count = cur.execute("pragma page_count;").fetchone()[0]
        case "freelist_count":
            count = cur.execute("pragma freelist_count;").fetchone()[0]
        case _:
            count = 0

    return (count)
