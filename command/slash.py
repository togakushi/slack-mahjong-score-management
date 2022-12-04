import command as c
import function as f
from function import global_value as g

commandname = g.config["slash"].get("commandname", "/goburei")


def subcommand_list(subcommand):
    """
    サブコマンドのリストを返す

    Parameters
    ----------
    subcommand : str
        サブコマンド名
    
    Returns
    -------
    commandlist : list
        エイリアスを含めたサブコマンドのリスト
    """

    commandlist = g.config["alias"].get(subcommand, "")
    commandlist = [subcommand] + [x for x in commandlist.split(",") if x]

    return(commandlist)


@g.app.command(commandname)
def slash_command(ack, body, client):
    ack()
    user_id = body["user_id"]

    if body["text"]:
        subcom = body["text"].split()[0]
        argument = body["text"].split()[1:]

        # 成績管理系コマンド
        if subcom.lower() in subcommand_list("results"):
            command_option = f.command_option_initialization("results")
            g.logging.info(f"[subcommand({subcom})] {argument} {command_option}")
            c.results.slackpost(client, user_id, argument, command_option)
            return

        if subcom.lower() in subcommand_list("graph"):
            command_option = f.command_option_initialization("graph")
            g.logging.info(f"[subcommand({subcom})] {argument} {command_option}")
            c.graph.slackpost(client, user_id, argument, command_option)
            return

        if subcom.lower() in subcommand_list("record"):
            command_option = f.command_option_initialization("record")
            g.logging.info(f"[subcommand({subcom})] {argument} {command_option}")
            c.record.slackpost(client, user_id, argument, command_option)
            return

        # メンバー管理系コマンド
        if subcom.lower() in subcommand_list("member"):
            title, msg = c.member.list()
            f.slack_api.post_text(client, user_id, title, msg)
            return

        if subcom.lower() in subcommand_list("add"):
            msg = c.member.Append(argument)
            f.slack_api.post_message(client, user_id, msg)
            return

        if subcom.lower() in subcommand_list("del"):
            msg = c.member.Remove(argument)
            f.slack_api.post_message(client, user_id, msg)
            return

        if subcom.lower() in subcommand_list("load"):
            g.player_list = f.common.configload(g.memberfile)
            f.slack_api.post_message(client, user_id, f"メンバーリストを再読み込みしました。")
            return

        if subcom.lower() in subcommand_list("save"):
            f.common.configsave(g.player_list, g.memberfile)
            f.slack_api.post_message(client, user_id, f"メンバーリストを保存しました。")
            return

        #if subcom.lower() in subcommand_list("export"):
        #    command_option = f.command_option_initialization("record") # 一旦recordに合わせる
        #    g.logging.info(f"[subcommand({subcom})] {argument} {command_option}")
        #    exportfile = f.score.csv_export(argument, command_option)
        #    f.slack_api.post_message(client, user_id, f"{exportfile}に保存しました。")
        #    return

    f.slack_api.post_message(client, user_id, f.message.help(body["command"]))
