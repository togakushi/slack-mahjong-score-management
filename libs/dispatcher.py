"""
libs/event_dispatcher.py
"""

import logging
import re
from typing import cast

import libs.commands.graph.entry
import libs.commands.ranking.entry
import libs.commands.report.entry
import libs.commands.results.entry
import libs.global_value as g
from cls.config import SubCommand
from cls.score import GameResult
from integrations import factory
from integrations.protocols import MessageParserProtocol
from libs.data import lookup, modify
from libs.functions import compose, message
from libs.registry import member, team
from libs.utils import formatter


def register():
    """コマンドディスパッチテーブル登録"""

    def dispatch_help(m: MessageParserProtocol):
        # ヘルプメッセージ
        m.post.message = compose.msg_help.event_message()
        m.post.ts = m.data.event_ts
        m.post.key_header = False
        # メンバーリスト
        m.post.message = lookup.textdata.get_members_list()
        m.post.codeblock = True
        m.post.key_header = True

    def dispatch_download(m: MessageParserProtocol):
        m.post.file_list = [{"成績記録DB": g.cfg.setting.database_file}]

    def dispatch_members_list(m: MessageParserProtocol):
        m.post.message = lookup.textdata.get_members_list()
        m.post.codeblock = True
        m.post.key_header = True
        m.post.ts = m.data.event_ts

    def dispatch_team_list(m: MessageParserProtocol):
        m.post.message = lookup.textdata.get_team_list()
        m.post.codeblock = True
        m.post.key_header = True
        m.post.ts = m.data.event_ts

    def dispatch_member_append(m: MessageParserProtocol):
        m.post.message = member.append(m.argument)
        m.post.key_header = False

    def dispatch_member_remove(m: MessageParserProtocol):
        m.post.message = member.remove(m.argument)
        m.post.key_header = False

    def dispatch_team_create(m: MessageParserProtocol):
        m.post.message = team.create(m.argument)
        m.post.key_header = False

    def dispatch_team_delete(m: MessageParserProtocol):
        m.post.message = team.delete(m.argument)
        m.post.key_header = False

    def dispatch_team_append(m: MessageParserProtocol):
        m.post.message = team.append(m.argument)
        m.post.key_header = False

    def dispatch_team_remove(m: MessageParserProtocol):
        m.post.message = team.remove(m.argument)
        m.post.key_header = False

    def dispatch_team_clear(m: MessageParserProtocol):
        m.post.message = team.clear()
        m.post.key_header = False

    dispatch_table: dict = {
        "results": libs.commands.results.entry.main,
        "graph": libs.commands.graph.entry.main,
        "ranking": libs.commands.ranking.entry.main,
        "report": libs.commands.report.entry.main,
        "member": dispatch_members_list,
        "team_list": dispatch_team_list,
        "download": dispatch_download,
        "add": dispatch_member_append,
        "delete": dispatch_member_remove,
        "team_create": dispatch_team_create,
        "team_del": dispatch_team_delete,
        "team_add": dispatch_team_append,
        "team_remove": dispatch_team_remove,
        "team_clear": dispatch_team_clear,
    }

    # ヘルプ
    g.keyword_dispatcher.update({g.cfg.setting.help: dispatch_help})

    for command, ep in dispatch_table.items():
        # 呼び出しキーワード登録
        if hasattr(g.cfg, command):
            sub_command = cast(SubCommand, getattr(g.cfg, command))
            for alias in sub_command.commandword:
                g.keyword_dispatcher.update({alias: ep})
        # スラッシュコマンド登録
        for alias in cast(list, getattr(g.cfg.alias, command)):
            g.command_dispatcher.update({alias: ep})


def by_keyword(m: MessageParserProtocol):
    """メイン処理"""

    logging.info(
        "status=%s, event_ts=%s, thread_ts=%s, in_thread=%s, keyword=%s, user_id=%s,",
        m.data.status, m.data.event_ts, m.data.thread_ts, m.in_thread, m.keyword, m.data.user_id,
    )

    # 許可されていないユーザのコマンドは処理しない
    if m.ignore_user:
        logging.info("event skip[ignore user]: %s", m.data.user_id)
        return

    # 投稿済みメッセージが削除された場合
    if m.data.status == "message_deleted":
        message_deleted(m)
        return

    match m.keyword:
        # 呼び出しキーワード
        case x if x in g.keyword_dispatcher and not m.is_command:
            g.keyword_dispatcher[x](m)
        # スラッシュコマンド
        case x if x in g.command_dispatcher and m.is_command:
            g.command_dispatcher[x](m)
        # リマインダ
        case "Reminder:":
            if m.data.text in g.keyword_dispatcher and m.is_bot:
                g.keyword_dispatcher[m.data.text](m)
        # その他
        case _ as x:
            other_words(x, m)  # コマンドに一致しない場合

    g.adapter.api.post(m)


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

    if _thread_check(m):
        modify.db_insert(detection, m)
    else:
        m.post.thread = True
        message.random_reply(m, "inside_thread")
        logging.notice("skip (inside thread). event_ts=%s, thread_ts=%s", m.data.event_ts, m.data.thread_ts)  # type: ignore

    g.adapter.functions.post_processing(m)


def message_changed(detection: GameResult, m: MessageParserProtocol):
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
                logging.notice("skip (rule_version not match). event_ts=%s", m.data.event_ts)  # type: ignore
        else:
            modify.db_insert(detection, m)
            modify.reprocessing_remarks(m)
    else:
        m.post.thread = True
        message.random_reply(m, "inside_thread")
        logging.notice("skip (inside thread). event_ts=%s, thread_ts=%s", m.data.event_ts, m.data.thread_ts)  # type: ignore

    g.adapter.functions.post_processing(m)


def message_deleted(m: MessageParserProtocol):
    """メッセージの削除処理

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    if re.match(rf"^{g.cfg.setting.remarks_word}", m.keyword):  # 追加メモ
        modify.remarks_delete(m)
    else:
        modify.db_delete(m)

    g.adapter.functions.post_processing(m)


def _thread_check(m: MessageParserProtocol) -> bool:
    """スレッド内判定関数"""

    if isinstance(g.adapter.conf, factory.slack.config.AppConfig):
        if not m.in_thread or (m.in_thread == g.adapter.conf.thread_report):
            return True
        return False
    return not m.in_thread
