import sqlite3
from contextlib import closing

import global_value as g
from lib import function as f
from lib import database as d


def main():
    """ポイント再計算
    """

    d.common.db_backup()
    with closing(sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)) as cur:
        cur.row_factory = sqlite3.Row
        rows = cur.execute("select * from result")

        for row in rows:
            detection = [
                row["p1_name"], row["p1_str"],
                row["p2_name"], row["p2_str"],
                row["p3_name"], row["p3_str"],
                row["p4_name"], row["p4_str"],
                row["comment"],
            ]
            ret = f.score.get_score(detection)
            ret["ts"] = row["ts"]
            cur.execute(d.sql_result_update, ret)

        cur.commit()
