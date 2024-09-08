import logging
import os
import shutil
import sqlite3
from contextlib import closing
from datetime import datetime

import global_value as g
from lib import database as d
from lib import function as f


def ExsistRecord(ts):
    resultdb = sqlite3.connect(
        g.cfg.db.database_file,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    row = resultdb.execute("select ts from result where ts=?", (ts,))
    line = len(row.fetchall())
    resultdb.close()

    if line:
        return (True)
    else:
        return (False)


def first_record():
    """
    最初のゲーム記録時間を返す
    """

    ret = datetime.now()
    with closing(sqlite3.connect(g.cfg.db.database_file)) as resultdb:
        table_count = resultdb.execute(
            "select count() from sqlite_master where type='view' and name='game_results'",
        ).fetchall()[0][0]

        if table_count:
            record = resultdb.execute(
                "select min(playtime) from game_results"
            ).fetchall()[0][0]
            if record:
                ret = datetime.fromisoformat(record)

    return (ret)


def resultdb_insert(msg, ts):
    param = {
        "ts": ts,
        "playtime": datetime.fromtimestamp(float(ts)),
        "rule_version": g.prm.rule_version,
    }
    param.update(f.score.get_score(msg))
    logging.notice(f"{param=}")  # type: ignore

    resultdb = sqlite3.connect(
        g.cfg.db.database_file,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    resultdb.execute(d.sql_result_insert, param)
    resultdb.commit()
    resultdb.close()


def resultdb_update(msg, ts):
    param = {
        "ts": ts,
        "playtime": datetime.fromtimestamp(float(ts)),
        "rule_version": g.prm.rule_version,
    }
    param.update(f.score.get_score(msg))
    logging.notice(f"{param=}")  # type: ignore

    resultdb = sqlite3.connect(
        g.cfg.db.database_file,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    resultdb.execute(d.sql_result_update, param)
    resultdb.commit()
    resultdb.close()


def resultdb_delete(ts):
    resultdb = sqlite3.connect(
        g.cfg.db.database_file,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    resultdb.execute(d.sql_result_delete, (ts,))
    resultdb.execute(d.sql_remarks_delete_all, (ts,))
    resultdb.commit()
    resultdb.close()
    logging.notice(f"{ts}")  # type: ignore


def database_backup():
    fname = os.path.splitext(g.cfg.db.database_file)[0]
    fext = os.path.splitext(g.cfg.db.database_file)[1]
    bktime = datetime.now().strftime('%Y%m%d-%H%M%S')
    bkfname = os.path.join(g.cfg.db.backup_dir, f"{fname}_{bktime}{fext}")

    if not g.cfg.db.backup_dir:  # バックアップ設定がされていない場合は何もしない
        return ("")

    if not os.path.isdir(g.cfg.db.backup_dir):  # バックアップディレクトリ作成
        try:
            os.mkdir(g.cfg.db.backup_dir)
        except Exception:
            logging.error("Database backup directory creation failed !!!")
            return ("\nバックアップ用ディレクトリ作成の作成に失敗しました。")

    # バックアップディレクトリにコピー
    try:
        shutil.copyfile(g.cfg.db.database_file, bkfname)
        logging.notice(f"database backup: {bkfname}")  # type: ignore
        return ("\nデータベースをバックアップしました。")
    except Exception:
        logging.error("Database backup failed !!!")
        return ("\nデータベースのバックアップに失敗しました。")
