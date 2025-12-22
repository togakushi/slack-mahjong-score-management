"""
libs/functions/tools/unification.py
"""

import configparser
import logging

import libs.global_value as g
from libs import configuration
from libs.data import modify
from libs.utils import dbutil, textutil, validator


def main():
    """ゲストメンバーの名前を統一する"""
    rename_conf = configparser.ConfigParser()
    rename_conf.read(g.args.unification, encoding="utf-8")
    configuration.read_memberslist(False)

    modify.db_backup()
    if "rename" in rename_conf.sections():
        name_table: dict = {}
        for name, alias in rename_conf["rename"].items():
            name_table.setdefault(name, [x.strip() for x in alias.split(",")])

        db = dbutil.connection(g.cfg.setting.database_file)
        for name, alias_list in name_table.items():
            count = 0
            chk, msg = validator.check_namepattern(name, "member")
            if chk:
                for alias in alias_list:
                    chk, msg = validator.check_namepattern(alias, "member")
                    if chk:
                        db.execute(
                            "update result set p1_name=? where p1_name=?;",
                            (
                                name,
                                alias,
                            ),
                        )
                        count += db.execute("select changes();").fetchone()[0]
                        db.execute(
                            "update result set p2_name=? where p2_name=?;",
                            (
                                name,
                                alias,
                            ),
                        )
                        count += db.execute("select changes();").fetchone()[0]
                        db.execute(
                            "update result set p3_name=? where p3_name=?;",
                            (
                                name,
                                alias,
                            ),
                        )
                        count += db.execute("select changes();").fetchone()[0]
                        db.execute(
                            "update result set p4_name=? where p4_name=?;",
                            (
                                name,
                                alias,
                            ),
                        )
                        count += db.execute("select changes();").fetchone()[0]
                        db.execute(
                            "update remarks set name=? where name=?;",
                            (
                                name,
                                alias,
                            ),
                        )
                        count += db.execute("select changes();").fetchone()[0]
                    else:
                        logging.warning("remove: %s -> %s (%s)", name, alias, msg)
                        alias_list.remove(alias)
                        continue
                logging.info("rename: %s -> %s changed: %s", alias_list, name, count)
            else:
                logging.warning("skip: %s (%s)", name, msg)
                continue
        db.commit()
        db.close()
    else:
        db = dbutil.connection(g.cfg.setting.database_file)
        for alias, name in g.cfg.member.info.items():
            check_list: list = [
                textutil.str_conv(name, "k2h"),
                textutil.str_conv(name, "h2k"),
                textutil.str_conv(alias, "k2h"),
                textutil.str_conv(alias, "h2k"),
            ]
            for check in list(set(check_list)):
                if check == name:
                    continue
                rows = db.execute(
                    """
                    select
                        ts, p1_name, p2_name, p3_name, p4_name
                    from
                        result
                    where ? in (p1_name, p2_name, p3_name, p4_name);
                    """,
                    (check,),
                )
                for row in rows:
                    match check:
                        case check if check == row["p1_name"]:
                            logging.info("ts=%s, p1_name(%s -> %s)", row["ts"], check, name)
                            db.execute("update result set p1_name=? where p1_name=? and ts=?;", (name, check, row["ts"]))
                        case check if check == row["p2_name"]:
                            logging.info("ts=%s, p2_name(%s -> %s)", row["ts"], check, name)
                            db.execute("update result set p2_name=? where p2_name=? and ts=?;", (name, check, row["ts"]))
                        case check if check == row["p3_name"]:
                            logging.info("ts=%s, p3_name(%s -> %s)", row["ts"], check, name)
                            db.execute("update result set p3_name=? where p3_name=? and ts=?;", (name, check, row["ts"]))
                        case check if check == row["p4_name"]:
                            logging.info("ts=%s, p4_name(%s -> %s)", row["ts"], check, name)
                            db.execute("update result set p4_name=? where p4_name=? and ts=?;", (name, check, row["ts"]))

        db.commit()
        db.close()
