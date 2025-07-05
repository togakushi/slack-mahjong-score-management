"""
libs/functions/events/slash_command.py
"""

import logging

import libs.commands.graph.slackpost
import libs.commands.ranking.slackpost
import libs.commands.report.slackpost
import libs.commands.results.slackpost
import libs.global_value as g
from libs.api import slack
from libs.data import comparison, lookup
from libs.functions import compose
from libs.registry import member, team


def main(ack, body, client):
    """スラッシュコマンド

    Args:
        ack (_type_): ack
        body (dict): ポストされたデータ
        client (slack_bolt.App.client): slack_boltオブジェクト
    """

    ack()
    logging.trace(body)  # type: ignore
    g.msg.parser(body)
    g.msg.client = client

    if g.msg.text:
        match g.msg.keyword:
            # 成績管理系コマンド
            case x if x in g.cfg.alias.results:
                libs.commands.results.slackpost.main()
            case x if x in g.cfg.alias.graph:
                libs.commands.graph.slackpost.main()
            case x if x in g.cfg.alias.ranking:
                libs.commands.ranking.slackpost.main()
            case x if x in g.cfg.alias.report:
                libs.commands.report.slackpost.main()

            # データベース関連コマンド
            case x if x in g.cfg.alias.check:
                comparison.main()
            case x if x in g.cfg.alias.download:
                slack.post.post_fileupload("resultdb", g.cfg.db.database_file)

            # メンバー管理系コマンド
            case x if x in g.cfg.alias.member:
                title, msg = lookup.textdata.get_members_list()
                slack.post.post_text(g.msg.event_ts, title, msg)
            case x if x in g.cfg.alias.add:
                slack.post.post_message(member.append(g.msg.argument))
            case x if x in g.cfg.alias.delete:
                slack.post.post_message(member.remove(g.msg.argument))

            # チーム管理系コマンド
            case x if x in g.cfg.alias.team_create:
                slack.post.post_message(team.create(g.msg.argument))
            case x if x in g.cfg.alias.team_del:
                slack.post.post_message(team.delete(g.msg.argument))
            case x if x in g.cfg.alias.team_add:
                slack.post.post_message(team.append(g.msg.argument))
            case x if x in g.cfg.alias.team_remove:
                slack.post.post_message(team.remove(g.msg.argument))
            case x if x in g.cfg.alias.team_list:
                slack.post.post_message(lookup.textdata.get_team_list())
            case x if x in g.cfg.alias.team_clear:
                slack.post.post_message(team.clear())

            # その他
            case _:
                slack.post.post_message(compose.msg_help.slash_command(body["command"]))
