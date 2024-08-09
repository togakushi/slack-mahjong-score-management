import lib.function as f
from lib.function import global_value as g

from lib.command.report import monthly
from lib.command.report import personal
from lib.command.report import winner
from lib.command.report import results


def main(client, channel, argument):
    """
    レポートをslackにpostする

    Parameters
    ----------
    client : obj

    channel : str
        post先のチャンネルID or ユーザーID

    argument : list
        slackから受け取った引数
        解析対象のプレイヤー、検索範囲などが指定される
    """

    g.opt.initialization("report", argument)
    g.prm.update(g.opt)

    if len(g.prm.player_list) == 1: # 個人成績レポート
        name, pdf_file = results.gen_pdf()
        if pdf_file:
            f.slack_api.post_fileupload(client, channel, f"成績レポート({name})", pdf_file)
        else:
            f.slack_api.post_message(client, channel, f.message.invalid_argument())
    elif g.opt.statistics:
        report_file_path = monthly.plot()
        if report_file_path:
            f.slack_api.post_fileupload(client, channel, "月別ゲーム統計", report_file_path)
        else:
            f.slack_api.post_message(client, channel, f.message.no_hits())
    elif g.opt.personal:
        report_file_path = personal.plot()
        if report_file_path:
            f.slack_api.post_fileupload(client, channel, "個人成績一覧", report_file_path)
        else:
            f.slack_api.post_message(client, channel, f.message.no_hits())
    else:
        report_file_path = winner.plot()
        if report_file_path:
            f.slack_api.post_fileupload(client, channel, "成績上位者", report_file_path)
        else:
            f.slack_api.post_message(client, channel, f.message.no_hits())
