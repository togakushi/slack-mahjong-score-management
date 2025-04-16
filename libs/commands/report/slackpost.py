"""
lib/command/report/slackpost.py
"""

import libs.global_value as g
from libs.commands import report
from libs.functions import message, slack_api
from libs.utils import debug, dictutil


def main():
    """レポートをslackにpostする"""
    g.params = dictutil.placeholder(g.cfg.report)

    if len(g.params["player_list"]) == 1:  # 成績レポート
        name, pdf_file = report.results_report.gen_pdf()
        if pdf_file:
            slack_api.post_fileupload(f"成績レポート({name})", pdf_file)
        else:
            slack_api.post_message(message.reply(message="invalid_argument"))
    elif g.params.get("order"):
        report_file_path = report.winner.plot()
        if report_file_path:
            slack_api.post_fileupload("成績上位者", report_file_path)
        else:
            slack_api.post_message(message.reply(message="no_hits"))
    elif g.params.get("statistics"):
        report_file_path = report.monthly.plot()
        if report_file_path:
            slack_api.post_fileupload("月別ゲーム統計", report_file_path)
        else:
            slack_api.post_message(message.reply(message="no_hits"))
    elif g.params.get("versus_matrix") or len(g.params["player_list"]) >= 2:  # 対局対戦マトリックス
        msg, file_list = report.matrix.plot()
        if g.args.testcase:
            debug.debug_out(msg)
        else:
            slack_api.slack_post(
                headline=msg,
                message=message.reply(message="no_hits"),
                file_list=file_list,
            )
    else:
        report_file_path = report.results_list.main()
        if report_file_path:
            slack_api.post_fileupload("成績一覧", report_file_path)
        else:
            slack_api.post_message(message.reply(message="no_hits"))
