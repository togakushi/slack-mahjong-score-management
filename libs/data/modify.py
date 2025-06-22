"""
lib/data/modify.py
"""

import logging
import os
import re
import shutil
from contextlib import closing

import libs.global_value as g
from cls.score import GameResult
from cls.timekit import ExtendedDatetime as ExtDt
from libs.data import lookup
from libs.functions import message, slack_api
from libs.utils import dbutil, formatter


def db_insert(detection: GameResult, reactions_data: list | None = None) -> None:
    """スコアデータをDBに追加する

    Args:
        detection (GameResult): スコアデータ
        reactions_data (list | None, optional): リアクションリスト. Defaults to None.
    """

    detection.set(ts=g.msg.event_ts)
    detection.calc()
    param = {
        "playtime": ExtDt(float(g.msg.event_ts)).format("sql"),
        "reactions_data": reactions_data,
        "rpoint_sum": detection.rpoint_sum(),
        **detection.to_dict(),
    }

    if g.msg.updatable:
        with closing(dbutil.get_connection()) as cur:
            cur.execute(g.sql["RESULT_INSERT"], param)
            cur.commit()
        logging.notice("%s, user=%s", detection, g.msg.user_id)  # type: ignore
        score_reactions(param)
    else:
        slack_api.post_message(message.reply(message="restricted_channel"), g.msg.event_ts)


def db_update(detection: GameResult, reactions_data: list | None = None) -> None:
    """スコアデータを変更する

    Args:
        detection (GameResult): スコアデータ
        reactions_data (list | None, optional): リアクションリスト. Defaults to None.
    """

    detection.set(ts=g.msg.event_ts)
    detection.calc()
    param = {
        "playtime": ExtDt(float(g.msg.event_ts)).format("sql"),
        "reactions_data": reactions_data,
        "rpoint_sum": detection.rpoint_sum(),
        **detection.to_dict(),
    }

    if g.msg.updatable:
        with closing(dbutil.get_connection()) as cur:
            cur.execute(g.sql["RESULT_UPDATE"], param)
            cur.commit()
        logging.notice("%s, user=%s", detection, g.msg.user_id)  # type: ignore
        score_reactions(param)
    else:
        slack_api.post_message(message.reply(message="restricted_channel"), g.msg.event_ts)


def db_delete(ts: str):
    """スコアデータを削除する

    Args:
        ts (str): 削除対象レコードのタイムスタンプ
    """

    if g.msg.updatable:
        with closing(dbutil.get_connection()) as cur:
            delete_list = cur.execute("select event_ts from remarks where thread_ts=?", (ts,)).fetchall()
            cur.execute(g.sql["RESULT_DELETE"], (ts,))
            delete_result = cur.execute("select changes();").fetchone()[0]
            cur.execute(g.sql["REMARKS_DELETE_ALL"], (ts,))
            delete_remark = cur.execute("select changes();").fetchone()[0]
            cur.commit()

        if delete_result:
            logging.notice("result: ts=%s, user=%s, count=%s", ts, g.msg.user_id, delete_result)  # type: ignore
        if delete_remark:
            logging.notice("remark: ts=%s, user=%s, count=%s", ts, g.msg.user_id, delete_remark)  # type: ignore

        # リアクションをすべて外す
        for icon in lookup.api.reactions_status():
            slack_api.call_reactions_remove(icon)
        # メモのアイコンを外す
        for x in delete_list:
            for icon in lookup.api.reactions_status(ts=x):
                slack_api.call_reactions_remove(icon, ts=x)


def db_backup() -> str:
    """データベースのバックアップ

    Returns:
        str: 動作結果メッセージ
    """

    if not g.cfg.db.backup_dir:  # バックアップ設定がされていない場合は何もしない
        return ""

    fname = os.path.splitext(g.cfg.db.database_file)[0]
    fext = os.path.splitext(g.cfg.db.database_file)[1]
    bktime = ExtDt().format("ext")
    bkfname = os.path.join(g.cfg.db.backup_dir, os.path.basename(f"{fname}_{bktime}{fext}"))

    if not os.path.isdir(g.cfg.db.backup_dir):  # バックアップディレクトリ作成
        try:
            os.mkdir(g.cfg.db.backup_dir)
        except OSError as e:
            logging.error(e, exc_info=True)
            logging.error("Database backup directory creation failed !!!")
            return "\nバックアップ用ディレクトリ作成の作成に失敗しました。"

    # バックアップディレクトリにコピー
    try:
        shutil.copyfile(g.cfg.db.database_file, bkfname)
        logging.notice("database backup: %s", bkfname)  # type: ignore
        return "\nデータベースをバックアップしました。"
    except OSError as e:
        logging.error(e, exc_info=True)
        logging.error("Database backup failed !!!")
        return "\nデータベースのバックアップに失敗しました。"


def remarks_append(remarks: dict | list) -> None:
    """メモをDBに記録する

    Args:
        remarks (dict | list): メモに残す内容
    """

    if isinstance(remarks, dict):
        remarks = [remarks]

    if g.msg.updatable:
        with closing(dbutil.get_connection()) as cur:
            for para in remarks:
                # 親スレッドの情報
                row = cur.execute("select * from result where ts=:thread_ts", para).fetchone()
                if row:
                    if para["name"] in [v for k, v in dict(row).items() if k.endswith("_name")]:
                        cur.execute(g.sql["REMARKS_INSERT"], para)
                        logging.notice("insert: %s, user=%s", para, g.msg.user_id)  # type: ignore

                        if g.cfg.setting.reaction_ok not in lookup.api.reactions_status(ts=para.get("event_ts")):
                            slack_api.call_reactions_add(g.cfg.setting.reaction_ok, ts=para.get("event_ts"))

            cur.commit()


def remarks_delete(ts: str) -> None:
    """DBからメモを削除する

    Args:
        ts (str): 削除対象レコードのタイムスタンプ
    """

    if g.msg.updatable:
        with closing(dbutil.get_connection()) as cur:
            cur.execute(g.sql["REMARKS_DELETE_ONE"], (ts,))
            count = cur.execute("select changes();").fetchone()[0]
            cur.commit()

        if count:
            logging.notice("ts=%s, user=%s, count=%s", ts, g.msg.user_id, count)  # type: ignore

        if g.msg.status != "message_deleted":
            if g.cfg.setting.reaction_ok in lookup.api.reactions_status():
                slack_api.call_reactions_remove(g.cfg.setting.reaction_ok, ts=ts)


def remarks_delete_compar(para: dict) -> None:
    """DBからメモを削除する(突合)

    Args:
        para (dict): パラメータ
    """

    ch: str | None

    with closing(dbutil.get_connection()) as cur:
        cur.execute(g.sql["REMARKS_DELETE_COMPAR"], para)
        cur.commit()

        left = cur.execute("select count() from remarks where event_ts=:event_ts;", para).fetchone()[0]

    if g.msg.channel_id:
        ch = g.msg.channel_id
    else:
        ch = lookup.api.get_channel_id()

    icon = lookup.api.reactions_status(ts=para.get("event_ts"))
    if g.cfg.setting.reaction_ok in icon and left == 0:
        slack_api.call_reactions_remove(g.cfg.setting.reaction_ok, ch=ch, ts=para.get("event_ts"))


def check_remarks() -> None:
    """メモの内容を拾ってDBに格納する"""
    game_result = lookup.db.exsist_record(g.msg.thread_ts)
    if not game_result.is_default():  # ゲーム結果のスレッドになっているか
        g.cfg.results.initialization()
        g.cfg.results.unregistered_replace = False  # ゲスト無効

        remarks: list = []
        for name, matter in zip(g.msg.argument[0::2], g.msg.argument[1::2]):
            remark = {
                "thread_ts": g.msg.thread_ts,
                "event_ts": g.msg.event_ts,
                "name": formatter.name_replace(name),
                "matter": matter,
            }
            if remark["name"] in game_result.to_list() and remark not in remarks:
                remarks.append(remark)

        match g.msg.status:
            case "message_append":
                remarks_append(remarks)
            case "message_changed":
                remarks_delete(g.msg.event_ts)
                remarks_append(remarks)
            case "message_deleted":
                remarks_delete(g.msg.event_ts)


def reprocessing_remarks():
    """スレッドの内容を再処理"""
    res = lookup.api.get_conversations()
    msg = res.get("messages")

    if msg:
        reply_count = msg[0].get("reply_count", 0)
        g.msg.thread_ts = msg[0].get("ts")

        for x in range(1, reply_count + 1):
            g.msg.event_ts = msg[x].get("ts")
            text = msg[x].get("text")
            logging.info("(%s/%s) thread_ts=%s, event_ts=%s, %s", x, reply_count, g.msg.thread_ts, g.msg.event_ts, text)

            if text:
                g.msg.keyword = text.split()[0]
                g.msg.argument = text.split()[1:]

                if re.match(rf"^{g.cfg.cw.remarks_word}", g.msg.keyword):
                    check_remarks()


def score_reactions(param: dict):
    """素点合計をチェックしリアクションを付ける

    Args:
        param (dict): 素点データ
    """

    correct_score = g.cfg.mahjong.origin_point * 4  # 配給原点
    rpoint_sum = param["rpoint_sum"]  # 素点合計

    if param["reactions_data"]:
        icon = param["reactions_data"]
    else:
        icon = lookup.api.reactions_status()

    if rpoint_sum == correct_score:
        if g.cfg.setting.reaction_ng in icon:
            slack_api.call_reactions_remove(g.cfg.setting.reaction_ng)
        if g.cfg.setting.reaction_ok not in icon:
            slack_api.call_reactions_add(g.cfg.setting.reaction_ok)
    else:
        if g.cfg.setting.reaction_ok in icon:
            slack_api.call_reactions_remove(g.cfg.setting.reaction_ok)
        if g.cfg.setting.reaction_ng not in icon:
            slack_api.call_reactions_add(g.cfg.setting.reaction_ng)

        slack_api.post_message(
            message.reply(message="invalid_score", rpoint_sum=rpoint_sum),
            g.msg.event_ts,
        )
