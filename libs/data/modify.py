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
from cls.types import RemarkDict
from integrations import factory
from integrations.slack import api
from libs.data import lookup
from libs.functions import message
from libs.utils import dbutil, formatter


def db_insert(detection: GameResult) -> int:
    """スコアデータをDBに追加する

    Args:
        detection (GameResult): スコアデータ
    """

    api_adapter = factory.get_api_adapter(g.selected_service)

    changes: int = 0
    if g.msg.updatable:
        with closing(dbutil.get_connection()) as cur:
            cur.execute(g.sql["RESULT_INSERT"], {
                "playtime": ExtDt(float(g.msg.event_ts)).format("sql"),
                "rpoint_sum": detection.rpoint_sum(),
                **detection.to_dict(),
            })
            changes = cur.total_changes
            cur.commit()
        logging.notice("%s, user=%s", detection, g.msg.user_id)  # type: ignore
    else:
        api_adapter.post_message(message.random_reply(message="restricted_channel"), g.msg.event_ts)

    return changes


def db_update(detection: GameResult) -> None:
    """スコアデータを変更する

    Args:
        detection (GameResult): スコアデータ
    """

    api_adapter = factory.get_api_adapter(g.selected_service)

    detection.calc(ts=g.msg.event_ts)
    if g.msg.updatable:
        with closing(dbutil.get_connection()) as cur:
            cur.execute(g.sql["RESULT_UPDATE"], {
                "playtime": ExtDt(float(g.msg.event_ts)).format("sql"),
                "rpoint_sum": detection.rpoint_sum(),
                **detection.to_dict(),
            })
            cur.commit()
        logging.notice("%s, user=%s", detection, g.msg.user_id)  # type: ignore
    else:
        api_adapter.post_message(message.random_reply(message="restricted_channel"), g.msg.event_ts)


def db_delete(ts: str) -> list:
    """スコアデータを削除する

    Args:
        ts (str): 削除対象レコードのタイムスタンプ

    Returns:
        list: 削除したタイムスタンプ
    """

    delete_list: list = []
    if g.msg.updatable:
        with closing(dbutil.get_connection()) as cur:
            # ゲーム結果の削除
            cur.execute(g.sql["RESULT_DELETE"], (ts,))
            if (delete_result := cur.execute("select changes();").fetchone()[0]):
                delete_list.append(ts)
                logging.notice("result: ts=%s, user=%s, count=%s", ts, g.msg.user_id, delete_result)  # type: ignore

            # メモの削除
            if (remark_list := cur.execute("select event_ts from remarks where thread_ts=?", (ts,)).fetchall()):
                cur.execute(g.sql["REMARKS_DELETE_ALL"], (ts,))
                if (delete_remark := cur.execute("select changes();").fetchone()[0]):
                    delete_list.extend([x.get("event_ts") for x in list(map(dict, remark_list))])
                    logging.notice("remark: ts=%s, user=%s, count=%s", ts, g.msg.user_id, delete_remark)  # type: ignore

            cur.commit()

    return delete_list


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


def remarks_append(remarks: list[RemarkDict]) -> None:
    """メモをDBに記録する

    Args:
        remarks (list[RemarkDict]): メモに残す内容
    """

    api_adapter = factory.get_api_adapter(g.selected_service)

    if g.msg.updatable:
        with closing(dbutil.get_connection()) as cur:
            for para in remarks:
                # 親スレッドの情報
                row = cur.execute("select * from result where ts=:thread_ts", para).fetchone()
                if row:
                    if para["name"] in [v for k, v in dict(row).items() if k.endswith("_name")]:
                        cur.execute(g.sql["REMARKS_INSERT"], para)
                        logging.notice("insert: %s, user=%s", para, g.msg.user_id)  # type: ignore

                        if g.cfg.setting.reaction_ok not in api_adapter.reactions_status(ts=para.get("event_ts")):
                            api.call_reactions_add(g.cfg.setting.reaction_ok, ts=para.get("event_ts"))

            cur.commit()


def remarks_delete(ts: str) -> list:
    """DBからメモを削除する

    Args:
        ts (str): 削除対象レコードのタイムスタンプ

    Returns:
        list: 削除したタイムスタンプ
    """

    delete_list: list = []
    if g.msg.updatable:
        with closing(dbutil.get_connection()) as cur:
            cur.execute(g.sql["REMARKS_DELETE_ONE"], (ts,))
            cur.commit()
            if (count := cur.execute("select changes();").fetchone()[0]):
                delete_list.append(ts)
                logging.notice("ts=%s, user=%s, count=%s", ts, g.msg.user_id, count)  # type: ignore

    return delete_list


def remarks_delete_compar(para: dict) -> None:
    """DBからメモを削除する(突合)

    Args:
        para (dict): パラメータ
    """

    api_adapter = factory.get_api_adapter(g.selected_service)

    with closing(dbutil.get_connection()) as cur:
        cur.execute(g.sql["REMARKS_DELETE_COMPAR"], para)
        cur.commit()

        left = cur.execute("select count() from remarks where event_ts=:event_ts;", para).fetchone()[0]

    if not (ch := g.msg.channel_id):
        ch = api_adapter.get_channel_id()

    icon = api_adapter.reactions_status(ts=para.get("event_ts"))
    if g.cfg.setting.reaction_ok in icon and left == 0:
        api.call_reactions_remove(g.cfg.setting.reaction_ok, ch=ch, ts=para.get("event_ts"))


def check_remarks() -> None:
    """メモの内容を拾ってDBに格納する"""
    game_result = lookup.db.exsist_record(g.msg.thread_ts)
    if game_result.has_valid_data():  # ゲーム結果のスレッドになっているか
        g.cfg.results.initialization()
        g.cfg.results.unregistered_replace = False  # ゲスト無効

        remarks: list[RemarkDict] = []
        for name, matter in zip(g.msg.argument[0::2], g.msg.argument[1::2]):
            remark: RemarkDict = {
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


def reprocessing_remarks() -> None:
    """スレッドの内容を再処理"""

    api_adapter = factory.get_api_adapter(g.selected_service)

    res = api_adapter.get_conversations()
    msg = res.get("messages")

    if msg:
        reply_count = msg[0].get("reply_count", 0)
        g.msg.thread_ts = msg[0].get("ts")

        for x in range(1, reply_count + 1):
            g.msg.event_ts = msg[x].get("ts")
            text = str(msg[x].get("text", ""))
            logging.info("(%s/%s) thread_ts=%s, event_ts=%s, %s", x, reply_count, g.msg.thread_ts, g.msg.event_ts, text)

            if text:
                g.msg.keyword = text.split()[0]
                g.msg.argument = text.split()[1:]

                if re.match(rf"^{g.cfg.cw.remarks_word}", g.msg.keyword):
                    check_remarks()
