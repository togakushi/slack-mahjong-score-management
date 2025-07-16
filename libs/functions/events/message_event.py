"""
libs/functions/events/message_event.py
"""

import logging
import re

import libs.commands.graph.slackpost
import libs.commands.ranking.slackpost
import libs.commands.report.slackpost
import libs.commands.results.slackpost
import libs.global_value as g
from cls.score import GameResult
from integrations import factory
from integrations.base import MessageParserInterface
from integrations.slack import comparison, functions
from libs.data import lookup, modify
from libs.functions import compose, message
from libs.utils import formatter


def main(body):
    """ポストされた内容で処理を分岐

    Args:
        client (slack_bolt.App.client): slack_boltオブジェクト
        body (dict): ポストされたデータ
    """

    api_adapter = factory.select_adapter(g.selected_service)
    m = factory.select_parser(g.selected_service)
    m.parser(body)

    logging.trace(body)  # type: ignore
    logging.info(
        "status=%s, event_ts=%s, thread_ts=%s, in_thread=%s, keyword=%s, user_id=%s,",
        m.data.status, m.data.event_ts, m.data.thread_ts, m.in_thread, m.keyword, m.data.user_id,
    )

    # 許可されていないユーザのポストは処理しない
    if m.data.user_id in g.cfg.setting.ignore_userid:
        logging.trace("event skip[ignore user]: %s", m.data.user_id)  # type: ignore
        return

    # 投稿済みメッセージが削除された場合
    if m.data.status == "message_deleted":
        message_deleted(m)
        return

    # キーワード処理
    match m.keyword:
        # ヘルプ
        case x if re.match(rf"^{g.cfg.cw.help}$", x):
            # ヘルプメッセージ
            m.post.message = compose.msg_help.event_message()
            api_adapter.post_message(m)
            # メンバーリスト
            m.post.title, m.post.message = lookup.textdata.get_members_list()
            api_adapter.post_text(m)

        # 成績管理系コマンド
        case x if re.match(rf"^{g.cfg.cw.results}$", x):
            libs.commands.results.slackpost.main(m)
        case x if re.match(rf"^{g.cfg.cw.graph}$", x):
            libs.commands.graph.slackpost.main(m)
        case x if re.match(rf"^{g.cfg.cw.ranking}$", x):
            libs.commands.ranking.slackpost.main(m)
        case x if re.match(rf"^{g.cfg.cw.report}$", x):
            libs.commands.report.slackpost.main(m)

        # データベース関連コマンド
        case x if re.match(rf"^{g.cfg.cw.check}$", x):
            comparison.main(m)
        case x if re.match(rf"^Reminder: {g.cfg.cw.check}$", str(m.data.text)):  # Reminderによる突合
            logging.notice("Reminder: %s", g.cfg.cw.check)  # type: ignore
            comparison.main(m)

        # メンバーリスト/チームリスト
        case x if re.match(rf"^{g.cfg.cw.member}$", x):
            m.post.title, m.post.message = lookup.textdata.get_members_list()
            api_adapter.post_text(m)
        case x if re.match(rf"^{g.cfg.cw.team}$", x):
            m.post.title = "チーム一覧"
            m.post.message = lookup.textdata.get_team_list()
            api_adapter.post_text(m)

        case _ as x:
            other_words(x, m)


def other_words(word: str, m: MessageParserInterface):
    """コマンド以外のワードの処理

    Args:
        word (str): 入力ワード
        m (MessageParserInterface): メッセージデータ
    """

    if re.match(rf"^{g.cfg.cw.remarks_word}$", word) and m.in_thread:  # 追加メモ
        if lookup.db.exsist_record(m.data.thread_ts).has_valid_data():
            modify.check_remarks(m)
    else:
        # スコア取り出し
        detection = GameResult(ts=m.data.event_ts, rule_version=g.cfg.mahjong.rule_version)
        detection.set(**m.get_score(g.cfg.search.keyword))

        if detection:  # 結果報告フォーマットに一致したポストの処理
            # 名前ブレ修正
            g.params.update(unregistered_replace=False)  # ゲスト無効
            g.params.update(individual=True)  # チーム戦オフ
            for k, p in detection.to_dict().items():
                if str(k).endswith("_name"):
                    detection.set(**{k: formatter.name_replace(str(p), False)})
                    continue
                detection.set(**{k: str(p)})

            detection.calc()
            match m.data.status:
                case "message_append":
                    message_append(detection, m)
                case "message_changed":
                    message_changed(detection, m)
        else:
            record_data = lookup.db.exsist_record(m.data.event_ts)
            if record_data and m.data.status == "message_changed":
                message_deleted(m)


def message_append(detection: GameResult, m: MessageParserInterface):
    """メッセージの追加処理

    Args:
        detection (GameResult): スコアデータ
        m (MessageParserInterface): メッセージデータ
    """

    api_adapter = factory.select_adapter(g.selected_service)

    if not m.in_thread or (m.in_thread == g.cfg.setting.thread_report):
        modify.db_insert(detection, m)
        functions.score_verification(detection, m)
    else:
        m.post.message_type = "inside_thread"
        m.post.thread = True
        m.post.message = message.random_reply(m)
        api_adapter.post_message(m)
        logging.notice("skip (inside thread). event_ts=%s, thread_ts=%s", m.data.event_ts, m.data.thread_ts)  # type: ignore


def message_changed(detection: GameResult, m: MessageParserInterface):
    """メッセージの変更処理

    Args:
        detection (GameResult): スコアデータ
        m (MessageParserInterface): メッセージデータ
    """

    api_adapter = factory.select_adapter(g.selected_service)

    record_data = lookup.db.exsist_record(m.data.event_ts)
    print("=" * 80)
    print(detection.to_dict())
    print(record_data.to_dict())
    print(">>>", vars(m.data))

    if detection.to_dict() == record_data.to_dict():  # スコア比較
        return  # 変更箇所がなければ何もしない
    if g.cfg.setting.thread_report == m.in_thread:
        if record_data.has_valid_data():
            if record_data.rule_version == g.cfg.mahjong.rule_version:
                modify.db_update(detection, m)
                functions.score_verification(detection, m)
            else:
                logging.notice("skip (rule_version not match). event_ts=%s", m.data.event_ts)  # type: ignore
        else:
            modify.db_insert(detection, m)
            functions.score_verification(detection, m)
            modify.reprocessing_remarks(m)
    else:
        m.post.message_type = "inside_thread"
        m.post.thread = True
        m.post.message = message.random_reply(m)
        api_adapter.post_message(m)
        logging.notice("skip (inside thread). event_ts=%s, thread_ts=%s", m.data.event_ts, m.data.thread_ts)  # type: ignore


def message_deleted(m: MessageParserInterface):
    """メッセージの削除処理

    Args:
        m (MessageParserInterface): メッセージデータ
    """

    api_adapter = factory.select_adapter(g.selected_service)

    if re.match(rf"^{g.cfg.cw.remarks_word}", m.keyword):  # 追加メモ
        delete_list = modify.remarks_delete(m)
    else:
        delete_list = modify.db_delete(m)

    api_adapter.reactions.all_remove(delete_list, ch=m.data.channel_id)
