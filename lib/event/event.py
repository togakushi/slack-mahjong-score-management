import re

import lib.command as c
import lib.database as d
import lib.function as f
from lib.function import global_value as g


# イベントAPI
@g.app.event("message")
def handle_message_events(client, body):
    """
    ポストされた内容で処理を分岐
    """

    g.logging.trace(body)  # type: ignore
    g.msg.parser(body)
    g.msg.client = client

    # 許可されていないユーザのポストは処理しない
    if g.msg.user_id in g.ignore_userid:
        g.logging.trace(f"event skip[ignore user]: {g.msg.user_id}")  # type: ignore
        return

    g.logging.info(f"{vars(g.msg)}")

    match g.msg.keyword:
        # ヘルプ
        case x if re.match(rf"^{g.commandword['help']}$", x):
            # ヘルプメッセージ
            f.slack_api.post_message(f.message.help_message(), g.msg.event_ts)
            # メンバーリスト
            title, msg = c.member.Getmemberslist()
            f.slack_api.post_text(g.msg.event_ts, title, msg)

        # 成績管理系コマンド
        case x if re.match(rf"^{g.commandword['results']}", x):
            c.results.slackpost.main()
        case x if re.match(rf"^{g.commandword['graph']}", x):
            c.graph.slackpost.main()
        case x if re.match(rf"^{g.commandword['ranking']}", x):
            c.ranking.slackpost.main()
        case x if re.match(rf"^{g.commandword['report']}", x):
            c.report.slackpost.main()

        # データベース関連コマンド
        case x if re.match(rf"^{g.commandword['check']}", x):
            d.comparison.main(
                client, g.msg.channel_id, g.msg.event_ts
            )
        case x if re.match(rf"^Reminder: {g.commandword['check']}$", x):  # Reminderによる突合
            g.logging.info(f'Reminder: {g.commandword["check"]}')
            d.comparison.main(
                client, g.msg.channel_id, g.msg.event_ts
            )

        # その他
        case x if re.match(rf"^{g.commandword['member']}", x):
            title, msg = c.member.Getmemberslist()
            f.slack_api.post_text(g.msg.event_ts, title, msg)
        case x if re.match(rf"^{g.commandword['team']}", x):
            title = "チーム一覧"
            msg = c.team.list()
            f.slack_api.post_text(g.msg.event_ts, title, msg)

        # 追加メモ
        case x if re.match(rf"^{g.commandword['remarks_word']}", x) and g.msg.thread_ts:
            if d.common.ExsistRecord(g.msg.thread_ts) and g.msg.updatable:
                f.score.check_remarks()

        # 結果報告フォーマットに一致したポストの処理
        case _:
            detection = f.search.pattern(g.msg.text)
            match g.msg.status:
                case "message_append":
                    if detection:
                        f.score.check_score(detection)
                        if g.msg.updatable:
                            d.common.resultdb_insert(detection, g.msg.event_ts)
                        else:
                            f.slack_api.post_message(f.message.restricted_channel(), g.msg.event_ts)
                case "message_changed":
                    if detection:
                        f.score.check_score(detection)
                        if g.msg.updatable:
                            if d.common.ExsistRecord(g.msg.event_ts):
                                d.common.resultdb_update(detection, g.msg.event_ts)
                            else:
                                d.common.resultdb_insert(detection, g.msg.event_ts)
                        else:
                            f.slack_api.post_message(f.message.restricted_channel(), g.msg.event_ts)
                    else:
                        f.slack_api.call_reactions_remove()
                        if d.common.ExsistRecord(g.msg.event_ts):
                            d.common.resultdb_delete(g.msg.event_ts)
                case "message_deleted":
                    if d.common.ExsistRecord(g.msg.event_ts):
                        d.common.resultdb_delete(g.msg.event_ts)


@g.app.event("reaction_added")
def handle_reaction_added_events(body):
    g.logging.notice(body)   # type: ignore
