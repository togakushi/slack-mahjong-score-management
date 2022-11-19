import random


def help(command):
    msg = f"```使い方："
    msg += f"\n\t{command} help                このメッセージ"
    msg += f"\n\t{command} results             成績出力"
    msg += f"\n\t{command} record              張り付け用集計済みデータ出力"
    msg += f"\n\t{command} allrecord           集計済み全データ出力(名前ブレ修正なし)"
    msg += f"\n\t{command} graph               ポイント推移グラフを表示"
    msg += f"\n\t{command} member | userlist   登録されているメンバー"
    msg += f"\n\t{command} add                 メンバーの追加"
    msg += f"\n\t{command} del                 メンバーの削除"
    msg += f"\n\t{command} load                メンバーリストの再読み込み"
    msg += f"\n\t{command} save                メンバーリストの保存"
    msg += f"```"
    return(msg)


def invalid_argument():
    return(random.choice([
        f"えっ？",
        f"すみません、よくわかりません。",
        f"困らせないでください。",
    ]))


def invalid_score(user_id, score):
    return(random.choice([
        f"<@{user_id}> {abs(1000-score)*100}点合わないようです。",
        f"<@{user_id}> {abs(1000-score)*100}点合いませんよ。",
        f"<@{user_id}> {abs(1000-score)*100}点合いません。ご確認を。",
        f"<@{user_id}> {abs(1000-score)*100}点合ってませんね。",
    ]))

