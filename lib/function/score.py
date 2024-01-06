import lib.function as f
from lib.function import global_value as g


def CalculationPoint(rpoint, rank):
    """
    順位点を計算して獲得ポイントを返す

    Parameters
    ----------
    rpoint : int
        素点

    rank : int
        着順（1位→1、2位→2、、、）

    Returns
    -------
    float : float
        獲得ポイント
    """

    p = g.config["mahjong"].getint("point", 250)
    r = g.config["mahjong"].getint("return", 300)
    u = g.config["mahjong"].get("rank_point", "30,10,-10,-30")

    oka = (r - p) * 4 / 10
    uma = [int(x) for x in u.split(",")]
    uma[0] = uma[0] + oka
    point = (rpoint - r) / 10 + uma[rank - 1]

    return(float(f"{point:>.1f}"))

def CalculationPoint2(rpoint_data, rpoint, seat):
    """
    素点データと獲得素点から獲得ポイントと順位を返す

    Parameters
    ----------
    rpoint_data : list
        全員分の素点リスト

    rpoint : int
        対象プレイヤーの素点

    seat : int
        対象プレイヤーの座席
        (0:東家 1:南家 2:西家 3:北家)

    Returns
    -------
    rank : int
        獲得順位

    point : float
        獲得ポイント
    """

    temp_data = []
    correction = [0.000004, 0.000003, 0.000002, 0.000001]
    for i in range(len(rpoint_data)):
        temp_data.append(rpoint_data[i] + correction[i])

    temp_data.sort(reverse = True)
    rank = temp_data.index(rpoint + correction[seat]) + 1
    point = CalculationPoint(rpoint, rank)

    return(rank, point)


def check_score(client, channel_id, event_ts, user, msg):
    """
    postされた素点合計が配給原点と同じかチェック
    """


    correct_score = g.config["mahjong"].getint("point", 250) * 4
    rpoint_sum = eval(msg[1]) + eval(msg[3]) + eval(msg[5]) + eval(msg[7])

    g.logging.notice("post data:[東 {} {}][南 {} {}][西 {} {}][北 {} {}][供託 {}]".format(
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
