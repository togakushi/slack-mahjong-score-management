import csv

from dateutil.relativedelta import relativedelta

import lib.command as c
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
    """

    temp_data = []
    correction = [0.000004, 0.000003, 0.000002, 0.000001]
    for i in range(len(rpoint_data)):
        temp_data.append(rpoint_data[i] + correction[i])

    temp_data.sort(reverse = True)
    rank = temp_data.index(rpoint + correction[seat]) + 1
    point = CalculationPoint(rpoint, rank)

    return(rank, point)
