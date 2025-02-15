import configparser
import sqlite3

import global_value as g
from lib import database as d


def main():
    """ゲストメンバーの名前を統一する
    """

    rename_conf = configparser.ConfigParser()
    rename_conf.read(g.args.unification, encoding="utf-8")

    if "rename" in rename_conf.sections():
        d.common.db_backup()
        name_table = {}
        for name, alias in rename_conf["rename"].items():
            name_table.setdefault(name, [x.strip() for x in alias.split(",")])

        db = sqlite3.connect(g.cfg.db.database_file)

        for name in name_table.keys():
            print("rename:", name_table[name], "->", name)
            for alias in name_table[name]:
                db.execute("update result set p1_name=? where p1_name=?;", (name, alias,))
                db.execute("update result set p2_name=? where p2_name=?;", (name, alias,))
                db.execute("update result set p3_name=? where p3_name=?;", (name, alias,))
                db.execute("update result set p4_name=? where p4_name=?;", (name, alias,))
                db.execute("update remarks set name=? where name=?;", (name, alias,))

        db.commit()
        db.close()
    else:
        print("no sections")
