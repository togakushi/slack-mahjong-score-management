import global_value as g
import lib.function as f
from lib.command.report import matrix, monthly, personal, results, winner


def main():
    """
    レポートをslackにpostする
    """

    g.opt.initialization("report", g.msg.argument)
    g.prm.update(g.opt)

    if len(g.prm.player_list) == 1:  # 個人成績レポート
        name, pdf_file = results.gen_pdf()
        if pdf_file:
            f.slack_api.post_fileupload(f"成績レポート({name})", pdf_file)
        else:
            f.slack_api.post_message(f.message.invalid_argument())
    elif g.opt.statistics:
        report_file_path = monthly.plot()
        if report_file_path:
            f.slack_api.post_fileupload("月別ゲーム統計", report_file_path)
        else:
            f.slack_api.post_message(f.message.no_hits())
    elif g.opt.personal:
        report_file_path = personal.plot()
        if report_file_path:
            f.slack_api.post_fileupload("個人成績一覧", report_file_path)
        else:
            f.slack_api.post_message(f.message.no_hits())
    elif g.opt.versus_matrix or len(g.prm.player_list) >= 2:  # 対局対戦マトリックス
        msg, file_list = matrix.plot()
        if g.args.testcase:
            f.common.debug_out(msg)
        else:
            f.slack_api.slack_post(
                headline=msg,
                message=f.message.no_hits(),
                file_list=file_list,
            )
    else:
        report_file_path = winner.plot()
        if report_file_path:
            f.slack_api.post_fileupload("成績上位者", report_file_path)
        else:
            f.slack_api.post_message(f.message.no_hits())
