import command as c
import function as f
from function import global_value as g


commandname = g.config["slash"].get("commandname", "/goburei")
results_alias = g.config["alias"].get("results", "成績")
graph_alias = g.config["alias"].get("graph", "グラフ")
record_alias = g.config["alias"].get("record", "記録")

@g.app.command(commandname)
def goburei_command(ack, body, client):
    ack()
    user_id = body["user_id"]

    if body["text"]:
        subcom = body["text"].split()[0]
        argument = body["text"].split()[1:]

        # 成績管理系コマンド
        if subcom.lower() in (["results"] + results_alias.split(",")):
            command_option = f.command_option_initialization("results")
            g.logging.info(f"[subcommand({subcom})] {argument} {command_option}")
            c.results.slackpost(client, user_id, argument, command_option)
            return

        if subcom.lower() in (["graph"] + graph_alias.split(",")):
            command_option = f.command_option_initialization("graph")
            g.logging.info(f"[subcommand({subcom})] {argument} {command_option}")
            c.graph.slackpost(client, user_id, argument, command_option)
            return

        if subcom.lower() in (["record"] + record_alias.split(",")):
            command_option = f.command_option_initialization("record")
            g.logging.info(f"[subcommand({subcom})] {argument} {command_option}")
            title, msg = c.record.getdata(playername_replace = True, guest_skip = True)
            f.slack_api.post_upload(client, user_id, title, msg)
            return

        # メンバー管理系コマンド
        if subcom.lower() in ("member", "userlist", "メンバー", "リスト"):
            title, msg = c.member.list()
            f.slack_api.post_text(client, user_id, title, msg)
            return

        if subcom.lower() in ("add", "追加"):
            msg = c.member.Append(argument)
            f.slack_api.post_message(client, user_id, msg)
            return

        if subcom.lower() in ("del", "削除"):
            msg = c.member.Remove(argument)
            f.slack_api.post_message(client, user_id, msg)
            return

        if subcom.lower() in ("load"):
            g.player_list = f.options.configload(g.args.member)
            f.slack_api.post_message(client, user_id, f"メンバーリストを再読み込みしました。")
            return

        if subcom.lower() in ("save"):
            f.options.configsave(g.player_list, g.args.member)
            f.slack_api.post_message(client, user_id, f"メンバーリストを保存しました。")
            return

    f.slack_api.post_message(client, user_id, f.message.help(body["command"]))
