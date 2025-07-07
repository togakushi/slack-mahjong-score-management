"""
libs/commands/report/slackpost.py
"""

import libs.global_value as g
from integrations.slack.functions import conversation
from libs.commands import report
from libs.functions import message
from libs.utils import dictutil, formatter


def main():
    """レポートをslackにpostする"""
    g.params = dictutil.placeholder(g.cfg.report)

    if len(g.params["player_list"]) == 1:  # 成績レポート
        name, pdf_file = report.results_report.gen_pdf()
        if pdf_file:
            conversation.post_fileupload(f"成績レポート({name})", pdf_file)
        else:
            conversation.post_message(message.random_reply(message="invalid_argument"))
    elif g.params.get("order"):
        report_file_path = report.winner.plot()
        if report_file_path:
            conversation.post_fileupload("成績上位者", report_file_path)
        else:
            conversation.post_message(message.random_reply(message="no_hits"))
    elif g.params.get("statistics"):
        report_file_path = report.monthly.plot()
        if report_file_path:
            conversation.post_fileupload("月別ゲーム統計", report_file_path)
        else:
            conversation.post_message(message.random_reply(message="no_hits"))
    elif g.params.get("versus_matrix") or len(g.params["player_list"]) >= 2:  # 対局対戦マトリックス
        msg, file_list = report.matrix.plot()
        if g.args.testcase:
            formatter.debug_out(msg)
        else:
            conversation.slack_post(
                headline=msg,
                message=message.random_reply(message="no_hits"),
                file_list=file_list,
            )
    else:
        report_file_path = report.results_list.main()
        if report_file_path:
            conversation.post_fileupload("成績一覧", report_file_path)
        else:
            conversation.post_message(message.random_reply(message="no_hits"))
