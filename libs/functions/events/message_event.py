"""
libs/functions/events/message_event.py
"""

import logging
import re

import libs.commands.graph.slackpost
import libs.commands.report.slackpost
import libs.commands.results.slackpost
import libs.global_value as g
from libs.commands import results
from libs.data import comparison, lookup, modify
from libs.functions import message, slack_api
from libs.utils import validator


def main(client, body):
    """ポストされた内容で処理を分岐

    Args:
        client (slack_bolt.App.client): slack_boltオブジェクト
        body (dict): ポストされたデータ
    """

    logging.trace(body)  # type: ignore
    g.msg.parser(body)
    g.msg.client = client
    logging.info(
        "status=%s, event_ts=%s, thread_ts=%s, in_thread=%s, keyword=%s, user_id=%s,",
        g.msg.status, g.msg.event_ts, g.msg.thread_ts, g.msg.in_thread, g.msg.keyword, g.msg.user_id,
    )

    # 許可されていないユーザのポストは処理しない
    if g.msg.user_id in g.cfg.setting.ignore_userid:
        logging.trace("event skip[ignore user]: %s", g.msg.user_id)  # type: ignore
        return

    # 投稿済みメッセージが削除された場合
    if g.msg.status == "message_deleted":
        if re.match(rf"^{g.cfg.cw.remarks_word}", g.msg.keyword):  # 追加メモ
            modify.remarks_delete(g.msg.event_ts)
        else:
            modify.db_delete(g.msg.event_ts)
        return

    # キーワード処理
    print(">>>", g.msg.keyword, g.cfg.cw.results)
    match g.msg.keyword:
        # ヘルプ
        case x if re.match(rf"^{g.cfg.cw.help}$", x):
            # ヘルプメッセージ
            slack_api.post_message(message.help_message(), g.msg.event_ts)
            # メンバーリスト
            title, msg = lookup.textdata.get_members_list()
            slack_api.post_text(g.msg.event_ts, title, msg)

        # 成績管理系コマンド
        case x if re.match(rf"^{g.cfg.cw.results}$", x):
            libs.commands.results.slackpost.main()
        case x if re.match(rf"^{g.cfg.cw.graph}$", x):
            libs.commands.graph.slackpost.main()
        case x if re.match(rf"^{g.cfg.cw.ranking}$", x):
            results.ranking.main()
        case x if re.match(rf"^{g.cfg.cw.report}$", x):
            libs.commands.report.slackpost.main()

        # データベース関連コマンド
        case x if re.match(rf"^{g.cfg.cw.check}$", x):
            comparison.main()
        case x if re.match(rf"^Reminder: {g.cfg.cw.check}$", str(g.msg.text)):  # Reminderによる突合
            logging.notice("Reminder: %s", g.cfg.cw.check)  # type: ignore
            comparison.main()

        # メンバーリスト/チームリスト
        case x if re.match(rf"^{g.cfg.cw.member}$", x):
            title, msg = lookup.textdata.get_members_list()
            slack_api.post_text(g.msg.event_ts, title, msg)
        case x if re.match(rf"^{g.cfg.cw.team}$", x):
            title = "チーム一覧"
            msg = lookup.textdata.get_team_list()
            slack_api.post_text(g.msg.event_ts, title, msg)

        case _ as x:
            record_data = lookup.db.exsist_record(g.msg.event_ts)
            if re.match(rf"^{g.cfg.cw.remarks_word}$", x) and g.msg.in_thread:  # 追加メモ
                if lookup.db.exsist_record(g.msg.thread_ts):
                    modify.check_remarks()
            else:
                detection = validator.pattern(str(g.msg.text))
                if detection:  # 結果報告フォーマットに一致したポストの処理
                    match g.msg.status:
                        case "message_append":
                            if g.cfg.setting.thread_report == g.msg.in_thread:
                                assert isinstance(detection, list), "detection should be a list"
                                modify.db_insert(detection, g.msg.event_ts)
                            else:
                                slack_api.post_message(message.reply(message="inside_thread"), g.msg.event_ts)
                                logging.notice("skip update(inside thread). event_ts=%s, thread_ts=%s", g.msg.event_ts, g.msg.thread_ts)  # type: ignore
                                logging.warning("DEBUG(inside_thread): body=%s msg=%s cfg=%s", body, vars(g.msg), vars(g.cfg))  # ToDo: 解析用
                        case "message_changed":
                            if detection == [record_data.get(x) for x in [f"p{x}_{y}" for x in range(1, 5) for y in ("name", "str")] + ["comment"]]:
                                return  # 変更箇所がなければ何もしない
                            if g.cfg.setting.thread_report == g.msg.in_thread:
                                if record_data:
                                    if record_data.get("rule_version") == g.cfg.mahjong.rule_version:
                                        assert isinstance(detection, list), "detection should be a list"
                                        modify.db_update(detection, g.msg.event_ts)
                                    else:
                                        logging.notice("skip update(rule_version not match). event_ts=%s", g.msg.event_ts)  # type: ignore
                                else:
                                    assert isinstance(detection, list), "detection should be a list"
                                    modify.db_insert(detection, g.msg.event_ts)
                                    modify.reprocessing_remarks()
                            else:
                                slack_api.post_message(message.reply(message="inside_thread"), g.msg.event_ts)
                                logging.notice("skip update(inside thread). event_ts=%s, thread_ts=%s", g.msg.event_ts, g.msg.thread_ts)  # type: ignore
                                logging.warning("DEBUG(inside_thread): body=%s msg=%s cfg=%s", body, vars(g.msg), vars(g.cfg))  # ToDo: 解析用
                else:
                    if record_data:
                        modify.db_delete(g.msg.event_ts)
                        for icon in lookup.api.reactions_status():
                            slack_api.call_reactions_remove(icon)
