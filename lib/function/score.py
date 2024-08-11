import pandas as pd

import lib.command as c
import lib.function as f
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
    origin_point = g.config["mahjong"].getint("point", 250)  # 配給原点
    return_point = g.config["mahjong"].getint("return", 300)  # 返し点
    uma = g.config["mahjong"].get("rank_point", "30,10,-10,-30")  # ウマ
    rank_point = list(map(int, uma.split(",")))
    rank_point[0] += int((return_point - origin_point) / 10 * 4)  # type: ignore # オカ

    if g.config["mahjong"].getboolean("draw_split", False):  # 山分け
        score_df["rank"] = score_df["rpoint"].rank(
            ascending=False, method="min"
        ).astype("int")

        # 順位点リストの更新
        rank_sequence = "".join(
            score_df["rank"].sort_values().to_string(index=False).split()
        )
        match rank_sequence:
            case "1111":
                rank_point = point_split(rank_point)
            case "1114":
                new_point = point_split(rank_point[0:3])
                rank_point[0] = new_point[0]
                rank_point[1] = new_point[1]
                rank_point[2] = new_point[2]
            case "1134":
                new_point = point_split(rank_point[0:2])
                rank_point[0] = new_point[0]
                rank_point[1] = new_point[1]
            case "1133":
                new_point = point_split(rank_point[0:2])
                rank_point[0] = new_point[0]
                rank_point[1] = new_point[1]
                new_point = point_split(rank_point[2:4])
                rank_point[2] = new_point[0]
                rank_point[3] = new_point[1]
            case "1222":
                new_point = point_split(rank_point[1:4])
                rank_point[1] = new_point[0]
                rank_point[2] = new_point[1]
                rank_point[3] = new_point[2]
            case "1224":
                new_point = point_split(rank_point[1:3])
                rank_point[1] = new_point[0]
                rank_point[2] = new_point[1]
            case "1233":
                new_point = point_split(rank_point[2:4])
                rank_point[2] = new_point[0]
                rank_point[3] = new_point[1]
            case _:
                pass

    else:  # 席順
        score_df["rank"] = score_df["rpoint"].rank(
            ascending=False, method="first"
        ).astype("int")

    # 獲得ポイント計算
    score_df["point"] = "point"
    score_df["position"] = score_df["rpoint"].rank(
        ascending=False, method="first"
    ).astype("int")
    for x in score_df.itertuples():
        score_df.at[x.Index, x.point] = (x.rpoint - return_point) / 10 + rank_point[x.position - 1]

    g.logging.info(f"{rank_point=}")
    return (score_df)


def point_split(point: list):
    """
    順位点を山分けする

    Parameters
    ----------
    point : list
        山分けするポイントのリスト

    Returns
    -------
    new_point : list
        山分けした結果
    """

    new_point = [int(sum(point) / len(point))] * len(point)
    if sum(point) % len(point):
        new_point[0] += sum(point) % len(point)
        if sum(point) < 0:
            new_point = list(map(lambda x: x - 1, new_point))

    return (new_point)


def check_score(client, channel_id, event_ts, user, msg):
    """
    postされた素点合計が配給原点と同じかチェック
    """

    correct_score = g.config["mahjong"].getint("point", 250) * 4
    rpoint_sum = eval(msg[1]) + eval(msg[3]) + eval(msg[5]) + eval(msg[7])

    g.logging.notice(  # type: ignore
        "post data:[東 {} {}][南 {} {}][西 {} {}][北 {} {}][供託 {}]".format(
            msg[0], msg[1], msg[2], msg[3], msg[4], msg[5], msg[6], msg[7],
            correct_score - rpoint_sum,
        )
    )

    if rpoint_sum == correct_score:  # 合計が一致している場合
        client.reactions_add(
            channel=channel_id,
            name=g.reaction_ok,
            timestamp=event_ts,
        )
    else:  # 合計が不一致の場合
        msg = f.message.invalid_score(user, rpoint_sum, correct_score)
        f.slack_api.post_message(client, channel_id, msg, event_ts)
        client.reactions_add(
            channel=channel_id,
            name=g.reaction_ng,
            timestamp=event_ts,
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

    g.opt.unregistered_replace = False  # ゲスト無効

    # ポイント計算
    score_df = pd.DataFrame({
        "name": [
            c.member.NameReplace(msg[x * 2], False)
            for x in range(4)
        ],
        "str": [msg[x * 2 + 1] for x in range(4)],
        "rpoint": [eval(msg[x * 2 + 1]) for x in range(4)],
    })
    score_df = calculation_point(score_df)
    score = score_df.to_dict(orient="records")

    ret = {
        "deposit": g.config["mahjong"].getint("point", 250) * 4 - score_df["rpoint"].sum(),
        "comment": msg[8],
    }
    ret.update(dict(zip([f"p1_{x}" for x in list(score[0])], list(score[0].values()))))
    ret.update(dict(zip([f"p2_{x}" for x in list(score[1])], list(score[1].values()))))
    ret.update(dict(zip([f"p3_{x}" for x in list(score[2])], list(score[2].values()))))
    ret.update(dict(zip([f"p4_{x}" for x in list(score[3])], list(score[3].values()))))

    return (ret)
