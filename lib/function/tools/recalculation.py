"""
lib/function/tools/score_simulator.py
"""

import logging
import sqlite3
from contextlib import closing

import lib.global_value as g
from lib.data import modify
from lib.function import score


def main():
    """ポイント再計算"""
    modify.db_backup()
    with closing(sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)) as cur:
        cur.row_factory = sqlite3.Row
        rows = cur.execute("select * from result where rule_version=?;", (g.cfg.mahjong.rule_version,))
        count = 0

        for row in rows:
            detection = [
                row["p1_name"], row["p1_str"],
                row["p2_name"], row["p2_str"],
                row["p3_name"], row["p3_str"],
                row["p4_name"], row["p4_str"],
                row["comment"],
            ]
            ret = score.get_score(detection)
            ret["ts"] = row["ts"]
            cur.execute(g.sql["RESULT_UPDATE"], ret)
            count += 1

        cur.commit()
    logging.notice("recalculated: %s", count)  # type: ignore
