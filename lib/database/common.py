"""
lib/database/common.py
"""

import logging
import os
import re
import shutil
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import TYPE_CHECKING

import pandas as pd

import lib.global_value as g
from lib import function as f


if TYPE_CHECKING:
    from cls.subcom import SubCommand


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


def read_data(filepath: str) -> pd.DataFrame:
    """データベースからデータを取得する

    Args:
        filepath (str): SQLファイルパス

    Returns:
        pd.DataFrame: 集計結果
    """

    sql = query_modification(load_query(filepath))
    df = pd.read_sql(
        sql,
        sqlite3.connect(g.cfg.db.database_file),
        params=g.params,
    )

    # デバッグ用
    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_columns", None)
    logging.trace("prm: %s", g.params)  # type: ignore
    logging.trace("sql: %s", named_query(sql))  # type: ignore
    logging.trace(df)  # type: ignore

    return (df)


def placeholder(subcom: "SubCommand") -> dict:
    """プレースホルダに使用する辞書を生成

    Args:
        subcom (SubCommand): パラメータ

    Returns:
        dict: プレースホルダ用辞書
    """

    ret_dict: dict = {}
    ret_dict.update(command=subcom.section)
    ret_dict.update(g.cfg.mahjong.to_dict())
    ret_dict.update(guest_name=g.cfg.member.guest_name)
    ret_dict.update(f.common.analysis_argument(g.msg.argument))
    ret_dict.update(subcom.update(g.msg.argument))
    ret_dict.update(subcom.to_dict())
    ret_dict.update(starttime=ret_dict["search_range"]["starttime"])
    ret_dict.update(endtime=ret_dict["search_range"]["endtime"])
    ret_dict.update(onday=ret_dict["search_range"]["onday"])

    if ret_dict.get("search_word"):
        ret_dict.update(search_word=f"%{ret_dict["search_word"]}%")

    if not ret_dict.get("interval"):
        ret_dict.update(interval=g.cfg.interval)

    # プレイヤーリスト/対戦相手リスト
    if ret_dict["player_list"]:
        for k, v in ret_dict["player_list"].items():
            ret_dict[k] = v
    if ret_dict["competition_list"]:
        for k, v in ret_dict["competition_list"].items():
            ret_dict[k] = v

    # 利用しない要素は削除
    drop_keys: list = [
        "config",
        "rank_point",
        "aggregation_range",
        "regulations_type2",
        "search_range",
    ]
    for key in drop_keys:
        if key in ret_dict:
            ret_dict.pop(key)

    return (ret_dict)


def query_modification(sql: str) -> str:
    """クエリをオプションの内容で修正する

    Args:
        sql (str): 修正するクエリ

    Returns:
        str: 修正後のクエリ
    """

    if g.params.get("individual"):  # 個人集計
        sql = sql.replace("--[individual] ", "")
        # ゲスト関連フラグ
        if g.params.get("unregistered_replace"):
            sql = sql.replace("--[unregistered_replace] ", "")
            if g.params.get("guest_skip"):
                sql = sql.replace("--[guest_not_skip] ", "")
            else:
                sql = sql.replace("--[guest_skip] ", "")
        else:
            sql = sql.replace("--[unregistered_not_replace] ", "")
    else:  # チーム集計
        g.params.update(unregistered_replace=False)
        g.params.update(guest_skip=True)
        sql = sql.replace("--[team] ", "")
        if not g.params.get("friendly_fire"):
            sql = sql.replace("--[friendly_fire] ", "")

    # 集約集計
    match g.params.get("collection"):
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

    # コメント検索
    if g.params.get("search_word") or g.params.get("group_length"):
        sql = sql.replace("--[group_by] ", "")
    else:
        sql = sql.replace("--[not_group_by] ", "")

    if g.params.get("search_word"):
        sql = sql.replace("--[search_word] ", "")
    else:
        sql = sql.replace("--[not_search_word] ", "")

    if g.params.get("group_length"):
        sql = sql.replace("--[group_length] ", "")
    else:
        sql = sql.replace("--[not_group_length] ", "")
        if g.params.get("search_word"):
            sql = sql.replace("--[comment] ", "")
        else:
            sql = sql.replace("--[not_comment] ", "")

    # 直近N検索用（全範囲取得してから絞る）
    if g.params.get("target_count") != 0:
        sql = sql.replace(
            "and my.playtime between",
            "-- and my.playtime between"
        )

    # プレイヤーリスト
    if g.params.get("player_name"):
        sql = sql.replace("--[player_name] ", "")
        sql = sql.replace(
            "<<player_list>>",
            ":" + ", :".join(g.params["player_list"])
        )
    sql = sql.replace("<<guest_mark>>", g.cfg.setting.guest_mark)

    # フラグの処理
    match g.cfg.aggregate_unit:
        case "M":
            sql = sql.replace("<<collection>>", "substr(collection_daily, 1, 7) as 集計")
            sql = sql.replace("<<group by>>", "group by 集計")
        case "Y":
            sql = sql.replace("<<collection>>", "substr(collection_daily, 1, 4) as 集計")
            sql = sql.replace("<<group by>>", "group by 集計")
        case "A":
            sql = sql.replace("<<collection>>", "'合計' as 集計")
            sql = sql.replace("<<group by>>", "")

    if g.params.get("interval") is not None:
        if g.params.get("interval") == 0:
            sql = sql.replace("<<Calculation Formula>>", ":interval")
        else:
            sql = sql.replace(
                "<<Calculation Formula>>",
                "(row_number() over (order by total_count desc) - 1) / :interval"
            )
    if g.params.get("kind") is not None:
        if g.params.get("kind") == "grandslam":
            if g.cfg.undefined_word == 0:
                sql = sql.replace("<<where_string>>", "and (words.type is null or words.type = 0)")
            else:
                sql = sql.replace("<<where_string>>", "and words.type = 0")
        else:
            match g.cfg.undefined_word:
                case 1:
                    sql = sql.replace("<<where_string>>", "and (words.type is null or words.type = 1)")
                case 2:
                    sql = sql.replace("<<where_string>>", "and (words.type is null or words.type = 2)")
                case _:
                    sql = sql.replace("<<where_string>>", "and (words.type = 1 or words.type = 2)")

    # SQLコメント削除
    sql = re.sub(r"^ *--\[.*$", "", sql, flags=re.MULTILINE)
    sql = re.sub(r"\n+", "\n", sql, flags=re.MULTILINE)

    return (sql)


def named_query(query: str) -> str:
    """クエリにパラメータをバインドして返す

    Args:
        query (str): SQL

    Returns:
        str: バインド済みSQL
    """

    for k, v in g.params.items():
        if isinstance(v, datetime):
            g.params[k] = v.strftime("%Y-%m-%d %H:%M:%S")

    return re.sub(r":(\w+)", lambda m: repr(g.params.get(m.group(1), m.group(0))), query)


def exsist_record(ts) -> dict:
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


def first_record() -> datetime:
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


def db_insert(detection: list, ts: str, reactions_data: list | None = None) -> None:
    """スコアデータをDBに追加する

    Args:
        detection (list): スコア情報
        ts (str): コマンドが発行された時間
        reactions_data (list | None, optional): リアクションリスト. Defaults to None.
    """

    param = {
        "ts": ts,
        "playtime": datetime.fromtimestamp(float(ts)),
        "rule_version": g.cfg.mahjong.rule_version,
        "reactions_data": reactions_data,
    }
    param.update(f.score.get_score(detection))

    if g.msg.updatable:
        with closing(sqlite3.connect(g.cfg.db.database_file)) as cur:
            cur.execute(g.SQL_RESULT_INSERT, param)
            cur.commit()
        logging.notice("user=%s, param=%s", g.msg.user_id, param)  # type: ignore
        f.score.reactions(param)
    else:
        f.slack_api.post_message(f.message.reply(message="restricted_channel"), g.msg.event_ts)


def db_update(detection: list, ts: str, reactions_data: list | None = None) -> None:
    """スコアデータを変更する

    Args:
        detection (list): スコア情報
        ts (str): コマンドが発行された時間
        reactions_data (list | None, optional): リアクションリスト. Defaults to None.
    """

    param = {
        "ts": ts,
        "playtime": datetime.fromtimestamp(float(ts)),
        "rule_version": g.cfg.mahjong.rule_version,
        "reactions_data": reactions_data,
    }
    param.update(f.score.get_score(detection))

    if g.msg.updatable:
        with closing(sqlite3.connect(g.cfg.db.database_file)) as cur:
            cur.execute(g.SQL_RESULT_UPDATE, param)
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
            cur.execute(g.SQL_RESULT_DELETE, (ts,))
            delete_result = cur.execute("select changes();").fetchone()[0]
            cur.execute(g.SQL_REMARKS_DELETE_ALL, (ts,))
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
        except OSError as e:
            logging.error(e, exc_info=True)
            logging.error("Database backup directory creation failed !!!")
            return ("\nバックアップ用ディレクトリ作成の作成に失敗しました。")

    # バックアップディレクトリにコピー
    try:
        shutil.copyfile(g.cfg.db.database_file, bkfname)
        logging.notice("database backup: %s", bkfname)  # type: ignore
        return ("\nデータベースをバックアップしました。")
    except OSError as e:
        logging.error(e, exc_info=True)
        logging.error("Database backup failed !!!")
        return ("\nデータベースのバックアップに失敗しました。")


def remarks_append(remarks: dict | list) -> None:
    """メモをDBに記録する

    Args:
        remarks (dict | list): メモに残す内容
    """

    if isinstance(remarks, dict):
        remarks = [remarks]

    if g.msg.updatable:
        with closing(sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)) as cur:
            cur.row_factory = sqlite3.Row

            for para in remarks:
                # 親スレッドの情報
                row = cur.execute("select * from result where ts=:thread_ts", para).fetchone()
                if row:
                    if para["name"] in [v for k, v in dict(row).items() if k.endswith("_name")]:
                        cur.execute(g.SQL_REMARKS_INSERT, para)
                        logging.notice("insert: %s, user=%s", para, g.msg.user_id)  # type: ignore

                        if g.cfg.setting.reaction_ok not in f.slack_api.reactions_status(ts=para.get("event_ts")):
                            f.slack_api.call_reactions_add(g.cfg.setting.reaction_ok, ts=para.get("event_ts"))

            cur.commit()


def remarks_delete(ts: str) -> None:
    """DBからメモを削除する

    Args:
        ts (str): 削除対象レコードのタイムスタンプ
    """

    if g.msg.updatable:
        with closing(sqlite3.connect(g.cfg.db.database_file)) as cur:
            cur.execute(g.SQL_REMARKS_DELETE_ONE, (ts,))
            count = cur.execute("select changes();").fetchone()[0]
            cur.commit()

        if count:
            logging.notice("ts=%s, user=%s, count=%s", ts, g.msg.user_id, count)  # type: ignore

        if g.msg.status != "message_deleted":
            if g.cfg.setting.reaction_ok in f.slack_api.reactions_status():
                f.slack_api.call_reactions_remove(g.cfg.setting.reaction_ok, ts=ts)


def remarks_delete_compar(para: dict) -> None:
    """DBからメモを削除する(突合)

    Args:
        para (dict): パラメータ
    """

    ch: str | None

    with closing(sqlite3.connect(g.cfg.db.database_file)) as cur:
        cur.execute(g.SQL_REMARKS_DELETE_COMPAR, para)
        cur.commit()

        left = cur.execute("select count() from remarks where event_ts=:event_ts;", para).fetchone()[0]

    if g.msg.channel_id:
        ch = g.msg.channel_id
    else:
        ch = f.slack_api.get_channel_id()

    icon = f.slack_api.reactions_status(ts=para.get("event_ts"))
    if g.cfg.setting.reaction_ok in icon and left == 0:
        f.slack_api.call_reactions_remove(g.cfg.setting.reaction_ok, ch=ch, ts=para.get("event_ts"))


def rule_version() -> dict:
    """DBに記録されているルールバージョン毎の範囲を取得する

    Returns:
        dict: 取得結果
    """

    rule: dict = {}
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


def word_list(word_type: int = 0) -> list:
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

    return (ret.fetchall())


def df_rename(df: pd.DataFrame, short=True) -> pd.DataFrame:
    """カラム名をリネームする

    Args:
        df (pd.DataFrame): 対象データフレーム
        short (bool, optional): 略語にリネーム. Defaults to True.

    Returns:
        pd.DataFrame: リネーム後のデータフレーム
    """

    rename_dict: dict = {
        "playtime": "日時",
        # 直接対決
        "results": "対戦結果", "win%": "勝率",
        "my_point_sum": "獲得ポイント(自分)", "my_point_avg": "平均ポイント(自分)",
        "vs_point_sum": "獲得ポイント(相手)", "vs_point_avg": "平均ポイント(相手)",
        "my_rpoint_avg": "平均素点(自分)", "my_rank_avg": "平均順位(自分)", "my_rank_distr": "順位分布(自分)",
        "vs_rpoint_avg": "平均素点(相手)", "vs_rank_avg": "平均順位(相手)", "vs_rank_distr": "順位分布(相手)",
    }

    for x in df.columns:
        match x:
            case "rank":
                rename_dict[x] = "#" if short else "順位"
            case "name" | "player":
                rename_dict[x] = "名前" if short else "プレイヤー名"
            case "team":
                rename_dict[x] = "チーム" if short else "チーム名"
            case "count" | "game":
                rename_dict[x] = "ゲーム数"
            case "rpoint":
                rename_dict[x] = "素点"
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
