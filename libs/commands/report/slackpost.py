"""
libs/commands/report/slackpost.py
"""

import libs.global_value as g
from integrations import factory
from integrations.base import MessageParserInterface
from libs.commands import report
from libs.functions import message
from libs.utils import dictutil


def main(m: MessageParserInterface):
    """レポートをslackにpostする"""
    api_adapter = factory.select_adapter(g.selected_service)
    g.params = dictutil.placeholder(g.cfg.report, m)
    m.post.message_type = "no_hits"
    m.post.thread = False

    if len(g.params["player_list"]) == 1:  # 成績レポート
        name, pdf_file = report.results_report.gen_pdf()
        if pdf_file:
            m.post.file_list = [{f"成績レポート({name})": str(pdf_file)}]
            api_adapter.fileupload(m)
        else:
            m.post.message_type = "invalid_argument"
            m.post.message = message.random_reply(m)
            api_adapter.post_message(m)
    elif g.params.get("order"):
        if (file_path := report.winner.plot()):
            m.post.file_list = [{"成績上位者": file_path}]
            api_adapter.fileupload(m)
        else:
            m.post.message = message.random_reply(m)
            api_adapter.post_message(m)
    elif g.params.get("statistics"):
        if (file_path := report.monthly.plot()):
            m.post.file_list = [{"月別ゲーム統計": file_path}]
            api_adapter.fileupload(m)
        else:
            m.post.message = message.random_reply(m)
            api_adapter.post_message(m)
    elif g.params.get("versus_matrix") or len(g.params["player_list"]) >= 2:  # 対局対戦マトリックス
        m.post.headline, m.post.file_list = report.matrix.plot(m)
        m.post.message = message.random_reply(m)
        api_adapter.post(m)
    else:
        if (file_path := report.results_list.main()):
            m.post.file_list = [{"成績一覧": file_path}]
            api_adapter.fileupload(m)
        else:
            m.post.message = message.random_reply(m)
            api_adapter.post_message(m)
