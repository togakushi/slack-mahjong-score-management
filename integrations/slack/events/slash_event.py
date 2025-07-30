"""
integrations/slack/events/slash_event.py
"""

import logging

import libs.commands.graph.slackpost
import libs.commands.ranking.slackpost
import libs.commands.report.slackpost
import libs.commands.results.slackpost
import libs.global_value as g
from integrations import factory
from integrations.slack import comparison
from libs.data import lookup
from libs.functions import compose
from libs.registry import member, team


def main(ack, body):
    """スラッシュコマンド

    Args:
        ack (_type_): ack
        body (dict): ポストされたデータ
    """

    ack()
    logging.trace(body)  # type: ignore

    api_adapter = factory.select_adapter(g.selected_service)
    m = factory.select_parser(g.selected_service, **g.cfg.setting.to_dict())
    m.parser(body)

    if m.data.text:
        match m.keyword:
            # 成績管理系コマンド
            case x if x in g.cfg.alias.results:
                libs.commands.results.slackpost.main(m)
            case x if x in g.cfg.alias.graph:
                libs.commands.graph.slackpost.main(m)
            case x if x in g.cfg.alias.ranking:
                libs.commands.ranking.slackpost.main(m)
            case x if x in g.cfg.alias.report:
                libs.commands.report.slackpost.main(m)

            # データベース関連コマンド
            case x if x in g.cfg.alias.check:
                comparison.main(m)
            case x if x in g.cfg.alias.download:
                m.post.file_list = [{m.post.title: g.cfg.db.database_file}]
                api_adapter.fileupload(m)

            # メンバー管理系コマンド
            case x if x in g.cfg.alias.member:
                m.post.title, m.post.message = lookup.textdata.get_members_list()
                api_adapter.post_text(m)
            case x if x in g.cfg.alias.add:
                m.post.message = member.append(m.argument)
                api_adapter.post_message(m)
            case x if x in g.cfg.alias.delete:
                m.post.message = member.remove(m.argument)
                api_adapter.post_message(m)

            # チーム管理系コマンド
            case x if x in g.cfg.alias.team_create:
                m.post.message = team.create(m.argument)
                api_adapter.post_message(m)
            case x if x in g.cfg.alias.team_del:
                m.post.message = team.delete(m.argument)
                api_adapter.post_message(m)
            case x if x in g.cfg.alias.team_add:
                m.post.message = team.append(m.argument)
                api_adapter.post_message(m)
            case x if x in g.cfg.alias.team_remove:
                m.post.message = team.remove(m.argument)
                api_adapter.post_message(m)
            case x if x in g.cfg.alias.team_list:
                m.post.message = lookup.textdata.get_team_list()
                api_adapter.post_message(m)
            case x if x in g.cfg.alias.team_clear:
                m.post.message = team.clear()
                api_adapter.post_message(m)

            # その他
            case _:
                m.post.message = compose.msg_help.slash_command(g.cfg.setting.slash_command)
                api_adapter.post_message(m)
