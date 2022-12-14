import random

from function import global_value as g


def help(command):
    msg = f"```使い方："
    msg += f"\n\t{command} help          このメッセージ"
    msg += f"\n\t{command} results       成績出力"
    msg += f"\n\t{command} record        張り付け用集計済みデータ出力"
    msg += f"\n\t{command} graph         ポイント推移グラフを表示"
    msg += f"\n\t{command} member        登録されているメンバー"
    msg += f"\n\t{command} add | del     メンバーの追加/削除"
    msg += f"\n\t{command} load | save   メンバーリストの再読み込み/保存"
    msg += f"```"
    return(msg)


def invalid_argument():
    return(random.choice([
        f"えっ？",
        f"すみません、よくわかりません。",
        f"困らせないでください。",
    ]))


def invalid_score(user_id, score, pointsum):
    return(random.choice([
        f"<@{user_id}> {abs(pointsum - score) * 100}点合わないようです。",
        f"<@{user_id}> {abs(pointsum - score) * 100}点合いませんよ。",
        f"<@{user_id}> {abs(pointsum - score) * 100}点合いません。ご確認を。",
        f"<@{user_id}> {abs(pointsum - score) * 100}点合ってませんね。",
    ]))


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
