"""
libs/functions/tools/score_simulator.py

得点シミュレーター

Returns:
    list: ゲーム終了時点の素点リスト
"""

import random
from typing import Union

INITIAL_POINTS: int = 25000
MAX_ROUNDS: int = 8

# 点数テーブル
HAN_POINTS: dict[int, dict[str, Union[int, tuple[int, ...]]]] = {
    1: {"ron_child": 1300, "ron_parent": 2000, "tsumo_child": (300, 500), "tsumo_parent": (500,)},
    2: {"ron_child": 2600, "ron_parent": 3900, "tsumo_child": (500, 1000), "tsumo_parent": (1000,)},
    3: {"ron_child": 5200, "ron_parent": 7700, "tsumo_child": (1000, 2000), "tsumo_parent": (2000,)},
    4: {"ron_child": 8000, "ron_parent": 12000, "tsumo_child": (2000, 4000), "tsumo_parent": (4000,)},
    5: {"ron_child": 8000, "ron_parent": 12000, "tsumo_child": (2000, 4000), "tsumo_parent": (4000,)},
    6: {"ron_child": 12000, "ron_parent": 18000, "tsumo_child": (3000, 6000), "tsumo_parent": (6000,)},
    7: {"ron_child": 12000, "ron_parent": 18000, "tsumo_child": (3000, 6000), "tsumo_parent": (6000,)},
    8: {"ron_child": 16000, "ron_parent": 24000, "tsumo_child": (4000, 8000), "tsumo_parent": (8000,)},
    9: {"ron_child": 16000, "ron_parent": 24000, "tsumo_child": (4000, 8000), "tsumo_parent": (8000,)},
    10: {"ron_child": 24000, "ron_parent": 36000, "tsumo_child": (6000, 12000), "tsumo_parent": (12000,)},
    11: {"ron_child": 24000, "ron_parent": 36000, "tsumo_child": (6000, 12000), "tsumo_parent": (12000,)},
    12: {"ron_child": 24000, "ron_parent": 36000, "tsumo_child": (6000, 12000), "tsumo_parent": (12000,)},
    13: {"ron_child": 32000, "ron_parent": 48000, "tsumo_child": (8000, 16000), "tsumo_parent": (16000,)},
    14: {"ron_child": 32000, "ron_parent": 48000, "tsumo_child": (8000, 16000), "tsumo_parent": (16000,)},
    15: {  # ダブル役満扱い
        "ron_child": 64000,
        "ron_parent": 96000,
        "tsumo_child": (16000, 32000),
        "tsumo_parent": (32000,),
    },
}


def determine_point(is_parent: bool, is_tsumo: bool) -> int | tuple:
    """和了打点を決める

    Args:
        is_parent (bool): 親フラグ
        is_tsumo (bool): ツモ/被ツモフラグ

    Returns:
        int | tuple: 打点
    """

    rank = 1
    while rank < 15:
        success_prob = max([0, 0.6 - 0.02 * rank])
        if random.random() > success_prob:
            break
        rank += 1

    key = (
        "tsumo_parent"
        if is_parent and is_tsumo
        else "tsumo_child"
        if not is_parent and is_tsumo
        else "ron_parent"
        if is_parent
        else "ron_child"
    )

    return HAN_POINTS[rank][key]


def determine_winner(k: int) -> tuple[list[int], list[int]]:
    """和了役を抽選し、放銃役候補と分けてリストを返す

    Args:
        k (int): 和了役に選ばれる人数

    Returns:
        tuple[list, list]: 抽選結果
    """

    member = list(range(4))
    winners = random.sample(member, k=k)  # 和了役
    losers = [i for i in member if i not in winners]

    return (winners, losers)


def should_renchan(
    winners: list, parent: int, tenpai: list, total_rounds: int, renchan_count: int
) -> tuple[int, int, int]:
    """連チャンの判定を行う

    Args:
        winners (list): 和了者のリスト（流局時は空リスト）
        parent (int): 現在の親
        tenpai (list): 流局時のテンパイ状況（和了時は空リスト）
        total_rounds (int): 現在の局数
        renchan_count (int): 現在の連チャン数


    Returns:
        tuple[int, int, int]:
        - int: 判定後の局数
        - int: 判定後の連チャン数
        - int: 次の親
    """

    flg: bool = False
    if winners:
        flg = parent in winners  # 和了時: 親が和了していれば連チャン
    elif tenpai:
        flg = tenpai[parent]  # 流局時: 親がテンパイしていれば連チャン

    if flg:
        renchan_count += 1
    else:
        parent = (parent + 1) % 4
        renchan_count = 0
        total_rounds += 1

    return (total_rounds, renchan_count, parent)


def simulate_game():
    """ゲーム進行シミュレーション"""
    scores: list = [INITIAL_POINTS] * 4  # 配給原点(0:東家 1:南家 2:西家 3:北家)
    parent: int = 0  # 親番
    total_rounds: int = 0  # 局数
    renchan_count: int = 0  # 本場

    while total_rounds < MAX_ROUNDS:
        member = list(range(4))  # 0:東家 1:南家 2:西家 3:北家
        wins = [random.random() < 0.23 for _ in member]  # 和了判定
        num_wins = sum(wins)

        if num_wins in [2, 3] and random.random() < 0.01:  # ダブロン発生
            winners, losers = determine_winner(num_wins)
            discarder = random.choice(losers)  # 放銃役

            for winner in winners:
                is_parent = winner == parent
                point = determine_point(is_parent, False)
                assert isinstance(point, int), "point should be a int"
                scores[winner] += point + 300 * renchan_count
                scores[discarder] -= point + 300 * renchan_count

            total_rounds, renchan_count, parent = should_renchan(winners, parent, [], total_rounds, renchan_count)

        elif num_wins in [1, 2, 3]:  # 通常の和了処理
            winners, losers = determine_winner(1)
            winner = winners[0]  # 和了役
            is_parent = winner == parent  # 和了役が親か？

            if random.random() > 0.75:  # ツモによる点数移動
                point_data = determine_point(is_parent, True)
                assert isinstance(point_data, tuple), "point_data should be a tuple"
                for i in losers:
                    pay = point_data[1] if i == parent else point_data[0]
                    scores[i] -= pay + 100 * renchan_count
                    scores[winner] += pay + 100 * renchan_count
            else:  # 被ツモによる点数移動
                discarder = random.choice(losers)  # 放銃役
                pay = determine_point(is_parent, False)
                assert isinstance(pay, int), "pay should be a int"
                scores[discarder] -= pay + 300 * renchan_count
                scores[winner] += pay + 300 * renchan_count

            total_rounds, renchan_count, parent = should_renchan(winners, parent, [], total_rounds, renchan_count)

        else:  # 流局処理
            tenpai = [random.random() < 0.25 for _ in member]
            noten = [not x for x in tenpai]
            payment = []

            if not (all(tenpai) or all(noten)):
                for i in tenpai:
                    if i:
                        payment.append(int(3000 / sum(tenpai)))
                    else:
                        payment.append(int(-3000 / sum(noten)))

                for i in member:
                    scores[i] += payment[i]

            total_rounds, renchan_count, parent = should_renchan([], parent, tenpai, total_rounds, renchan_count)

        if any(score < 0 for score in scores):
            break

    return scores


if __name__ == "__main__":
    final_scores = simulate_game()
    print("最終素点:", final_scores, "素点合計", sum(final_scores))
