"""
libs/functions/tools/score_simulator.py
"""

import logging
import sqlite3
from contextlib import closing

import libs.global_value as g
from cls.types import ScoreDataDict
from libs.data import modify
from libs.functions import score


def main():
    """ポイント再計算"""
    modify.db_backup()
    detection: ScoreDataDict = {}
    with closing(sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)) as cur:
        cur.row_factory = sqlite3.Row
        rows = cur.execute("select * from result where rule_version=?;", (g.cfg.mahjong.rule_version,))
        count = 0

        for row in rows:
            tmp_dict = dict(row)
            detection["ts"] = str(row["ts"])
            detection["p1_name"] = str(tmp_dict["p1_name"])
            detection["p1_str"] = str(tmp_dict["p1_str"])
            detection["p2_name"] = str(tmp_dict["p2_name"])
            detection["p2_str"] = str(tmp_dict["p2_str"])
            detection["p3_name"] = str(tmp_dict["p3_name"])
            detection["p3_str"] = str(tmp_dict["p3_str"])
            detection["p4_name"] = str(tmp_dict["p4_name"])
            detection["p4_str"] = str(tmp_dict["p4_str"])
            detection["comment"] = str(tmp_dict["comment"])
            detection["rule_version"] = str(tmp_dict["rule_version"])
            detection = score.get_score(detection)
            cur.execute(g.sql["RESULT_UPDATE"], detection)
            count += 1

        cur.commit()
    logging.notice("recalculated: %s", count)  # type: ignore
