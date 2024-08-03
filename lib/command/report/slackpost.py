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

    command_option = f.configure.command_option_initialization("report")
    _, target_player, _, command_option = f.common.argument_analysis(argument, command_option)
    params, _ = f.common.game_info(argument, command_option)

    g.logging.info(f"{argument=}")
    g.logging.info(f"{command_option=}")

    if len(target_player) == 1: # 個人成績レポート
        name, pdf_file = results.gen_pdf(argument, command_option)
        if pdf_file:
            f.slack_api.post_fileupload(client, channel, f"成績レポート({name})", pdf_file)
        else:
            f.slack_api.post_message(client, channel, f.message.invalid_argument())
    elif command_option["statistics"]:
        report_file_path = monthly.plot(argument, command_option)
        if report_file_path:
            f.slack_api.post_fileupload(client, channel, "月別ゲーム統計", report_file_path)
        else:
            f.slack_api.post_message(client, channel, f.message.no_hits(params))
    elif command_option["personal"]:
        report_file_path = personal.plot(argument, command_option)
        if report_file_path:
            f.slack_api.post_fileupload(client, channel, "個人成績一覧", report_file_path)
        else:
            f.slack_api.post_message(client, channel, f.message.no_hits(params))
    else:
        report_file_path = winner.plot(argument, command_option)
        if report_file_path:
            f.slack_api.post_fileupload(client, channel, "成績上位者", report_file_path)
        else:
            f.slack_api.post_message(client, channel, f.message.no_hits(params))
