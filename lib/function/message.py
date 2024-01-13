import random

import lib.function as f
from lib.function import global_value as g


def help(command):
    msg = f"```使い方："
    msg += f"\n\t{command} help          このメッセージ"
    msg += f"\n\t{command} results       成績出力"
    msg += f"\n\t{command} ranking       ランキング出力"
    msg += f"\n\t{command} graph         ポイント推移グラフを表示"
    msg += f"\n\t{command} report        レポート表示"
    msg += f"\n\t{command} check         データ突合"
    msg += f"\n\t{command} download      データベースダウンロード"
    msg += f"\n\t{command} member        登録されているメンバー"
    msg += f"\n\t{command} add | del     メンバーの追加/削除"
    msg += f"```"
    return(msg)


def invalid_argument():
    msg = f"使い方が間違っています。"

    if "custom_message" in g.config.sections():
        key_list = []
        for i in g.config["custom_message"]:
            if i.startswith("invalid_argument"):
                key_list.append(i)
        if key_list:
            msg = g.config["custom_message"][random.choice(key_list)]

    return(msg)


def invalid_score(user_id, rpoint_sum, correct_score):
    rpoint_diff = abs(correct_score - rpoint_sum)
    msg = f"素点合計： {rpoint_sum}\n点数差分： {rpoint_diff}"

    if "custom_message" in g.config.sections():
        key_list = []
        for i in g.config["custom_message"]:
            if i.startswith("invalid_score"):
                key_list.append(i)
        if key_list:
            msg = g.config["custom_message"][random.choice(key_list)]

    return(f"<@{user_id}> " + msg.format(
        rpoint_diff = rpoint_diff * 100,
        rpoint_sum = rpoint_sum * 100,
    ))


def no_hits(argument, command_option):
    target_days, _, _, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)
    keyword = g.config["search"].get("keyword", "終局")
    start = starttime.strftime("%Y/%m/%d %H:%M")
    end = endtime.strftime("%Y/%m/%d %H:%M")
    msg = f"{start} ～ {end} に≪{keyword}≫はありません。"

    if "custom_message" in g.config.sections():
        key_list = []
        for i in g.config["custom_message"]:
            if i.startswith("no_hits"):
                key_list.append(i)
        if key_list:
            msg = g.config["custom_message"][random.choice(key_list)]

    return(msg.format(keyword = keyword, start = start, end = end))


def remarks(command_option):
    ret = ""
    remark = []

    if not command_option["guest_skip"]:
        remark.append("2ゲスト戦の結果を含む")
    if not command_option["unregistered_replace"]:
        remark.append("ゲスト置換なし("+ g.guest_mark + "：未登録プレイヤー)")
    if remark:
        ret = f"\t特記：" + "、".join(remark)

    return(ret)
