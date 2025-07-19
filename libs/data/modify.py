"""
lib/data/modify.py
"""

import logging
import os
import re
import shutil
import sqlite3
from contextlib import closing
from typing import cast

import libs.global_value as g
from cls.score import GameResult
from cls.timekit import ExtendedDatetime as ExtDt
from cls.types import RemarkDict
from integrations import factory
from integrations.protocols import MessageParserProtocol
from libs.data import lookup
from libs.functions import message
from libs.utils import dbutil, formatter


def db_insert(detection: GameResult, m: MessageParserProtocol) -> int:
    """スコアデータをDBに追加する

    Args:
        detection (GameResult): スコアデータ
        m (MessageParserProtocol): メッセージデータ

    Returns:
        int: _description_
    """

    api_adapter = factory.select_adapter(g.selected_service)

    changes: int = 0
    if m.check_updatable:
        with closing(dbutil.get_connection()) as cur:
            try:
                cur.execute(g.sql["RESULT_INSERT"], {
                    "playtime": ExtDt(float(detection.ts)).format("sql"),
                    "rpoint_sum": detection.rpoint_sum(),
                    **detection.to_dict(),
                })
                changes = cur.total_changes
                cur.commit()
            except sqlite3.IntegrityError as err:
                logging.error(err)
        logging.notice("%s", detection.to_text("logging"))  # type: ignore
    else:
        m.post.message_type = "restricted_channel"
        m.post.message = message.random_reply(m)
        api_adapter.post_message(m)

    return changes


def db_update(detection: GameResult, m: MessageParserProtocol) -> None:
    """スコアデータを変更する

    Args:
        detection (GameResult): スコアデータ
        m (MessageParserProtocol): メッセージデータ
    """

    api_adapter = factory.select_adapter(g.selected_service)

    detection.calc()
    if m.check_updatable:
        with closing(dbutil.get_connection()) as cur:
            cur.execute(g.sql["RESULT_UPDATE"], {
                "playtime": ExtDt(float(detection.ts)).format("sql"),
                "rpoint_sum": detection.rpoint_sum(),
                **detection.to_dict(),
            })
            cur.commit()
        logging.notice("%s", detection.to_text("logging"))  # type: ignore
    else:
        m.post.message_type = "restricted_channel"
        m.post.message = message.random_reply(m)
        api_adapter.post_message(m)


def db_delete(m: MessageParserProtocol) -> list:
    """スコアデータを削除する

    Args:
        m (MessageParserProtocol): メッセージデータ

    Returns:
        list: 削除したタイムスタンプ
    """

    delete_list: list = []
    if m.check_updatable:
        with closing(dbutil.get_connection()) as cur:
            # ゲーム結果の削除
            cur.execute(g.sql["RESULT_DELETE"], (m.data.event_ts,))
            if (delete_result := cur.execute("select changes();").fetchone()[0]):
                delete_list.append(m.data.event_ts)
                logging.notice("result: ts=%s, count=%s", m.data.event_ts, delete_result)  # type: ignore

            # メモの削除
            if (remark_list := cur.execute("select event_ts from remarks where thread_ts=?", (m.data.event_ts,)).fetchall()):
                cur.execute(g.sql["REMARKS_DELETE_ALL"], (m.data.event_ts,))
                if (delete_remark := cur.execute("select changes();").fetchone()[0]):
                    delete_list.extend([x.get("event_ts") for x in list(map(dict, remark_list))])
                    logging.notice("remark: ts=%s, count=%s", m.data.event_ts, delete_remark)  # type: ignore

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


def remarks_append(m: MessageParserProtocol, remarks: list[RemarkDict]) -> None:
    """メモをDBに記録する

    Args:
        m (MessageParserProtocol): メッセージデータ
        remarks (list[RemarkDict]): メモに残す内容
    """

    api_adapter = factory.select_adapter(g.selected_service)

    if m.check_updatable:
        with closing(dbutil.get_connection()) as cur:
            for para in remarks:
                # 親スレッドの情報
                row = cur.execute("select * from result where ts=:thread_ts", para).fetchone()
                if row:
                    if para["name"] in [v for k, v in dict(row).items() if str(k).endswith("_name")]:
                        cur.execute(g.sql["REMARKS_INSERT"], para)
                        logging.notice("insert: %s, user=%s", para, m.data.user_id)  # type: ignore

                        if not (ch := m.data.channel_id):
                            ch = api_adapter.lookup.get_channel_id()

                        # リアクション処理
                        reactions = api_adapter.reactions.status(ts=para["event_ts"], ch=ch)
                        if not reactions.get("ok"):
                            api_adapter.reactions.append(m.reaction_ok, ts=para["event_ts"], ch=ch)
                        if reactions.get("ng"):
                            api_adapter.reactions.remove(m.reaction_ng, ts=para["event_ts"], ch=ch)

            cur.commit()


def remarks_delete(m: MessageParserProtocol) -> list:
    """DBからメモを削除する

    Args:
        m (MessageParserProtocol): メッセージデータ

    Returns:
        list: 削除したタイムスタンプ
    """

    delete_list: list = []
    if m.check_updatable:
        with closing(dbutil.get_connection()) as cur:
            cur.execute(g.sql["REMARKS_DELETE_ONE"], (m.data.event_ts,))
            cur.commit()
            if (count := cur.execute("select changes();").fetchone()[0]):
                delete_list.append(m.data.event_ts)
                logging.notice("ts=%s, user=%s, count=%s", m.data.event_ts, m.data.user_id, count)  # type: ignore

    return delete_list


def remarks_delete_compar(para: dict, m: MessageParserProtocol) -> None:
    """DBからメモを削除する(突合)

    Args:
        para (dict): パラメータ
        m (MessageParserProtocol): メッセージデータ
    """

    api_adapter = factory.select_adapter(g.selected_service)

    with closing(dbutil.get_connection()) as cur:
        cur.execute(g.sql["REMARKS_DELETE_COMPAR"], para)
        cur.commit()

        left = cur.execute("select count() from remarks where event_ts=:event_ts;", para).fetchone()[0]

    if not (ch := m.data.channel_id):
        ch = api_adapter.lookup.get_channel_id()

    reactions = api_adapter.reactions.status(ch=ch, ts=para["event_ts"])
    if reactions.get("ok") and left == 0:
        api_adapter.reactions.remove(g.cfg.setting.reaction_ok, ch=ch, ts=para["event_ts"])


def check_remarks(m: MessageParserProtocol) -> None:
    """メモの内容を拾ってDBに格納する

    Args:
        m (MessageParserProtocol): メッセージデータ

    """

    game_result = lookup.db.exsist_record(m.data.thread_ts)
    if game_result.has_valid_data():  # ゲーム結果のスレッドになっているか
        g.cfg.results.initialization()
        g.cfg.results.unregistered_replace = False  # ゲスト無効

        remarks: list[RemarkDict] = []
        for name, matter in zip(m.argument[0::2], m.argument[1::2]):
            remark: RemarkDict = {
                "thread_ts": m.data.thread_ts,
                "event_ts": m.data.event_ts,
                "name": formatter.name_replace(name),
                "matter": matter,
            }
            if remark["name"] in game_result.to_list() and remark not in remarks:
                remarks.append(remark)

        match m.data.status:
            case "message_append":
                remarks_append(m, remarks)
            case "message_changed":
                remarks_delete(m)
                remarks_append(m, remarks)
            case "message_deleted":
                remarks_delete(m)


def reprocessing_remarks(m: MessageParserProtocol) -> None:
    """スレッドの内容を再処理

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    api_adapter = factory.select_adapter(g.selected_service)

    res = api_adapter.get_conversations(m)
    msg = cast(dict, res.get("messages"))

    if msg:
        reply_count = cast(dict, msg[0]).get("reply_count", 0)
        m.data.thread_ts = str(cast(dict, msg[0]).get("ts"))

        for x in range(1, reply_count + 1):
            m.data.text = str(cast(dict, msg[x]).get("text", ""))
            if m.data.text:
                m.data.event_ts = str(cast(dict, msg[x]).get("ts"))
                logging.info("(%s/%s) thread_ts=%s, event_ts=%s, %s", x, reply_count, m.data.thread_ts, m.data.event_ts, m.data.text)
                if re.match(rf"^{g.cfg.cw.remarks_word}", m.keyword):
                    check_remarks(m)
