import random


def message():
    return(random.choice([
        f"えっ？",
        f"すみません、よくわかりません。",
        f"困らせないでください。",
    ]))


def invalid_score(user_id, score):
    return(random.choice([
        f"<@{user_id}> {abs(1000-score)*100}点合わないようです。",
        f"<@{user_id}> {abs(1000-score)*100}点合いませんが。",
        f"<@{user_id}> {abs(1000-score)*100}点合いません。ご確認を。",
        f"<@{user_id}> ・・・。{abs(1000-score)*100}点合ってませんね・・・。",
    ]))

