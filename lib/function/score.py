import logging
import sqlite3

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


def check_score(msg):
    """
    postされた素点合計が配給原点と同じかチェック
    """

    if g.msg.checked:
        return

    correct_score = g.prm.origin_point * 4
    rpoint_sum = eval(msg[1]) + eval(msg[3]) + eval(msg[5]) + eval(msg[7])

    logging.notice(  # type: ignore
        "post data:[東 {} {}][南 {} {}][西 {} {}][北 {} {}][供託 {}]".format(
            msg[0], msg[1], msg[2], msg[3], msg[4], msg[5], msg[6], msg[7],
            correct_score - rpoint_sum,
        )
    )

    f.slack_api.call_reactions_remove()
    if rpoint_sum == correct_score:  # 合計が一致している場合
        f.slack_api.call_reactions_add(g.cfg.setting.reaction_ok)
    else:  # 合計が不一致の場合
        f.slack_api.post_message(
            f.message.invalid_score(g.msg.user_id, rpoint_sum, correct_score),
            g.msg.event_ts
        )
        f.slack_api.call_reactions_add(g.cfg.setting.reaction_ng)

    g.msg.checked = True


def check_remarks():
    """
    メモの内容を拾ってDBに格納する
    """

    g.opt.initialization("results")
    g.opt.unregistered_replace = False  # ゲスト無効
    resultdb = sqlite3.connect(
        g.cfg.db.database_file,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )

    # スレッド元にあるメンバーを取得
    rows = resultdb.execute(
        "select p1_name, p2_name, p3_name, p4_name from result where ts == ?",
        (g.msg.thread_ts,)
    )
    check_list = rows.fetchone()

    match g.msg.status:
        case "message_append":
            for name, val in zip(g.msg.argument[0::2], g.msg.argument[1::2]):
                if c.member.NameReplace(name) in check_list:
                    logging.info(f"insert: {name}, {val}")
                    resultdb.execute(d.sql_remarks_insert, (
                        g.msg.thread_ts,
                        g.msg.event_ts,
                        c.member.NameReplace(name),
                        val,
                    ))
                    f.slack_api.call_reactions_add(g.cfg.setting.reaction_ok)
        case "message_changed":
            f.slack_api.call_reactions_remove()
            resultdb.execute(
                d.sql_remarks_delete_one,
                (g.msg.event_ts,)
            )
            for name, val in zip(g.msg.argument[0::2], g.msg.argument[1::2]):
                if name in check_list:
                    logging.info(f"update: {name}, {val}")
                    resultdb.execute(d.sql_remarks_insert, (
                        g.msg.thread_ts,
                        g.msg.event_ts,
                        c.member.NameReplace(name),
                        val,
                    ))
                    f.slack_api.call_reactions_add(g.cfg.setting.reaction_ok)
        case "message_deleted":
            logging.info("delete one")
            resultdb.execute(
                d.sql_remarks_delete_one,
                (g.msg.event_ts,)
            )

    resultdb.commit()
    resultdb.close()


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
        "deposit": g.prm.origin_point * 4 - int(score_df["rpoint"].sum()),
        "comment": msg[8],
    }
    ret.update(dict(zip([f"p1_{x}" for x in list(score[0])], list(score[0].values()))))
    ret.update(dict(zip([f"p2_{x}" for x in list(score[1])], list(score[1].values()))))
    ret.update(dict(zip([f"p3_{x}" for x in list(score[2])], list(score[2].values()))))
    ret.update(dict(zip([f"p4_{x}" for x in list(score[3])], list(score[3].values()))))

    return (ret)
