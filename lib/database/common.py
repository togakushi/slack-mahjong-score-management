import os
import shutil
import sqlite3
from datetime import datetime

import lib.function as f
import lib.database as d
from lib.function import global_value as g


def ExsistRecord(ts):
    resultdb = sqlite3.connect(
        g.database_file,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    row = resultdb.execute("select ts from result where ts=?", (ts,))
    line = len(row.fetchall())
    resultdb.close()

    if line:
        return (True)

    return (False)


def resultdb_insert(msg, ts):
    param = {
        "ts": ts,
        "playtime": datetime.fromtimestamp(float(ts)),
        "rule_version": g.rule_version,
    }
    param.update(f.score.get_score(msg))
    g.logging.notice(f"{param=}")  # type: ignore

    resultdb = sqlite3.connect(
        g.database_file,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    resultdb.execute(d.sql_result_insert, param)
    resultdb.commit()
    resultdb.close()


def resultdb_update(msg, ts):
    param = {
        "ts": ts,
        "playtime": datetime.fromtimestamp(float(ts)),
        "rule_version": g.rule_version,
    }
    param.update(f.score.get_score(msg))
    g.logging.notice(f"{param=}")  # type: ignore

    resultdb = sqlite3.connect(
        g.database_file,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    resultdb.execute(d.sql_result_update, param)
    resultdb.commit()
    resultdb.close()


def resultdb_delete(ts):
    resultdb = sqlite3.connect(
        g.database_file,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    resultdb.execute(d.sql_result_delete, (ts,))
    resultdb.execute(d.sql_remarks_delete_all, (ts,))
    resultdb.commit()
    resultdb.close()
    g.logging.notice(f"{ts}")  # type: ignore


def database_backup():
    backup_dir = g.config["database"].get("backup_dir", "")
    fname = os.path.splitext(g.database_file)[0]
    fext = os.path.splitext(g.database_file)[1]
    bktime = datetime.now().strftime('%Y%m%d-%H%M%S')
    bkfname = os.path.join(backup_dir, f"{fname}_{bktime}{fext}")

    if not backup_dir:  # バックアップ設定がされていない場合は何もしない
        return ("")

    if not os.path.isdir(backup_dir):  # バックアップディレクトリ作成
        try:
            os.mkdir(backup_dir)
        except Exception:
            g.logging.error("Database backup directory creation failed !!!")
            return ("\nバックアップ用ディレクトリ作成の作成に失敗しました。")

    # バックアップディレクトリにコピー
    try:
        shutil.copyfile(g.database_file, bkfname)
        g.logging.notice(f"database backup: {bkfname}")  # type: ignore
        return ("\nデータベースをバックアップしました。")
    except Exception:
        g.logging.error("Database backup failed !!!")
        return ("\nデータベースのバックアップに失敗しました。")
