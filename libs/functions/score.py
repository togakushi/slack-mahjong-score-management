"""
libs/functions/score.py
"""

import logging
import re

import pandas as pd

import libs.global_value as g


def point_split(point: list) -> list:
    """順位点を山分けする

    Args:
        point (list): 山分けするポイントのリスト

    Returns:
        list: 山分けした結果
    """

    new_point = [int(sum(point) / len(point))] * len(point)
    if sum(point) % len(point):
        new_point[0] += sum(point) % len(point)
        if sum(point) < 0:
            new_point = list(map(lambda x: x - 1, new_point))

    return new_point


def calculation_point(score_list: list[str]) -> dict:
    """獲得ポイントと順位を計算する

    Args:
        score_list (list[str]): 素点リスト

    Returns:
        dict: 更新用辞書(順位と獲得ポイントのデータ)
    """

    # 計算用データフレーム
    score_df = pd.DataFrame(
        {"rpoint": [normalized_expression(x) for x in score_list]},
        index=["p1", "p2", "p3", "p4"]
    )

    # 順位点算出
    rank_point = g.cfg.mahjong.rank_point.copy()  # ウマ
    rank_point[0] += int((g.cfg.mahjong.return_point - g.cfg.mahjong.origin_point) / 10 * 4)  # オカ

    if g.cfg.mahjong.draw_split:  # 山分け
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

    logging.trace("rank_point=%s", rank_point)  # type: ignore

    # 獲得ポイントの計算 (素点-配給原点)/10+順位点
    score_df["position"] = score_df["rpoint"].rank(  # 加算する順位点リストの位置
        ascending=False, method="first"
    ).astype("int")
    score_df["point"] = (score_df["rpoint"] - g.cfg.mahjong.return_point) / 10 + score_df["position"].apply(lambda p: rank_point[p - 1])
    score_df["point"] = score_df["point"].apply(lambda p: float(f"{p:.1f}"))  # 桁ブレ修正

    # 返却値用辞書
    ret_dict = {f"{k}_{x}": v for x in score_df.columns for k, v in score_df[x].to_dict().items()}
    ret_dict.update(deposit=int(g.cfg.mahjong.origin_point * 4 - score_df["rpoint"].sum()))

    return ret_dict


def normalized_expression(expr: str) -> int:
    """入力文字列を式として評価し、計算結果を返す

    Args:
        expr (str): 入力式

    Returns:
        int: 計算結果
    """

    normalized: list = []

    for token in re.findall(r"\d+|[+\-*/]", expr):
        if isinstance(token, str):
            if token.isnumeric():
                normalized.append(str(int(token)))
            else:
                normalized.append(token)

    return eval("".join(normalized))  # pylint: disable=eval-used
