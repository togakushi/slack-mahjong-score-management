import logging
import re

import lib.global_value as g
from cls.search import CommandCheck
from lib import command as c
from lib import database as d
from lib import function as f
from lib import home_tab as h


# イベントAPI
@g.app.event("message")
def handle_message_events(client, body):
    """ポストされた内容で処理を分岐

    Args:
        client (slack_bolt.App.client): slack_boltオブジェクト
        body (dict): ポストされたデータ
    """

    logging.trace(body)
    g.prm.initialization()
    g.msg.parser(body)
    g.msg.client = client

    # 許可されていないユーザのポストは処理しない
    if g.msg.user_id in g.cfg.setting.ignore_userid:
        logging.trace(f"event skip[ignore user]: {g.msg.user_id}")
        return

    # 投稿済みメッセージが削除された場合
    if g.msg.status == "message_deleted":
        d.common.db_delete(g.msg.event_ts)
        return

    match g.msg.keyword:
        # ヘルプ
        case x if re.match(rf"^{g.cfg.cw.help}$", x):
            # ヘルプメッセージ
            f.slack_api.post_message(f.message.help_message(), g.msg.event_ts)
            # メンバーリスト
            title, msg = c.member.get_members_list()
            f.slack_api.post_text(g.msg.event_ts, title, msg)

        # 成績管理系コマンド
        case x if re.match(rf"^{g.cfg.cw.results}", x):
            c.results.slackpost.main()
        case x if re.match(rf"^{g.cfg.cw.graph}", x):
            c.graph.slackpost.main()
        case x if re.match(rf"^{g.cfg.cw.ranking}", x):
            c.results.ranking.main()
        case x if re.match(rf"^{g.cfg.cw.report}", x):
            c.report.slackpost.main()

        # データベース関連コマンド
        case x if re.match(rf"^{g.cfg.cw.check}", x):
            d.comparison.main()
        case x if re.match(rf"^Reminder: {g.cfg.cw.check}$", g.msg.text):  # Reminderによる突合
            logging.notice(f'Reminder: {g.cfg.cw.check}')
            d.comparison.main()

        # メンバーリスト/チームリスト
        case x if re.match(rf"^{g.cfg.cw.member}", x):
            title, msg = c.member.get_members_list()
            f.slack_api.post_text(g.msg.event_ts, title, msg)
        case x if re.match(rf"^{g.cfg.cw.team}", x):
            title = "チーム一覧"
            msg = c.team.list()
            f.slack_api.post_text(g.msg.event_ts, title, msg)

        case _:
            if re.match(rf"^{g.cfg.cw.remarks_word}", g.msg.keyword) and g.msg.in_thread:  # 追加メモ
                if d.common.exsist_record(g.msg.thread_ts) and g.msg.updatable:
                    f.score.check_remarks()
            else:  # 結果報告フォーマットに一致したポストの処理
                detection = f.search.pattern(g.msg.text)
                match g.msg.status:
                    case "message_append":
                        if detection:
                            if g.cfg.setting.thread_report == g.msg.in_thread:
                                d.common.db_insert(detection, g.msg.event_ts)
                            else:
                                f.slack_api.post_message(f.message.reply(message="inside_thread"), g.msg.event_ts)
                                logging.warning(f"DEBUG(inside_thread): {body=} {vars(g.msg)=} {vars(g.prm)=} {vars(g.cfg)=}")  # ToDo: 解析用
                    case "message_changed":
                        record_data = d.common.exsist_record(g.msg.event_ts)
                        record_detection = [record_data.get(x) for x in [f"p{x}_{y}" for x in range(1, 5) for y in ("name", "str")] + ["comment"]]
                        if detection == record_detection:
                            return
                        if detection:
                            if g.cfg.setting.thread_report == g.msg.in_thread:
                                if record_data:
                                    if record_data.get("rule_version") == g.prm.rule_version:
                                        d.common.db_update(detection, g.msg.event_ts)
                                    else:
                                        logging.notice(f"skip update(rule_version not match). ts={g.msg.event_ts}")
                                else:
                                    d.common.db_insert(detection, g.msg.event_ts)
                            else:
                                f.slack_api.post_message(f.message.reply(message="inside_thread"), g.msg.event_ts)
                                logging.warning(f"DEBUG(inside_thread): {body=} {vars(g.msg)=} {vars(g.prm)=} {vars(g.cfg)=}")  # ToDo: 解析用
                        else:
                            if record_data:
                                d.common.db_delete(g.msg.event_ts)
                                for icon in f.slack_api.reactions_status():
                                    f.slack_api.call_reactions_remove(icon)


@g.app.command(g.cfg.setting.slash_command)
def slash_command(ack, body, client):
    """スラッシュコマンド

    Args:
        ack (_type_): ack
        body (dict): ポストされたデータ
        client (slack_bolt.App.client): slack_boltオブジェクト
    """

    ack()
    logging.trace(f"{body}")
    g.msg.parser(body)
    g.msg.client = client

    if g.msg.text:
        match CommandCheck(g.msg.keyword):
            # 成績管理系コマンド
            case "results":
                c.results.slackpost.main()
            case "graph":
                c.graph.slackpost.main()
            case "ranking":
                c.results.ranking.main()
            case "report":
                c.report.slackpost.main()

            # データベース関連コマンド
            case "check":
                d.comparison.main()
            case "download":
                f.slack_api.post_fileupload("resultdb", g.cfg.db.database_file)

            # メンバー管理系コマンド
            case "member":
                title, msg = c.member.get_members_list()
                f.slack_api.post_text(g.msg.event_ts, title, msg)
            case "add":
                f.slack_api.post_message(c.member.member_append(g.msg.argument))
            case "del":
                f.slack_api.post_message(c.member.member_remove(g.msg.argument))

            # チーム管理系コマンド
            case "team_create":
                f.slack_api.post_message(c.team.create(g.msg.argument))
            case "team_del":
                f.slack_api.post_message(c.team.delete(g.msg.argument))
            case "team_add":
                f.slack_api.post_message(c.team.append(g.msg.argument))
            case "team_remove":
                f.slack_api.post_message(c.team.remove(g.msg.argument))
            case "team_list":
                f.slack_api.post_message(c.team.list())
            case "team_clear":
                f.slack_api.post_message(c.team.clear())

            # その他
            case _:
                f.slack_api.post_message(f.message.help(body["command"]))


@g.app.event("app_home_opened")
def handle_home_events(client, event):
    """ホームタブオープン

    Args:
        client (slack_bolt.App.client): slack_boltオブジェクト
        event (dict): イベント内容
    """

    g.app_var["user_id"] = event["user"]
    if "view" in event:
        g.app_var["view_id"] = event["view"]["id"]

    logging.trace(f"{g.app_var}")

    result = client.views_publish(
        user_id=g.app_var["user_id"],
        view=h.home.build_main_menu(),
    )

    logging.trace(result)
