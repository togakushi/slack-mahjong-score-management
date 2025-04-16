"""
lib/function/tools/unification.py
"""

import configparser
import logging
import sqlite3

import libs.global_value as g
from libs.data import modify
from libs.functions import configuration
from libs.utils import validator


def main():
    """ゲストメンバーの名前を統一する"""
    rename_conf = configparser.ConfigParser()
    rename_conf.read(g.args.unification, encoding="utf-8")
    configuration.read_memberslist(False)

    if "rename" in rename_conf.sections():
        modify.db_backup()
        name_table: dict = {}
        for name, alias in rename_conf["rename"].items():
            name_table.setdefault(name, [x.strip() for x in alias.split(",")])

        db = sqlite3.connect(g.cfg.db.database_file)

        for name, alias_list in name_table.items():
            count = 0
            chk, msg = validator.check_namepattern(name)
            if chk:
                for alias in alias_list:
                    chk, msg = validator.check_namepattern(alias)
                    if chk:
                        db.execute("update result set p1_name=? where p1_name=?;", (name, alias,))
                        count += db.execute("select changes();").fetchone()[0]
                        db.execute("update result set p2_name=? where p2_name=?;", (name, alias,))
                        count += db.execute("select changes();").fetchone()[0]
                        db.execute("update result set p3_name=? where p3_name=?;", (name, alias,))
                        count += db.execute("select changes();").fetchone()[0]
                        db.execute("update result set p4_name=? where p4_name=?;", (name, alias,))
                        count += db.execute("select changes();").fetchone()[0]
                        db.execute("update remarks set name=? where name=?;", (name, alias,))
                        count += db.execute("select changes();").fetchone()[0]
                    else:
                        logging.warning("remove: %s -> %s (%s)", name, alias, msg)
                        alias_list.remove(alias)
                        continue
                logging.notice("rename: %s -> %s changed: %s", alias_list, name, count)  # type: ignore
            else:
                logging.warning("skip: %s (%s)", name, msg)
                continue
        db.commit()
        db.close()
    else:
        logging.error("section not found.")
