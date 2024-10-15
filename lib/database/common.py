import inspect
import logging
import os
import re
import shutil
import sqlite3
import textwrap
from contextlib import closing
from datetime import datetime

import global_value as g
from lib import database as d
from lib import function as f


def query_modification(sql: str):
    """
    オプションの内容でクエリを修正する
    """

    if g.opt.individual:  # 個人集計
        sql = sql.replace("--[individual] ", "")
        # ゲスト関連フラグ
        if g.opt.unregistered_replace:
            sql = sql.replace("--[unregistered_replace] ", "")
            if g.opt.guest_skip:
                sql = sql.replace("--[guest_not_skip] ", "")
            else:
                sql = sql.replace("--[guest_skip] ", "")
        else:
            sql = sql.replace("--[unregistered_not_replace] ", "")
    else:  # チーム集計
        sql = sql.replace("--[team] ", "")
        if not g.opt.friendly_fire:
            sql = sql.replace("--[friendly_fire] ", "")

    # 集約集計
    match g.opt.collection:
        case "daily":
            sql = sql.replace("--[collection_daily] ", "")
            sql = sql.replace("--[collection] ", "")
        case "monthly":
            sql = sql.replace("--[collection_monthly] ", "")
            sql = sql.replace("--[collection] ", "")
        case "yearly":
            sql = sql.replace("--[collection_yearly] ", "")
            sql = sql.replace("--[collection] ", "")
        case _:
            sql = sql.replace("--[not_collection] ", "")

    if g.prm.search_word or g.prm.group_length:
        sql = sql.replace("--[group_by] ", "")
    else:
        sql = sql.replace("--[not_group_by] ", "")

    # コメント検索
    if g.opt.search_word:
        sql = sql.replace("--[search_word] ", "")
    else:
        sql = sql.replace("--[not_search_word] ", "")

    if g.opt.group_length:
        sql = sql.replace("--[group_length] ", "")
    else:
        sql = sql.replace("--[not_group_length] ", "")
        if g.prm.search_word:
            sql = sql.replace("--[comment] ", "")
        else:
            sql = sql.replace("--[not_comment] ", "")

    # 直近N検索用（全範囲取得してから絞る）
    if g.prm.target_count != 0:
        sql = sql.replace(
            "and my.playtime between",
            "-- and my.playtime between"
        )

    # プレイヤーリスト
    if g.prm.player_name:
        sql = sql.replace("--[player_name] ", "")
        sql = sql.replace(
            "<<player_list>>",
            ":" + ", :".join([x for x in [*g.prm.player_list]])
        )

    # SQLコメント削除
    sql = re.sub(r"^ *--\[.*$", "", sql, flags=re.MULTILINE)
    sql = re.sub(r"\n+", "\n", sql, flags=re.MULTILINE)

    # デバッグ用
    func = inspect.stack()[1].function
    logging.trace(f"{func}: opt = {vars(g.opt)}")  # type: ignore
    logging.trace(f"{func}: prm = {vars(g.prm)}")  # type: ignore
    logging.trace(f"{func}: sql = {textwrap.dedent(sql)}")  # type: ignore

    return (sql)


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


def resultdb_insert(detection, ts):
    param = {
        "ts": ts,
        "playtime": datetime.fromtimestamp(float(ts)),
        "rule_version": g.prm.rule_version,
    }
    param.update(f.score.get_score(detection))
    logging.notice(f"{param=}")  # type: ignore

    with closing(sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)) as cur:
        cur.execute(d.sql_result_insert, param)
        cur.commit()

    f.score.reactions(param, True)


def resultdb_update(msg, ts):
    param = {
        "ts": ts,
        "playtime": datetime.fromtimestamp(float(ts)),
        "rule_version": g.prm.rule_version,
    }
    param.update(f.score.get_score(msg))
    logging.notice(f"{param=}")  # type: ignore

    with closing(sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)) as cur:
        cur.execute(d.sql_result_update, param)
        cur.commit()

    f.score.reactions(param, True)


def resultdb_delete(ts):
    logging.notice(f"{ts}")  # type: ignore

    with closing(sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)) as cur:
        cur.execute(d.sql_result_delete, (ts,))
        cur.execute(d.sql_remarks_delete_all, (ts,))
        cur.commit()


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
