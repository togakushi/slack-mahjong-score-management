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
    """オプションの内容でクエリを修正する

    Args:
        sql (str): SQL

    Returns:
        str: SQL
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
        case "all":
            sql = sql.replace("--[collection_all] ", "")
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
    logging.trace(f"{func}: opt = {vars(g.opt)}")
    logging.trace(f"{func}: prm = {vars(g.prm)}")
    logging.trace(f"{func}: sql = {textwrap.dedent(sql)}")

    return (sql)


def exsist_record(ts):
    """記録されているゲーム結果を返す

    Args:
        ts (float): 検索するタイムスタンプ

    Returns:
        dict: 検索結果
    """

    with closing(sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)) as cur:
        cur.row_factory = sqlite3.Row
        row = cur.execute("select * from result where ts=?", (ts,)).fetchone()

    if row:
        return (dict(row))
    else:
        return ({})


def first_record():
    """最初のゲーム記録時間を返す

    Returns:
        datetime: 最初のゲーム記録時間
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


def db_insert(detection, ts, reactions_data=None):
    """スコアデータをDBに追加する

    Args:
        detection (list): スコア情報
        ts (datetime): コマンドが発行された時間
        reactions_data (_type_, optional): リアクションリスト. Defaults to None.
    """

    param = {
        "ts": ts,
        "playtime": datetime.fromtimestamp(float(ts)),
        "rule_version": g.prm.rule_version,
        "reactions_data": reactions_data,
    }
    param.update(f.score.get_score(detection))
    logging.notice(f"user={g.msg.user_id} {param=}")

    with closing(sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)) as cur:
        cur.execute(d.sql_result_insert, param)
        cur.commit()

    f.score.reactions(param)


def db_update(detection, ts, reactions_data=None):
    """スコアデータを変更する

    Args:
        detection (list): スコア情報
        ts (datetime): コマンドが発行された時間
        reactions_data (_type_, optional): リアクションリスト. Defaults to None.
    """

    param = {
        "ts": ts,
        "playtime": datetime.fromtimestamp(float(ts)),
        "rule_version": g.prm.rule_version,
        "reactions_data": reactions_data,
    }
    param.update(f.score.get_score(detection))
    logging.notice(f"user={g.msg.user_id} {param=}")

    with closing(sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)) as cur:
        cur.execute(d.sql_result_update, param)
        cur.commit()

    f.score.reactions(param)


def db_delete(ts):
    """スコアデータを削除する

    Args:
        ts (datetime): 削除対象レコードのタイムスタンプ
    """

    with closing(sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)) as cur:
        delete_list = cur.execute("select event_ts from remarks where thread_ts=?", (ts,)).fetchall()
        cur.execute(d.sql_result_delete, (ts,))
        delete_result = cur.execute("select changes();").fetchone()[0]
        cur.execute(d.sql_remarks_delete_all, (ts,))
        delete_remark = cur.execute("select changes();").fetchone()[0]
        cur.commit()

    if delete_result:
        logging.notice(f"result: {ts=} user={g.msg.user_id} count={delete_result}")
    if delete_remark:
        logging.notice(f"remark: {ts=} user={g.msg.user_id} count={delete_remark}")

    # リアクションをすべて外す
    for icon in f.slack_api.reactions_status():
        f.slack_api.call_reactions_remove(icon)
    # メモのアイコンを外す
    for x in delete_list:
        for icon in f.slack_api.reactions_status(ts=x):
            f.slack_api.call_reactions_remove(icon, ts=x)


def db_backup():
    """データベースのバックアップ

    Returns:
        str: 動作結果メッセージ
    """

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
        logging.notice(f"database backup: {bkfname}")
        return ("\nデータベースをバックアップしました。")
    except Exception:
        logging.error("Database backup failed !!!")
        return ("\nデータベースのバックアップに失敗しました。")


def remarks_append(remarks):
    """メモをDBに記録する

    Args:
        remarks (list): メモに残す内容
    """

    with closing(sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)) as cur:
        cur.row_factory = sqlite3.Row

        for remark in remarks:
            # 親スレッドの情報
            row = cur.execute("select * from result where ts=:thread_ts", remark).fetchone()

            if row:
                if remark["name"] in [v for k, v in dict(row).items() if k.endswith("_name")]:
                    cur.execute(d.sql_remarks_insert, remark)
                    logging.notice(f"insert: {remark}")

                    if g.cfg.setting.reaction_ok not in f.slack_api.reactions_status():
                        f.slack_api.call_reactions_add(g.cfg.setting.reaction_ok, ts=remark["event_ts"])

        cur.commit()


def remarks_delete(ts):
    """DBからメモを削除する

    Args:
        ts (datetime): 削除対象レコードのタイムスタンプ
    """

    logging.notice(f"{ts}")

    with closing(sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)) as cur:
        cur.execute(d.sql_remarks_delete_one, (ts,))
        cur.commit()

    if g.msg.status != "message_deleted":
        if g.cfg.setting.reaction_ok in f.slack_api.reactions_status():
            f.slack_api.call_reactions_remove(g.cfg.setting.reaction_ok, ts=ts)


def remarks_delete_compar(para):
    with closing(sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)) as cur:
        cur.execute(d.sql_remarks_delete_compar, para)
        cur.commit()


def rule_version():
    """DBに記録されているルールバージョン毎の範囲を取得する

    Returns:
        dict: 取得結果
    """

    rule = {}
    with closing(sqlite3.connect(g.cfg.db.database_file)) as cur:
        ret = cur.execute(
            """
            select
                rule_version,
                strftime("%Y/%m/%d %H:%M:%S", min(playtime)) as min,
                strftime("%Y/%m/%d %H:%M:%S", max(playtime)) as max
            from
                result
            group by
                rule_version
            """
        )

        for version, first_time, last_time in ret.fetchall():
            rule[version] = {
                "first_time": first_time,
                "last_time": last_time,
            }

    return (rule)


def word_list(word_type=0):
    """登録済みワードリストを取得する

    Args:
        word_type (int, optional): 取得するタイプ. Defaults to 0.

    Returns:
        list: 取得結果
    """

    with closing(sqlite3.connect(g.cfg.db.database_file)) as cur:
        ret = cur.execute(
            """
            select
                word,
                ex_point
            from
                words
            where
                type=?
            """, (word_type,)
        )

        x = ret.fetchall()

    return (x)
