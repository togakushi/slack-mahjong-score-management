import logging
import os
import re
import shutil
import sqlite3
from contextlib import closing
from datetime import datetime

import pandas as pd

import lib.global_value as g
from lib import database as d
from lib import function as f


def load_query(filepath: str) -> str:
    """外部ファイルからクエリを読み込む

    Args:
        filepath (str): 読み込むSQLファイルパス

    Returns:
        str: SQL
    """

    with open(filepath, "r", encoding="utf-8") as queryfile:
        sql = queryfile.read().strip()

    return (sql)


def read_data(filepath: str, flag: str | None = None) -> pd.DataFrame:
    """データベースからデータを取得する

    Args:
        filepath (str): SQLファイルパス
        flag (str | None, optional): 集計単位. Defaults to None.
            - M: 月間集計
            - Y: 年間集計
            - A: 全期間集計

    Returns:
        pd.DataFrame: 集計結果
    """

    sql = query_modification(load_query(filepath), flag)
    df = pd.read_sql(
        sql,
        sqlite3.connect(g.cfg.db.database_file),
        params=g.prm.to_dict(),
    )

    # デバッグ用
    logging.trace("opt: opt=%s", vars(g.opt))  # type: ignore
    logging.trace("prm: prm=%s", vars(g.prm))  # type: ignore
    logging.trace("sql: sql=%s", named_query(sql, g.prm.to_dict()))  # type: ignore

    return (df)


def query_modification(sql: str, flag: str | None = None) -> str:
    """クエリをオプションの内容で修正する

    Args:
        sql (str): 修正するクエリ
        flag (str, optional): 集計単位. Defaults to None.
            - M: 月間集計
            - Y: 年間集計
            - A: 全期間集計

    Returns:
        str: 修正後のクエリ
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
        g.opt.unregistered_replace = False
        g.opt.guest_skip = True
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

    if g.prm.search_word or g.prm.get("group_length"):
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
            ":" + ", :".join(list([*g.prm.player_list]))
        )
    sql = sql.replace("<<guest_mark>>", g.cfg.setting.guest_mark)

    # フラグの処理
    match flag:
        case "M":
            sql = sql.replace("<<collection>>", "substr(collection_daily, 1, 7) as 集計")
            sql = sql.replace("<<group by>>", "group by 集計")
        case "Y":
            sql = sql.replace("<<collection>>", "substr(collection_daily, 1, 4) as 集計")
            sql = sql.replace("<<group by>>", "group by 集計")
        case "A":
            sql = sql.replace("<<collection>>", "'合計' as 集計")
            sql = sql.replace("<<group by>>", "")

    if g.prm.get("interval") is not None:
        if g.prm.get("interval") == 0:
            sql = sql.replace("<<Calculation Formula>>", ":interval")
        else:
            sql = sql.replace(
                "<<Calculation Formula>>",
                "(row_number() over (order by total_count desc) - 1) / :interval"
            )
    if g.prm.get("kind") is not None:
        if g.prm.get("kind") == "grandslam":
            if g.undefined_word == 0:
                sql = sql.replace("<<where_string>>", "and (words.type is null or words.type = 0)")
            else:
                sql = sql.replace("<<where_string>>", "and words.type = 0")
        else:
            if g.undefined_word == 2:
                sql = sql.replace("<<where_string>>", "and (words.type is null or words.type = 1 or words.type = 2)")
            else:
                sql = sql.replace("<<where_string>>", "and (words.type = 1 or words.type = 2)")

    # SQLコメント削除
    sql = re.sub(r"^ *--\[.*$", "", sql, flags=re.MULTILINE)
    sql = re.sub(r"\n+", "\n", sql, flags=re.MULTILINE)

    return (sql)


def named_query(query: str, params: dict) -> str:
    """クエリにパラメータをバインドして返す

    Args:
        query (str): SQL
        params (dict): パラメータ

    Returns:
        str: バインド済みSQL
    """

    for k, v in params.items():
        if isinstance(v, datetime):
            params[k] = v.strftime("%Y-%m-%d %H:%M:%S")

    return re.sub(r":(\w+)", lambda m: repr(params.get(m.group(1), m.group(0))), query)


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

    if g.msg.updatable:
        with closing(sqlite3.connect(g.cfg.db.database_file)) as cur:
            cur.execute(d.sql_result_insert, param)
            cur.commit()
        logging.notice("user=%s, param=%s", g.msg.user_id, param)  # type: ignore
        f.score.reactions(param)
    else:
        f.slack_api.post_message(f.message.reply(message="restricted_channel"), g.msg.event_ts)


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

    if g.msg.updatable:
        with closing(sqlite3.connect(g.cfg.db.database_file)) as cur:
            cur.execute(d.sql_result_update, param)
            cur.commit()
        logging.notice("user=%s, param=%s", g.msg.user_id, param)  # type: ignore
        f.score.reactions(param)
    else:
        f.slack_api.post_message(f.message.reply(message="restricted_channel"), g.msg.event_ts)


def db_delete(ts):
    """スコアデータを削除する

    Args:
        ts (datetime): 削除対象レコードのタイムスタンプ
    """

    if g.msg.updatable:
        with closing(sqlite3.connect(g.cfg.db.database_file)) as cur:
            delete_list = cur.execute("select event_ts from remarks where thread_ts=?", (ts,)).fetchall()
            cur.execute(d.sql_result_delete, (ts,))
            delete_result = cur.execute("select changes();").fetchone()[0]
            cur.execute(d.sql_remarks_delete_all, (ts,))
            delete_remark = cur.execute("select changes();").fetchone()[0]
            cur.commit()

        if delete_result:
            logging.notice("result: ts=%s, user=%s, count=%s", ts, g.msg.user_id, delete_result)  # type: ignore
        if delete_remark:
            logging.notice("remark: ts=%s, user=%s, count=%s", ts, g.msg.user_id, delete_remark)  # type: ignore

        # リアクションをすべて外す
        for icon in f.slack_api.reactions_status():
            f.slack_api.call_reactions_remove(icon)
        # メモのアイコンを外す
        for x in delete_list:
            for icon in f.slack_api.reactions_status(ts=x):
                f.slack_api.call_reactions_remove(icon, ts=x)


def db_backup() -> str:
    """データベースのバックアップ

    Returns:
        str: 動作結果メッセージ
    """

    if not g.cfg.db.backup_dir:  # バックアップ設定がされていない場合は何もしない
        return ("")

    fname = os.path.splitext(g.cfg.db.database_file)[0]
    fext = os.path.splitext(g.cfg.db.database_file)[1]
    bktime = datetime.now().strftime('%Y%m%d-%H%M%S')
    bkfname = os.path.join(g.cfg.db.backup_dir, f"{fname}_{bktime}{fext}")

    if not os.path.isdir(g.cfg.db.backup_dir):  # バックアップディレクトリ作成
        try:
            os.mkdir(g.cfg.db.backup_dir)
        except Exception:
            logging.error("Database backup directory creation failed !!!")
            return ("\nバックアップ用ディレクトリ作成の作成に失敗しました。")

    # バックアップディレクトリにコピー
    try:
        shutil.copyfile(g.cfg.db.database_file, bkfname)
        logging.notice("database backup: %s", bkfname)  # type: ignore
        return ("\nデータベースをバックアップしました。")
    except Exception:
        logging.error("Database backup failed !!!")
        return ("\nデータベースのバックアップに失敗しました。")


def remarks_append(remarks):
    """メモをDBに記録する

    Args:
        remarks (list): メモに残す内容
    """

    if g.msg.updatable:
        with closing(sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)) as cur:
            cur.row_factory = sqlite3.Row

            for remark in remarks:
                # 親スレッドの情報
                row = cur.execute("select * from result where ts=:thread_ts", remark).fetchone()

                if row:
                    if remark["name"] in [v for k, v in dict(row).items() if k.endswith("_name")]:
                        cur.execute(d.sql_remarks_insert, remark)
                        logging.notice("insert: %s, user=%s", remark, g.msg.user_id)  # type: ignore

                        if g.cfg.setting.reaction_ok not in f.slack_api.reactions_status():
                            f.slack_api.call_reactions_add(g.cfg.setting.reaction_ok, ts=remark["event_ts"])

            cur.commit()


def remarks_delete(ts):
    """DBからメモを削除する

    Args:
        ts (datetime): 削除対象レコードのタイムスタンプ
    """

    if g.msg.updatable:
        with closing(sqlite3.connect(g.cfg.db.database_file)) as cur:
            cur.execute(d.sql_remarks_delete_one, (ts,))
            count = cur.execute("select changes();").fetchone()[0]
            cur.commit()

        if count:
            logging.notice("ts=%s, user=%s, count=%s", ts, g.msg.user_id, count)  # type: ignore

        if g.msg.status != "message_deleted":
            if g.cfg.setting.reaction_ok in f.slack_api.reactions_status():
                f.slack_api.call_reactions_remove(g.cfg.setting.reaction_ok, ts=ts)


def remarks_delete_compar(para):
    with closing(sqlite3.connect(g.cfg.db.database_file)) as cur:
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


def df_rename(df: pd.DataFrame, short=True) -> pd.DataFrame:
    """カラム名をリネームする

    Args:
        df (pd.DataFrame): 対象データフレーム
        short (bool, optional): 略語にリネーム. Defaults to True.

    Returns:
        pd.DataFrame: リネーム後のデータフレーム
    """

    rename_dict: dict = {}

    for x in df.columns:
        match x:
            case "rank":
                rename_dict[x] = "#" if short else "順位"
            case "playtime":
                rename_dict[x] = "日時"
            case "name" | "player":
                rename_dict[x] = "名前" if short else "プレイヤー名"
            case "team":
                rename_dict[x] = "チーム" if short else "チーム名"
            case "count" | "game":
                rename_dict[x] = "ゲーム数"
            case "point":
                rename_dict[x] = "獲得ポイント"
            case "pt_total" | "total_point" | "point_sum" | "total_mix":
                rename_dict[x] = "通算" if short else "通算ポイント"
            case "pt_avg" | "avg_point" | "point_avg" | "avg_mix":
                rename_dict[x] = "平均" if short else "平均ポイント"
            case "ex_point":
                rename_dict[x] = "卓外" if short else "卓外ポイント"
            case "rank_distr" | "rank_distr1" | "rank_distr2":
                rename_dict[x] = "順位分布"
            case "rank_avg":
                rename_dict[x] = "平順" if short else "平均順位"
            case "1st" | "rank1" | "1st_mix":
                rename_dict[x] = "1位"
            case "2nd" | "rank2" | "2nd_mix":
                rename_dict[x] = "2位"
            case "3rd" | "rank3" | "3rd_mix":
                rename_dict[x] = "3位"
            case "4th" | "rank4" | "4th_mix":
                rename_dict[x] = "4位"
            case "1st(%)" | "1st_%" | "rank1_rate":
                rename_dict[x] = "1位率"
            case "2nd(%)" | "2nd_%" | "rank2_rate":
                rename_dict[x] = "2位率"
            case "3rd(%)" | "3rd_%" | "rank3_rate":
                rename_dict[x] = "3位率"
            case "4th(%)" | "4th_%" | "rank4_rate":
                rename_dict[x] = "4位率"
            case "1st_count":
                rename_dict[x] = "1位数"
            case "2nd_count":
                rename_dict[x] = "2位数"
            case "3rd_count":
                rename_dict[x] = "3位数"
            case "4th_count":
                rename_dict[x] = "4位数"
            case "flying" | "flying_mix":
                rename_dict[x] = "トビ"
            case "flying_count":
                rename_dict[x] = "トビ数"
            case "flying_rate" | "flying_%":
                rename_dict[x] = "トビ率"
            case "pt_diff":
                rename_dict[x] = "差分"
            case "diff_from_above":
                rename_dict[x] = "順位差"
            case "diff_from_top":
                rename_dict[x] = "トップ差"
            case "yakuman_mix" | "grandslam":
                rename_dict[x] = "役満和了"
            case "yakuman_count":
                rename_dict[x] = "役満和了数"
            case "yakuman_%":
                rename_dict[x] = "役満和了率"

    return (df.rename(columns=rename_dict))
