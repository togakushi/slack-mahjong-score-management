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
from libs.data import lookup, modify
from libs.functions import compose, message
from libs.registry import member, team
from libs.utils import formatter


def dispatch_by_keyword(m: MessageParserProtocol):
    """メイン処理"""

    adapter = factory.select_adapter(g.selected_service)

    logging.info(
        "status=%s, event_ts=%s, thread_ts=%s, in_thread=%s, keyword=%s, user_id=%s,",
        m.data.status, m.data.event_ts, m.data.thread_ts, m.in_thread, m.keyword, m.data.user_id,
    )

    # 許可されていないユーザのポストは処理しない
    if isinstance(g.app_config, factory.slack.config.AppConfig):
        if m.data.user_id in g.app_config.ignore_userid:
            logging.trace("event skip[ignore user]: %s", m.data.user_id)  # type: ignore
            return

    # 投稿済みメッセージが削除された場合
    if m.data.status == "message_deleted":
        message_deleted(m)
        return

    match m.keyword:
        # ヘルプ
        case x if re.match(rf"^{g.cfg.setting.help}$", x):
            # ヘルプメッセージ
            m.post.message = compose.msg_help.event_message()
            m.post.ts = m.data.event_ts
            m.post.key_header = False
            # メンバーリスト
            m.post.message = lookup.textdata.get_members_list()
            m.post.codeblock = True
            m.post.key_header = True

        # 成績管理系コマンド
        case x if re.match(rf"^{g.cfg.cw.results}$", x) or (m.is_command and x in g.cfg.alias.results):
            m.data.command_type = "results"
            libs.commands.dispatcher.main(m)
        case x if re.match(rf"^{g.cfg.cw.graph}$", x) or (m.is_command and x in g.cfg.alias.graph):
            m.data.command_type = "graph"
            libs.commands.dispatcher.main(m)
        case x if re.match(rf"^{g.cfg.cw.ranking}$", x) or (m.is_command and x in g.cfg.alias.ranking):
            m.data.command_type = "ranking"
            libs.commands.dispatcher.main(m)
        case x if re.match(rf"^{g.cfg.cw.report}$", x) or (m.is_command and x in g.cfg.alias.report):
            m.data.command_type = "report"
            libs.commands.dispatcher.main(m)

        # データベース関連コマンド
        case x if m.is_command and x in g.cfg.alias.download:
            m.post.file_list = [{"成績記録DB": g.cfg.setting.database_file}]

        # メンバーリスト/チームリスト
        case x if re.match(rf"^{g.cfg.cw.member}$", x) or (m.is_command and x in g.cfg.alias.member):
            m.post.message = lookup.textdata.get_members_list()
            m.post.codeblock = True
            m.post.key_header = True
            m.post.ts = m.data.event_ts
        case x if re.match(rf"^{g.cfg.cw.team}$", x) or (m.is_command and x in g.cfg.alias.team_list):
            m.post.message = lookup.textdata.get_team_list()
            m.post.codeblock = True
            m.post.key_header = True
            m.post.ts = m.data.event_ts

        # メンバー管理系コマンド
        case x if m.is_command and x in g.cfg.alias.add:
            m.post.message = member.append(m.argument)
            m.post.key_header = False
        case x if m.is_command and x in g.cfg.alias.delete:
            m.post.message = member.remove(m.argument)
            m.post.key_header = False

        # チーム管理系コマンド
        case x if m.is_command and x in g.cfg.alias.team_create:
            m.post.message = team.create(m.argument)
            m.post.key_header = False
        case x if m.is_command and x in g.cfg.alias.team_del:
            m.post.message = team.delete(m.argument)
            m.post.key_header = False
        case x if m.is_command and x in g.cfg.alias.team_add:
            m.post.message = team.append(m.argument)
            m.post.key_header = False
        case x if m.is_command and x in g.cfg.alias.team_remove:
            m.post.message = team.remove(m.argument)
            m.post.key_header = False
        case x if m.is_command and x in g.cfg.alias.team_clear:
            m.post.message = team.clear()
            m.post.key_header = False

        # その他
        case _ as x:
            if m.is_command:  # スラッシュコマンド
                if x in g.app_config.slash_commands:
                    g.app_config.slash_commands[x](m)
                else:
                    m.post.message = g.app_config.slash_commands["help"](g.app_config.slash_command)
            else:  # 個別コマンド
                if x in g.app_config.special_commands:
                    g.app_config.special_commands[x](m)
                if x == "Reminder:" and m.data.text in g.app_config.special_commands:
                    g.app_config.special_commands[m.data.text](m)

            other_words(x, m)  # コマンドに一致しない場合

    adapter.api.post(m)


def other_words(word: str, m: MessageParserProtocol):
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


def message_append(detection: GameResult, m: MessageParserProtocol):
    """メッセージの追加処理

    Args:
        detection (GameResult): スコアデータ
        m (MessageParserProtocol): メッセージデータ
    """

    adapter = factory.select_adapter(g.selected_service)

    if _thread_check(m):
        modify.db_insert(detection, m)
        adapter.functions.score_verification(detection, m)
    else:
        m.post.thread = True
        message.random_reply(m, "inside_thread")
        logging.notice("skip (inside thread). event_ts=%s, thread_ts=%s", m.data.event_ts, m.data.thread_ts)  # type: ignore


def message_changed(detection: GameResult, m: MessageParserProtocol):
    """メッセージの変更処理

    Args:
        detection (GameResult): スコアデータ
        m (MessageParserProtocol): メッセージデータ
    """

    adapter = factory.select_adapter(g.selected_service)
    record_data = lookup.db.exsist_record(m.data.event_ts)

    if detection.to_dict() == record_data.to_dict():  # スコア比較
        return  # 変更箇所がなければ何もしない
    if _thread_check(m):
        if record_data.has_valid_data():
            if record_data.rule_version == g.cfg.mahjong.rule_version:
                modify.db_update(detection, m)
                adapter.functions.score_verification(detection, m)
            else:
                logging.notice("skip (rule_version not match). event_ts=%s", m.data.event_ts)  # type: ignore
        else:
            modify.db_insert(detection, m)
            adapter.functions.score_verification(detection, m)
            modify.reprocessing_remarks(m)
    else:
        m.post.thread = True
        message.random_reply(m, "inside_thread")
        logging.notice("skip (inside thread). event_ts=%s, thread_ts=%s", m.data.event_ts, m.data.thread_ts)  # type: ignore


def message_deleted(m: MessageParserProtocol):
    """メッセージの削除処理

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    api_adapter = factory.select_adapter(g.selected_service)

    if re.match(rf"^{g.cfg.setting.remarks_word}", m.keyword):  # 追加メモ
        delete_list = modify.remarks_delete(m)
    else:
        delete_list = modify.db_delete(m)

    for ts in delete_list:
        if isinstance(g.app_config, factory.slack.config.AppConfig):
            api_adapter.reactions.remove(icon=g.app_config.reaction_ok, ch=m.data.channel_id, ts=ts)
            api_adapter.reactions.remove(icon=g.app_config.reaction_ng, ch=m.data.channel_id, ts=ts)


def _thread_check(m: MessageParserProtocol) -> bool:
    """スレッド内判定関数"""

    if isinstance(g.app_config, factory.slack.config.AppConfig):
        if not m.in_thread or (m.in_thread == g.app_config.thread_report):
            return True
        return False
    return not m.in_thread
