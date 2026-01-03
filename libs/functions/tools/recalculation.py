"""
libs/functions/tools/recalculation.py
"""

import logging
from contextlib import closing

import libs.global_value as g
from cls.score import GameResult
from libs.data import modify
from libs.utils import dbutil, dictutil


def main():
    """ポイント再計算"""

    g.cfg.initialization()

    modify.db_backup()

    with closing(dbutil.connection(g.cfg.setting.database_file)) as cur:
        for rule_version, rule_set in g.cfg.rule.data.items():
            logging.info("%s", rule_set)
            rows = cur.execute(
                """
                select
                    ts,
                    p1_name, p1_str,
                    p2_name, p2_str,
                    p3_name, p3_str,
                    p4_name, p4_str,
                    comment,
                    rule_version
                    from result where rule_version=?;
                """,
                (rule_version,),
            )
            count = 0

            for row in rows:
                dictutil.merge_dicts(dict(row), g.cfg.rule.to_dict(rule_version))
                result = GameResult(**dictutil.merge_dicts(dict(row), g.cfg.rule.to_dict(rule_version)))
                cur.execute(dbutil.query("RESULT_UPDATE"), result.to_dict())
                count += 1
            logging.info("recalculated: %s", count)

        cur.commit()
