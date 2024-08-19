#!/usr/bin/env python3
import os

from slack_bolt.adapter.socket_mode import SocketModeHandler

import lib.command as c
import lib.database as d
import lib.event as e
import lib.function as f
from lib.function import global_value as g


class CommandCheck(str):
    """
    キーワードがサブコマンドかチェックする(match専用)
    """

    def __init__(self, command_name: str):
        self.command_name = command_name

    def __eq__(self, chk_pattern):
        commandlist = g.config["alias"].get(chk_pattern, "")
        commandlist = [chk_pattern] + [x for x in commandlist.split(",") if x]

        if self.command_name in commandlist:
            return (True)

        return (False)


# イベントAPI
@g.app.event("app_home_opened")
def handle_home_events(client, event):
    g.app_var["user_id"] = event["user"]
    if "view" in event:
        g.app_var["view_id"] = event["view"]["id"]

    g.logging.trace(f"{g.app_var}")  # type: ignore

    result = client.views_publish(
        user_id=g.app_var["user_id"],
        view=e.build_main_menu(),
    )

    g.logging.trace(result)  # type: ignore


@g.app.command(g.slash_command)
def slash_command(ack, body, client):
    ack()
    g.logging.trace(f"{body}")  # type: ignore
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
                c.ranking.slackpost.main()
            case "report":
                c.report.slackpost.main()

            # データベース関連コマンド
            case "check":
                d.comparison.main(client, g.msg.channel_id, g.msg.event_ts)
            case "download":
                f.slack_api.post_fileupload("resultdb", g.database_file)

            # メンバー管理系コマンド
            case "member":
                title, msg = c.member.Getmemberslist()
                f.slack_api.post_text(g.msg.event_ts, title, msg)
            case "add":
                f.slack_api.post_message(c.member.MemberAppend(g.msg.argument))
            case "del":
                f.slack_api.post_message(c.member.MemberRemove(g.msg.argument))

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


if __name__ == "__main__":
    d.initialization.initialization_resultdb()
    c.member.read_memberslist()

    handler = SocketModeHandler(g.app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
