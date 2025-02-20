import configparser
import logging
import sqlite3

import lib.global_value as g
from lib import command as c
from lib import database as d


def main():
    """ゲストメンバーの名前を統一する
    """

    rename_conf = configparser.ConfigParser()
    rename_conf.read(g.args.unification, encoding="utf-8")
    c.member.read_memberslist(False)

    if "rename" in rename_conf.sections():
        d.common.db_backup()
        name_table = {}
        for name, alias in rename_conf["rename"].items():
            name_table.setdefault(name, [x.strip() for x in alias.split(",")])

        db = sqlite3.connect(g.cfg.db.database_file)

        for name in name_table.keys():
            count = 0
            chk, msg = c.member.check_namepattern(name)
            if chk:
                for alias in name_table[name]:
                    chk, msg = c.member.check_namepattern(alias)
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
                        name_table[name].remove(alias)
                        continue
                logging.notice("rename: %s -> %s changed: %s", name_table[name], name, count)
            else:
                logging.warning("skip: %s (%s)", name, msg)
                continue
        db.commit()
        db.close()
    else:
        logging.error("section not found.")
