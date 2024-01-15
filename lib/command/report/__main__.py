import lib.function as f
from lib.function import global_value as g

from lib.command.report import monthly
from lib.command.report import personal
from lib.command.report import winner


def help_message():
    report_option = f.configure.command_option_initialization("report")

    msg = [
        "*成績レポートヘルプ*",
        f"\t呼び出しキーワード： {g.commandword['report']}",
        f"\t検索範囲デフォルト： {report_option['aggregation_range'][0]}",
        "\tモード切替",
        "\t\t月間成績上位者： オプションなし",
        "\t\tゲーム傾向統計： 追加オプション「統計」",
        "\t\t個人成績一覧： 追加オプション「個人」または「個人成績」",
    ]
    return("\n".join(msg))


def slackpost(client, channel, argument):
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
    _, _, _, command_option = f.common.argument_analysis(argument, command_option)

    g.logging.info(f"arg: {argument}")
    g.logging.info(f"opt: {command_option}")

    # ヘルプ表示
    if command_option["help"]:
        return(help_message())

    if command_option["statistics"]:
        report_file_path = monthly.plot(argument, command_option)
        if report_file_path:
            f.slack_api.post_fileupload(client, channel, "月別ゲーム統計", report_file_path)
        else:
            f.slack_api.post_message(client, channel, f.message.no_hits(argument, command_option))
    elif command_option["personal"]:
        report_file_path = personal.plot(argument, command_option)
        if report_file_path:
            f.slack_api.post_fileupload(client, channel, "個人成績", report_file_path)
        else:
            f.slack_api.post_message(client, channel, f.message.no_hits(argument, command_option))
    else:
        report_file_path = winner.plot(argument, command_option)
        if report_file_path:
            f.slack_api.post_fileupload(client, channel, "成績上位者", report_file_path)
        else:
            f.slack_api.post_message(client, channel, f.message.no_hits(argument, command_option))
