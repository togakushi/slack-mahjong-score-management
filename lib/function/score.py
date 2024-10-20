import logging

import pandas as pd

import global_value as g
from lib import command as c
from lib import database as d
from lib import function as f


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
    uma = g.cfg.config["mahjong"].get("rank_point", "30,10,-10,-30")  # ウマ
    rank_point = list(map(int, uma.split(",")))
    rank_point[0] += int((g.prm.return_point - g.prm.origin_point) / 10 * 4)  # オカ

    if g.cfg.config["mahjong"].getboolean("draw_split", False):  # 山分け
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
        score_df.at[x.Index, x.point] = (x.rpoint - g.prm.return_point) / 10 + rank_point[x.position - 1]

    logging.info(f"{rank_point=}")
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


def reactions(param: dict):
    """
    素点合計をチェックしリアクションを付ける

    Parameters
    ----------
    param : dict
        素点データ
    """

    correct_score = g.prm.origin_point * 4  # 配給原点
    rpoint_sum = param["rpoint_sum"]  # 素点合計

    icon = f.slack_api.reactions_status()

    if rpoint_sum == correct_score:
        if g.cfg.setting.reaction_ng in icon:
            f.slack_api.call_reactions_remove(g.cfg.setting.reaction_ng)
        if g.cfg.setting.reaction_ok not in icon:
            f.slack_api.call_reactions_add(g.cfg.setting.reaction_ok)
    else:
        if g.cfg.setting.reaction_ok in icon:
            f.slack_api.call_reactions_remove(g.cfg.setting.reaction_ok)
        if g.cfg.setting.reaction_ng not in icon:
            f.slack_api.call_reactions_add(g.cfg.setting.reaction_ng)

        f.slack_api.post_message(
            f.message.invalid_score(g.msg.user_id, rpoint_sum, correct_score),
            g.msg.event_ts
        )


def check_remarks():
    """
    メモの内容を拾ってDBに格納する
    """

    game_result = d.common.exsist_record(g.msg.thread_ts)
    if game_result:  # ゲーム結果のスレッドになっているか
        check_list = [v for k, v in game_result.items() if k.endswith("_name")]

        g.opt.initialization("results")
        g.opt.unregistered_replace = False  # ゲスト無効
        match g.msg.status:
            case "message_append" | "message_changed":
                remarks = {}
                for name, matter in zip(g.msg.argument[0::2], g.msg.argument[1::2]):
                    target_name = c.member.name_replace(name)
                    if target_name in check_list:
                        remarks.update(
                            thread_ts=g.msg.thread_ts,
                            event_ts=g.msg.event_ts,
                            name=target_name,
                            matter=matter,
                        )
                        d.common.remarks_append(remarks)
                    else:
                        d.common.remarks_delete(g.msg.event_ts)
            case "message_deleted":
                d.common.remarks_delete(g.msg.event_ts)
    else:
        d.common.remarks_delete(g.msg.event_ts)


def get_score(detection):
    """
    順位と獲得ポイントを計算する

    Parameters
    ----------
    detection : list
        素点データ(名前, 素点) x 4人分 + ゲームコメント

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
            c.member.name_replace(detection[x * 2], False)
            for x in range(4)
        ],
        "str": [detection[x * 2 + 1] for x in range(4)],
        "rpoint": [eval(detection[x * 2 + 1]) for x in range(4)],
    })
    score_df = calculation_point(score_df)
    score = score_df.to_dict(orient="records")
    rpoint_sum = int(score_df["rpoint"].sum())
    deposit = g.prm.origin_point * 4 - rpoint_sum

    ret = {
        "deposit": deposit,
        "rpoint_sum": rpoint_sum,
        "comment": detection[8],
    }
    ret.update(dict(zip([f"p1_{x}" for x in list(score[0])], list(score[0].values()))))
    ret.update(dict(zip([f"p2_{x}" for x in list(score[1])], list(score[1].values()))))
    ret.update(dict(zip([f"p3_{x}" for x in list(score[2])], list(score[2].values()))))
    ret.update(dict(zip([f"p4_{x}" for x in list(score[3])], list(score[3].values()))))

    logging.info(
        "score data:[東 {} {}][南 {} {}][西 {} {}][北 {} {}][供託 {}]".format(
            ret["p1_name"], ret["p1_rpoint"],
            ret["p2_name"], ret["p2_rpoint"],
            ret["p3_name"], ret["p3_rpoint"],
            ret["p4_name"], ret["p4_rpoint"],
            ret["deposit"],
        )
    )

    return (ret)
