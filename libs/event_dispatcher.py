"""
libs/event_dispatcher.py
"""

import logging
import re

import libs.commands.dispatcher
import libs.global_value as g
from cls.score import GameResult
from integrations import factory
from integrations.protocols import MessageParserProtocol
from integrations.slack import comparison, functions
from libs.data import lookup, modify
from libs.functions import compose, message
from libs.registry import member, team
from libs.utils import formatter


def dispatch_by_keyword(m: MessageParserProtocol):
    """メイン処理"""

    api_adapter = factory.select_adapter(g.selected_service)

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
        case x if re.match(rf"^{g.cfg.cw.results}$", x) or (m.is_command and x in g.cfg.alias.results):
            m.command_type = "results"
            libs.commands.dispatcher.main(m)
        case x if re.match(rf"^{g.cfg.cw.graph}$", x) or (m.is_command and x in g.cfg.alias.graph):
            m.command_type = "graph"
            libs.commands.dispatcher.main(m)
        case x if re.match(rf"^{g.cfg.cw.ranking}$", x) or (m.is_command and x in g.cfg.alias.ranking):
            m.command_type = "ranking"
            libs.commands.dispatcher.main(m)
        case x if re.match(rf"^{g.cfg.cw.report}$", x) or (m.is_command and x in g.cfg.alias.report):
            m.command_type = "report"
            libs.commands.dispatcher.main(m)

        # データベース関連コマンド
        case x if re.match(rf"^{g.cfg.cw.check}$", x) or (m.is_command and x in g.cfg.alias.check):
            comparison.main(m)
        case x if re.match(rf"^Reminder: {g.cfg.cw.check}$", str(m.data.text)):  # Reminderによる突合
            logging.notice("Reminder: %s", g.cfg.cw.check)  # type: ignore
            comparison.main(m)
        case x if m.is_command and x in g.cfg.alias.download:
            m.post.file_list = [{m.post.title: g.cfg.db.database_file}]
            api_adapter.fileupload(m)

        # メンバーリスト/チームリスト
        case x if re.match(rf"^{g.cfg.cw.member}$", x) or (m.is_command and x in g.cfg.alias.member):
            m.post.title, m.post.message = lookup.textdata.get_members_list()
            api_adapter.post_text(m)
        case x if re.match(rf"^{g.cfg.cw.team}$", x) or (m.is_command and x in g.cfg.alias.team_list):
            m.post.title = "チーム一覧"
            m.post.message = lookup.textdata.get_team_list()
            api_adapter.post_text(m)

        # メンバー管理系コマンド
        case x if m.is_command and x in g.cfg.alias.member:
            m.post.title, m.post.message = lookup.textdata.get_members_list()
            api_adapter.post_text(m)
        case x if m.is_command and x in g.cfg.alias.add:
            m.post.message = member.append(m.argument)
            api_adapter.post_message(m)
        case x if m.is_command and x in g.cfg.alias.delete:
            m.post.message = member.remove(m.argument)
            api_adapter.post_message(m)

        # チーム管理系コマンド
        case x if m.is_command and x in g.cfg.alias.team_create:
            m.post.message = team.create(m.argument)
            api_adapter.post_message(m)
        case x if m.is_command and x in g.cfg.alias.team_del:
            m.post.message = team.delete(m.argument)
            api_adapter.post_message(m)
        case x if m.is_command and x in g.cfg.alias.team_add:
            m.post.message = team.append(m.argument)
            api_adapter.post_message(m)
        case x if m.is_command and x in g.cfg.alias.team_remove:
            m.post.message = team.remove(m.argument)
            api_adapter.post_message(m)
        case x if m.is_command and x in g.cfg.alias.team_list:
            m.post.message = lookup.textdata.get_team_list()
            api_adapter.post_message(m)
        case x if m.is_command and x in g.cfg.alias.team_clear:
            m.post.message = team.clear()
            api_adapter.post_message(m)

        # その他
        case _ as x:
            if m.is_command:
                m.post.message = compose.msg_help.slash_command(g.cfg.setting.slash_command)
                api_adapter.post_message(m)
            else:
                other_words(x, m)


def other_words(word: str, m: MessageParserProtocol):
    """コマンド以外のワードの処理

    Args:
        word (str): 入力ワード
        m (MessageParserProtocol): メッセージデータ
    """

    if re.match(rf"^{g.cfg.cw.remarks_word}$", word) and m.in_thread:  # 追加メモ
        if lookup.db.exsist_record(m.data.thread_ts).has_valid_data():
            modify.check_remarks(m)
    else:
        # スコア取り出し
        detection = GameResult(**m.get_score(g.cfg.search.keyword), **g.cfg.mahjong.to_dict())
        if detection:  # 結果報告フォーマットに一致したポストの処理
            # 名前ブレ修正
            g.params.update(unregistered_replace=False)  # ゲスト無効
            g.params.update(individual=True)  # チーム戦オフ
            for k, p in detection.to_dict().items():
                if str(k).endswith("_name"):
                    detection.set(**{k: formatter.name_replace(str(p), False)})
                    continue
                detection.set(**{k: str(p)})

            match m.data.status:
                case "message_append":
                    message_append(detection, m)
                case "message_changed":
                    message_changed(detection, m)
        else:
            record_data = lookup.db.exsist_record(m.data.event_ts)
            if record_data and m.data.status == "message_changed":
                message_deleted(m)


def message_append(detection: GameResult, m: MessageParserProtocol):
    """メッセージの追加処理

    Args:
        detection (GameResult): スコアデータ
        m (MessageParserProtocol): メッセージデータ
    """

    api_adapter = factory.select_adapter(g.selected_service)

    if not m.in_thread or (m.in_thread == g.cfg.setting.thread_report):
        modify.db_insert(detection, m)
        functions.score_verification(detection, m)
    else:
        m.post.thread = True
        message.random_reply(m, "inside_thread")
        api_adapter.post_message(m)
        logging.notice("skip (inside thread). event_ts=%s, thread_ts=%s", m.data.event_ts, m.data.thread_ts)  # type: ignore


def message_changed(detection: GameResult, m: MessageParserProtocol):
    """メッセージの変更処理

    Args:
        detection (GameResult): スコアデータ
        m (MessageParserProtocol): メッセージデータ
    """

    api_adapter = factory.select_adapter(g.selected_service)
    record_data = lookup.db.exsist_record(m.data.event_ts)

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
        m.post.thread = True
        message.random_reply(m, "inside_thread")
        api_adapter.post_message(m)
        logging.notice("skip (inside thread). event_ts=%s, thread_ts=%s", m.data.event_ts, m.data.thread_ts)  # type: ignore


def message_deleted(m: MessageParserProtocol):
    """メッセージの削除処理

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    api_adapter = factory.select_adapter(g.selected_service)

    if re.match(rf"^{g.cfg.cw.remarks_word}", m.keyword):  # 追加メモ
        delete_list = modify.remarks_delete(m)
    else:
        delete_list = modify.db_delete(m)

    for ts in delete_list:
        api_adapter.reactions.remove(icon=m.reaction_ok, ch=m.data.channel_id, ts=ts)
        api_adapter.reactions.remove(icon=m.reaction_ng, ch=m.data.channel_id, ts=ts)
