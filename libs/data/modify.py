"""
libs/data/modify.py
"""

import logging
import os
import re
import shutil
import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING, cast

import libs.global_value as g
from cls.timekit import ExtendedDatetime as ExtDt
from libs.data import lookup
from libs.functions import message
from libs.utils import dbutil, formatter

if TYPE_CHECKING:
    from cls.score import GameResult
    from integrations.protocols import MessageParserProtocol
    from libs.types import RemarkDict


def db_insert(detection: "GameResult", m: "MessageParserProtocol") -> int:
    """スコアデータをDBに追加する

    Args:
        detection (GameResult): スコアデータ
        m (MessageParserProtocol): メッセージデータ

    Returns:
        int: _description_
    """

    changes: int = 0
    if m.check_updatable:
        with closing(dbutil.connection(g.cfg.setting.database_file)) as cur:
            try:
                cur.execute(dbutil.query("RESULT_INSERT"), {
                    "playtime": ExtDt(float(detection.ts)).format("sql"),
                    "rpoint_sum": detection.rpoint_sum(),
                    **detection.to_dict(),
                })
                changes = cur.total_changes
                cur.commit()
            except sqlite3.IntegrityError as err:
                logging.error(err)
        logging.info("%s", detection.to_text("logging"))
        _score_check(detection, m)
    else:
        message.random_reply(m, "restricted_channel")

    return changes


def db_update(detection: "GameResult", m: "MessageParserProtocol") -> None:
    """スコアデータを変更する

    Args:
        detection (GameResult): スコアデータ
        m (MessageParserProtocol): メッセージデータ
    """

    detection.calc()
    if m.check_updatable:
        with closing(dbutil.connection(g.cfg.setting.database_file)) as cur:
            cur.execute(dbutil.query("RESULT_UPDATE"), {
                "playtime": ExtDt(float(detection.ts)).format("sql"),
                "rpoint_sum": detection.rpoint_sum(),
                **detection.to_dict(),
            })
            cur.commit()
        logging.info("%s", detection.to_text("logging"))
        _score_check(detection, m)
    else:
        message.random_reply(m, "restricted_channel")


def db_delete(m: "MessageParserProtocol"):
    """スコアデータを削除する

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    if m.check_updatable:
        with closing(dbutil.connection(g.cfg.setting.database_file)) as cur:
            # ゲーム結果の削除
            cur.execute(dbutil.query("RESULT_DELETE"), (m.data.event_ts,))
            if (delete_result := cur.execute("select changes();").fetchone()[0]):
                m.status.target_ts.append(m.data.event_ts)
                logging.info("result: ts=%s, count=%s", m.data.event_ts, delete_result)
            # メモの削除
            if (remark_list := cur.execute("select event_ts from remarks where thread_ts=?", (m.data.event_ts,)).fetchall()):
                cur.execute(dbutil.query("REMARKS_DELETE_ALL"), (m.data.event_ts,))
                if (delete_remark := cur.execute("select changes();").fetchone()[0]):
                    m.status.target_ts.extend([x.get("event_ts") for x in list(map(dict, remark_list))])
                    logging.info("remark: ts=%s, count=%s", m.data.event_ts, delete_remark)
            cur.commit()

        m.status.action = "delete"


def db_backup() -> str:
    """データベースのバックアップ

    Returns:
        str: 動作結果メッセージ
    """

    if not g.cfg.setting.backup_dir:  # バックアップ設定がされていない場合は何もしない
        return ""

    fname = os.path.splitext(g.cfg.setting.database_file)[0]
    fext = os.path.splitext(g.cfg.setting.database_file)[1]
    bktime = ExtDt().format("ext")
    bkfname = os.path.join(g.cfg.setting.backup_dir, os.path.basename(f"{fname}_{bktime}{fext}"))

    if not os.path.isdir(g.cfg.setting.backup_dir):  # バックアップディレクトリ作成
        try:
            os.mkdir(g.cfg.setting.backup_dir)
        except OSError as e:
            logging.error(e, exc_info=True)
            logging.error("Database backup directory creation failed !!!")
            return "\nバックアップ用ディレクトリ作成の作成に失敗しました。"

    # バックアップディレクトリにコピー
    try:
        shutil.copyfile(g.cfg.setting.database_file, bkfname)
        logging.info("database backup: %s", bkfname)
        return "\nデータベースをバックアップしました。"
    except OSError as e:
        logging.error(e, exc_info=True)
        logging.error("Database backup failed !!!")
        return "\nデータベースのバックアップに失敗しました。"


def remarks_append(m: "MessageParserProtocol", remarks: list["RemarkDict"]) -> None:
    """メモをDBに記録する

    Args:
        m (MessageParserProtocol): メッセージデータ
        remarks (list[RemarkDict]): メモに残す内容
    """

    if m.check_updatable:
        with closing(dbutil.connection(g.cfg.setting.database_file)) as cur:
            for para in remarks:
                # 親スレッドの情報
                row = cur.execute("select * from result where ts=:thread_ts", para).fetchone()
                if row:
                    if para["name"] in [v for k, v in dict(row).items() if str(k).endswith("_name")]:
                        cur.execute(dbutil.query("REMARKS_INSERT"), para)
                        m.status.target_ts.append(para["event_ts"])
                        m.status.target_ts.append(para["event_ts"])
                        logging.info("insert: %s, user=%s", para, m.data.user_id)
            cur.commit()

        # 後処理
        m.status.action = "change"
        m.status.reaction = True  # 対象外はINSERTしないようにガード済
        g.adapter.functions.post_processing(m)


def remarks_delete(m: "MessageParserProtocol"):
    """DBからメモを削除する

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    if m.check_updatable:
        with closing(dbutil.connection(g.cfg.setting.database_file)) as cur:
            cur.execute(dbutil.query("REMARKS_DELETE_ONE"), (m.data.event_ts,))
            cur.commit()
            if (count := cur.execute("select changes();").fetchone()[0]):
                m.status.target_ts.append(m.data.event_ts)
                logging.info("ts=%s, user=%s, count=%s", m.data.event_ts, m.data.user_id, count)
        # 後処理
        m.status.action = "delete"
        g.adapter.functions.post_processing(m)


def remarks_delete_compar(para: dict, m: "MessageParserProtocol") -> None:
    """DBからメモを削除する(突合)

    Args:
        para (dict): パラメータ
        m (MessageParserProtocol): メッセージデータ
    """

    with closing(dbutil.connection(g.cfg.setting.database_file)) as cur:
        cur.execute(dbutil.query("REMARKS_DELETE_COMPAR"), para)
        cur.commit()

        left = cur.execute("select count() from remarks where event_ts=:event_ts;", para).fetchone()[0]

    # 後処理
    m.status.action = "delete"
    m.status.target_ts.append(para["event_ts"])
    if left > 0:  # メモデータが残っているなら
        m.status.action = "change"
    g.adapter.functions.post_processing(m)


def check_remarks(m: "MessageParserProtocol") -> None:
    """メモの内容を拾ってDBに格納する

    Args:
        m (MessageParserProtocol): メッセージデータ

    """

    game_result = lookup.db.exsist_record(m.data.thread_ts)
    if game_result.has_valid_data():  # ゲーム結果のスレッドになっているか
        remarks: list["RemarkDict"] = []
        for name, matter in zip(m.argument[0::2], m.argument[1::2]):
            remark: "RemarkDict" = {
                "thread_ts": m.data.thread_ts,
                "event_ts": m.data.event_ts,
                "name": formatter.name_replace(name, not_replace=True),
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


def reprocessing_remarks(m: "MessageParserProtocol") -> None:
    """スレッドの内容を再処理

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    res = g.adapter.functions.get_conversations(m)
    msg = cast(dict, res.get("messages"))

    if msg:
        reply_count = cast(dict, msg[0]).get("reply_count", 0)
        m.data.thread_ts = str(cast(dict, msg[0]).get("ts"))

        for x in range(1, reply_count + 1):
            m.data.text = str(cast(dict, msg[x]).get("text", ""))
            if m.data.text:
                m.data.event_ts = str(cast(dict, msg[x]).get("ts"))
                logging.info("(%s/%s) thread_ts=%s, event_ts=%s, %s", x, reply_count, m.data.thread_ts, m.data.event_ts, m.data.text)
                if re.match(rf"^{g.cfg.setting.remarks_word}", m.keyword):
                    check_remarks(m)


def _score_check(detection: "GameResult", m: "MessageParserProtocol"):
    """スコアデータ格納状態を記録する

    Args:
        detection (GameResult): スコアデータ
        m (MessageParserProtocol): メッセージデータ
    """

    # 結果
    m.status.action = "change"
    m.status.target_ts.append(m.data.event_ts)
    m.status.reaction = True
    m.status.message = detection.to_text("detail")
    m.post.message = {}

    # 素点合計チェック
    if detection.deposit:
        m.status.reaction = False
        m.status.rpoint_sum = detection.rpoint_sum()
        m.post.ts = m.data.event_ts
        m.post.message.update({"0": message.random_reply(m, "invalid_score", False)})

    # プレイヤー名重複チェック
    if len(set(detection.to_list())) != 4:
        m.status.reaction = False
        m.post.ts = m.data.event_ts
        m.post.message.update({"1": message.random_reply(m, "same_player", False)})
