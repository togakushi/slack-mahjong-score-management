import random
from datetime import datetime

from dateutil.relativedelta import relativedelta

from lib.function import global_value as g


def help(command):
    msg = f"```使い方："
    msg += f"\n\t{command} help          このメッセージ"
    msg += f"\n\t{command} results       成績出力"
    msg += f"\n\t{command} ranking       ランキング出力"
    msg += f"\n\t{command} record        張り付け用集計済みデータ出力"
    msg += f"\n\t{command} graph         ポイント推移グラフを表示"
    msg += f"\n\t{command} ranking       ランキングを表示"
    msg += f"\n\t{command} check         データ突合"
    msg += f"\n\t{command} download      データベースダウンロード"
    msg += f"\n\t{command} member        登録されているメンバー"
    msg += f"\n\t{command} add | del     メンバーの追加/削除"
    msg += f"```"
    return(msg)


def invalid_argument():
    return(random.choice([
        f"えっ？",
        f"すみません、よくわかりません。",
        f"困らせないでください。",
    ]))


def invalid_score(user_id, score, pointsum):
    rpoint_diff = abs(pointsum - score) * 100
    if "invalid_score" in g.config.sections():
        select_msg = [random.choice([i for i in g.config["invalid_score"]])][0]
        msg = g.config["invalid_score"][select_msg]
    else:
        msg = "{rpoint_diff}点合っていません。"

    return(f"<@{user_id}> " + msg.format(rpoint_diff = rpoint_diff))


def no_hits(starttime, endtime):
    keyword = g.config["search"].get("keyword", False)
    if keyword:
        return(
            "{} ～ {} に{}はありません。".format(
                starttime.strftime('%Y/%m/%d %H:%M'),
                endtime.strftime('%Y/%m/%d %H:%M'),
                keyword,
            )
        )
    else:
        return("見つかりません。")

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
