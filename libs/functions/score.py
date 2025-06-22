"""
libs/functions/score.py
"""

import logging
import re

import pandas as pd

import libs.global_value as g
from cls.types import ScoreDataDict


def calculation_point(score_df) -> pd.DataFrame:
    """素点データから獲得ポイントと順位を取得する

    Args:
        score_df (pd.DataFrame): 全員分の素点データ(東家から順)

    Returns:
        pd.DataFrame: 順位と獲得ポイントを追加したデータ
    """

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

    # 獲得ポイント計算
    score_df["point"] = "point"
    score_df["position"] = score_df["rpoint"].rank(
        ascending=False, method="first"
    ).astype("int")
    for x in score_df.itertuples():
        score_df.at[x.Index, x.point] = (x.rpoint - g.cfg.mahjong.return_point) / 10 + rank_point[x.position - 1]

    logging.trace("rank_point=%s", rank_point)  # type: ignore
    return score_df


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


def get_score(detection: ScoreDataDict) -> ScoreDataDict:
    """順位と獲得ポイントを計算する

    Args:
        detection (ScoreDataDict): スコアデータ

    Returns:
        ScoreDataDict: スコアデータ(計算結果追加)
    """

    g.params.update(unregistered_replace=False)  # ゲスト無効
    g.params.update(individual=True)

    # ポイント計算
    score_df = pd.DataFrame({
        "name": [str(v) for k, v in detection.items() if str(k).endswith("_name")],
        "str": [str(v) for k, v in detection.items() if str(k).endswith("_str")],
        "rpoint": [normalized_expression(str(v)) for k, v in detection.items() if str(k).endswith("_str")],
    })
    score_df = calculation_point(score_df)
    for idx in score_df.index:
        point = float(score_df.at[idx, "point"])
        detection[f"p{int(idx + 1)}_rpoint"] = int(score_df.at[idx, "rpoint"])  # type: ignore[literal-required]
        detection[f"p{int(idx + 1)}_point"] = float(f"{point:.1f}")  # type: ignore[literal-required]  # 桁ブレ修正
        detection[f"p{int(idx + 1)}_rank"] = int(score_df.at[idx, "rank"])  # type: ignore[literal-required]

    rpoint_sum = int(score_df["rpoint"].sum())
    detection["rpoint_sum"] = rpoint_sum
    detection["deposit"] = g.cfg.mahjong.origin_point * 4 - rpoint_sum

    logging.info(
        "score data:[東 %s %s][南 %s %s][西 %s %s][北 %s %s][供託 %s]",
        detection["p1_name"], detection["p1_rpoint"],
        detection["p2_name"], detection["p2_rpoint"],
        detection["p3_name"], detection["p3_rpoint"],
        detection["p4_name"], detection["p4_rpoint"],
        detection["deposit"],
    )

    return detection


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
