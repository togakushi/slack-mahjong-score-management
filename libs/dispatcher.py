"""
libs/dispatcher.py
"""

import logging
import re
from typing import TYPE_CHECKING

import libs.global_value as g
from cls.score import GameResult
from integrations import factory
from libs.data import lookup, modify
from libs.functions import message
from libs.types import StyleOptions
from libs.utils import formatter

if TYPE_CHECKING:
    from integrations.protocols import MessageParserProtocol


def by_keyword(m: "MessageParserProtocol"):
    """メイン処理"""

    logging.debug("keyword=%s, argument=%s", m.keyword, m.argument)
    logging.debug(
        "status=%s, event_ts=%s, thread_ts=%s, in_thread=%s, keyword=%s, user_id=%s,",
        m.data.status, m.data.event_ts, m.data.thread_ts, m.in_thread, m.keyword, m.data.user_id,
    )

    # 許可されていないユーザのコマンドは処理しない
    if m.ignore_user:
        logging.debug("event skip[ignore user]: %s", m.data.user_id)
        return

    # メッセージが削除された場合
    if m.data.status == "message_deleted":
        message_deleted(m)
        return

    match m.keyword:
        # キーワード実行
        case word if word in g.keyword_dispatcher and not m.is_command:
            g.keyword_dispatcher[word](m)
        # コマンド実行
        case word if word in g.command_dispatcher and m.is_command:
            g.command_dispatcher[word](m)
        # リマインダ実行
        case "Reminder:":
            if m.data.text in g.keyword_dispatcher and m.is_bot:
                g.keyword_dispatcher[m.data.text](m)
        # その他(ディスパッチテーブルにない場合)
        case _ as word:
            other_words(word, m)

    g.adapter.api.post(m)


def other_words(word: str, m: "MessageParserProtocol"):
    """コマンド以外のワードの処理

    Args:
        word (str): 入力ワード
        m (MessageParserProtocol): メッセージデータ
    """

    if re.match(rf"^{g.cfg.setting.remarks_word}$", word) and m.in_thread:  # 追加メモ
        if lookup.db.exsist_record(m.data.thread_ts).has_valid_data():
            modify.check_remarks(m)
    else:
        # スコア取り出し
        detection = GameResult(**m.get_score(g.cfg.setting.keyword), **g.cfg.mahjong.to_dict())
        if detection:  # 結果報告フォーマットに一致したポストの処理
            # 名前ブレ修正
            g.params.update(unregistered_replace=False)  # ゲスト無効
            g.params.update(individual=True)  # チーム戦オフ
            for k, p in detection.to_dict().items():
                if str(k).endswith("_name"):
                    detection.set(**{k: formatter.name_replace(str(p))})
                    continue

            match m.data.status:
                case "message_append":
                    message_append(detection, m)
                case "message_changed":
                    message_changed(detection, m)
        else:
            record_data = lookup.db.exsist_record(m.data.event_ts)
            if record_data and m.data.status == "message_changed":
                message_deleted(m)


def message_append(detection: GameResult, m: "MessageParserProtocol"):
    """メッセージの追加処理

    Args:
        detection (GameResult): スコアデータ
        m (MessageParserProtocol): メッセージデータ
    """

    if _thread_check(m):
        modify.db_insert(detection, m)
    else:
        m.post.thread = True
        m.set_data("0", message.random_reply(m, "inside_thread"), StyleOptions(key_title=False))
        logging.debug("skip (inside thread). event_ts=%s, thread_ts=%s", m.data.event_ts, m.data.thread_ts)

    g.adapter.functions.post_processing(m)


def message_changed(detection: GameResult, m: "MessageParserProtocol"):
    """メッセージの変更処理

    Args:
        detection (GameResult): スコアデータ
        m (MessageParserProtocol): メッセージデータ
    """

    record_data = lookup.db.exsist_record(m.data.event_ts)

    if detection.to_dict() == record_data.to_dict():  # スコア比較
        return  # 変更箇所がなければ何もしない
    if _thread_check(m):
        if record_data.has_valid_data():
            if record_data.rule_version == g.cfg.mahjong.rule_version:
                modify.db_update(detection, m)
            else:
                logging.debug("skip (rule_version not match). event_ts=%s", m.data.event_ts)
        else:
            modify.db_insert(detection, m)
            modify.reprocessing_remarks(m)
    else:
        m.post.thread = True
        m.set_data("0", message.random_reply(m, "inside_thread"), StyleOptions(key_title=False))
        logging.debug("skip (inside thread). event_ts=%s, thread_ts=%s", m.data.event_ts, m.data.thread_ts)

    g.adapter.functions.post_processing(m)


def message_deleted(m: "MessageParserProtocol"):
    """メッセージの削除処理

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    if re.match(rf"^{g.cfg.setting.remarks_word}", m.keyword):  # 追加メモ
        modify.remarks_delete(m)
    else:
        modify.db_delete(m)

    g.adapter.functions.post_processing(m)


def _thread_check(m: "MessageParserProtocol") -> bool:
    """スレッド内判定関数"""

    if isinstance(g.adapter, factory.slack_adapter):
        if not m.in_thread or (m.in_thread == g.adapter.conf.thread_report):
            return True
        return False
    return not m.in_thread
