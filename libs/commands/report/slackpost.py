"""
libs/commands/report/slackpost.py
"""

import libs.global_value as g
from integrations import factory
from libs.commands import report
from libs.functions import message
from libs.utils import dictutil


def main():
    """レポートをslackにpostする"""
    api_adapter = factory.get_api_adapter(g.selected_service)

    g.params = dictutil.placeholder(g.cfg.report)

    if len(g.params["player_list"]) == 1:  # 成績レポート
        name, pdf_file = report.results_report.gen_pdf()
        if pdf_file:
            api_adapter.fileupload(f"成績レポート({name})", pdf_file)
        else:
            api_adapter.post_message(message.random_reply(message="invalid_argument"))
    elif g.params.get("order"):
        report_file_path = report.winner.plot()
        if report_file_path:
            api_adapter.fileupload("成績上位者", report_file_path)
        else:
            api_adapter.post_message(message.random_reply(message="no_hits"))
    elif g.params.get("statistics"):
        report_file_path = report.monthly.plot()
        if report_file_path:
            api_adapter.fileupload("月別ゲーム統計", report_file_path)
        else:
            api_adapter.post_message(message.random_reply(message="no_hits"))
    elif g.params.get("versus_matrix") or len(g.params["player_list"]) >= 2:  # 対局対戦マトリックス
        msg, file_list = report.matrix.plot()
        api_adapter.post(
            headline=msg,
            message=message.random_reply(message="no_hits"),
            file_list=file_list,
        )
    else:
        report_file_path = report.results_list.main()
        if report_file_path:
            api_adapter.fileupload("成績一覧", report_file_path)
        else:
            api_adapter.post_message(message.random_reply(message="no_hits"))
