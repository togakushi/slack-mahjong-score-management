import pandas as pd

import lib.function as f
import lib.command as c
from lib.function import global_value as g


def calculation_point(score_df):
    """
    素点データから獲得ポイントと順位を取得する

    Parameters
    ----------
    score_df : DataFrame
        全員分の素点データ(東家から順)

    Returns
    -------
    score_df : DataFrame
        順位と獲得ポイントを追加したデータ
    """

    # 順位点算出
    origin_point  = g.config["mahjong"].getint("point", 250) # 配給原点
    return_point = g.config["mahjong"].getint("return", 300) # 返し点
    uma = g.config["mahjong"].get("rank_point", "30,10,-10,-30") # ウマ
    rank_point = [int(x) for x in uma.split(",")]
    rank_point[0] += (return_point - origin_point) / 10 * 4 # type: ignore # オカ

    # 同点は席順で決定するパターン
    score_df["rank"] = score_df.rank(numeric_only = True, ascending = False, method = "first").astype("int")
    score_df["point"] = [
        (x["rpoint"] - return_point) / 10 + rank_point[x["rank"] - 1]
        for _, x in score_df.iterrows()
    ]

    # ToDo: 同点は順位点を山分けするパターン

    return(score_df)


def check_score(client, channel_id, event_ts, user, msg):
    """
    postされた素点合計が配給原点と同じかチェック
    """


    correct_score = g.config["mahjong"].getint("point", 250) * 4
    rpoint_sum = eval(msg[1]) + eval(msg[3]) + eval(msg[5]) + eval(msg[7])

    g.logging.notice("post data:[東 {} {}][南 {} {}][西 {} {}][北 {} {}][供託 {}]".format( # type: ignore
        msg[0], msg[1], msg[2], msg[3], msg[4], msg[5], msg[6], msg[7],
        correct_score - rpoint_sum,
        )
    )

    if rpoint_sum == correct_score: # 合計が一致している場合
        client.reactions_add(
            channel = channel_id,
            name = g.reaction_ok,
            timestamp = event_ts,
        )
    else: # 合計が不一致の場合
        msg = f.message.invalid_score(user, rpoint_sum, correct_score)
        f.slack_api.post_message(client, channel_id, msg, event_ts) #
        client.reactions_add(
            channel = channel_id,
            name = g.reaction_ng,
            timestamp = event_ts,
        )


def get_score(msg):
    """
    postされた内容から素点を抽出し、順位と獲得ポイントを計算する

    Parameters
    ----------
    msg : list
        postされたデータ(名前, 素点)

    Returns
    -------
    ret : dict
        名前(p?_name), 素点文字列(p?_str), 素点(p?_rpoint),
        ポイント(p?_point), 順位(p?_rank), 供託(deposit), コメント(comment)
    """

    command_option = {}
    command_option["unregistered_replace"] = False # ゲスト無効

    # ポイント計算
    score_df = pd.DataFrame({
        "name": [
            c.member.NameReplace(msg[x * 2], command_option, False)
            for x in range(4)
        ],
        "str": [msg[x * 2 + 1] for x in range(4)],
        "rpoint": [eval(msg[x * 2 + 1]) for x in range(4)],
    })
    score_df = calculation_point(score_df)
    score = score_df.to_dict(orient = "records")

    ret = {
        "deposit": g.config["mahjong"].getint("point", 250) * 4 - score_df["rpoint"].sum(),
        "comment": msg[8],
    }
    ret.update(dict(zip([f"p1_{x}" for x in list(score[0])], list(score[0].values()))))
    ret.update(dict(zip([f"p2_{x}" for x in list(score[1])], list(score[1].values()))))
    ret.update(dict(zip([f"p3_{x}" for x in list(score[2])], list(score[2].values()))))
    ret.update(dict(zip([f"p4_{x}" for x in list(score[3])], list(score[3].values()))))

    return(ret)
