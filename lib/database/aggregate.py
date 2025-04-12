"""
lib/database/aggregate.py
"""

import logging
import os
from datetime import datetime
from typing import cast

import numpy as np
import pandas as pd

import lib.global_value as g
from lib import command as c
from lib.database.common import read_data


def game_info():
    """指定条件を満たすゲーム数のカウント、最初と最後の時刻とコメントを取得

    Returns:
        dict: 取得したデータ
            - game_count: int
            - first_game: datetime
            - last_game: datetime
            - first_comment: str
            - last_comment: str
    """

    # データ収集
    df = read_data(os.path.join(g.script_dir, "lib/queries/game.info.sql"))

    ret = {
        "game_count": int(df["count"].to_string(index=False)),
        "first_game": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        "last_game": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        "first_comment": None,
        "last_comment": None,
    }

    if cast(int, ret["game_count"]) >= 1:
        ret["first_game"] = df["first_game"].to_string(index=False).replace("-", "/")
        ret["last_game"] = df["last_game"].to_string(index=False).replace("-", "/")
        ret["first_comment"] = df["first_comment"].to_string(index=False)
        ret["last_comment"] = df["last_comment"].to_string(index=False)

    # 規定打数更新
    match g.params.get("command", ""):
        case "results":
            old_stipulated = g.cfg.results.stipulated
            new_stipulated = g.cfg.results.stipulated_calculation(ret["game_count"])
        case "graph":
            old_stipulated = g.cfg.graph.stipulated
            new_stipulated = g.cfg.graph.stipulated_calculation(ret["game_count"])
        case "ranking":
            old_stipulated = g.cfg.ranking.stipulated
            new_stipulated = g.cfg.ranking.stipulated_calculation(ret["game_count"])
        case "report":
            old_stipulated = g.cfg.report.stipulated
            new_stipulated = g.cfg.report.stipulated_calculation(ret["game_count"])

    if not old_stipulated:  # 規定打数が0なら更新
        g.params.update(stipulated=new_stipulated)

    logging.info("return: %s", ret)
    return (ret)


def game_summary(filter_items: list | None = None, drop_items: list | None = None) -> pd.DataFrame:
    """ゲーム結果をサマライズする

    Args:
        filter_items (list | None, optional): 抽出するカラム. Defaults to None.
        drop_items (list | None, optional): 除外するカラム. Defaults to None.

    Returns:
        pd.DataFrame: 集計結果
    """

    # データ収集
    df = read_data(os.path.join(g.script_dir, "lib/queries/summary/total.sql"))

    if isinstance(filter_items, list):
        df = df.filter(items=filter_items)

    if isinstance(drop_items, list):
        df = df.drop(columns=drop_items)

    logging.trace(df)  # type: ignore
    return (df)


def remark_count(kind: str):
    """メモの内容を種別でカウント

    Args:
        kind (str): 集計種別

    Returns:
        pd.DataFrame: 集計結果
    """

    # データ収集
    g.params.update(kind=kind)
    df = read_data(os.path.join(g.script_dir, "lib/queries/summary/remark_count.sql"))

    if kind == "grandslam":
        df = df.filter(items=["name", "matter", "count"])

    logging.trace(df)  # type: ignore
    return (df)


def game_results():
    """成績を集計する

    Returns:
        pd.DataFrame: 集計結果
    """

    # データ収集
    df = read_data(os.path.join(g.script_dir, "lib/queries/summary/results.sql"))

    # Nullが返ってきたときにobject型になるので型変換
    df = df.astype({
        "東家-平均順位": "float", "南家-平均順位": "float", "西家-平均順位": "float", "北家-平均順位": "float",
        "東家-役満和了": "Int64", "南家-役満和了": "Int64", "西家-役満和了": "Int64", "北家-役満和了": "Int64",
    }).fillna(0)

    # インデックスの振り直し
    df = df.reset_index(drop=True)
    df.index = df.index + 1

    logging.trace(df)  # type: ignore
    return (df)


# ランキング
def ranking_record():
    """ランキング集計

    Returns:
        pd.DataFrame: 集計結果
    """

    # データ収集
    gamedata: pd.DataFrame = read_data(os.path.join(g.script_dir, "lib/queries/ranking/record_count.sql"))
    player_list = gamedata["name"].unique().tolist()

    # 連続順位カウント
    rank_mask = {
        "c_top": {1: 1, 2: 0, 3: 0, 4: 0},  # 連続トップ
        "c_top2": {1: 1, 2: 1, 3: 0, 4: 0},  # 連続連対
        "c_top3": {1: 1, 2: 1, 3: 1, 4: 0},  # 連続ラス回避
        "c_low": {1: 0, 2: 1, 3: 1, 4: 1},  # 連続トップなし
        "c_low2": {1: 0, 2: 0, 3: 1, 4: 1},  # 連続逆連対
        "c_low4": {1: 0, 2: 0, 3: 0, 4: 1},  # 連続ラス
    }

    record_df = pd.DataFrame(
        {
            "name": player_list,
            "c_top": [0 for x in player_list],
            "c_top2": [0 for x in player_list],
            "c_top3": [0 for x in player_list],
            "c_low": [0 for x in player_list],
            "c_low2": [0 for x in player_list],
            "c_low4": [0 for x in player_list],
        },
        index=player_list
    )

    for key, val in rank_mask.items():
        for pname in player_list:
            tmp_df = pd.DataFrame()
            tmp_df["flg"] = gamedata.query(
                "name == @pname"
            )["順位"].replace(val)

            tmp_df[key] = tmp_df["flg"].groupby(
                (tmp_df["flg"] != tmp_df["flg"].shift()).cumsum()
            ).cumcount() + 1
            tmp_df.loc[tmp_df["flg"] == 0, key] = 0
            record_df.at[pname, key] = tmp_df[[key]].max().values[0]

    # 最大値/最小値追加
    record_df["max_point"] = gamedata["max_point"].iloc[0]
    record_df["min_point"] = gamedata["min_point"].iloc[0]
    record_df["max_rpoint"] = gamedata["max_rpoint"].iloc[0]
    record_df["min_rpoint"] = gamedata["min_rpoint"].iloc[0]

    logging.trace(record_df)  # type: ignore
    return (record_df)


def calculation_rating():
    """レーティング集計

    Returns:
        pd.DataFrame: 集計結果
    """

    # データ収集
    df_results = read_data(os.path.join(g.script_dir, "lib/queries/ranking/ratings.sql")).set_index("playtime")
    df_ratings = pd.DataFrame(index=["initial_rating"] + df_results.index.to_list())  # 記録用
    last_ratings: dict = {}  # 最終値格納用

    # 獲得スコア
    score_mapping = {"1": 30.0, "2": 10.0, "3": -10.0, "4": -30.0}

    for x in df_results.itertuples():
        player_list = (x.p1_name, x.p2_name, x.p3_name, x.p4_name)
        for player in player_list:
            if player not in df_ratings.columns:
                last_ratings[player] = 1500.0
                df_ratings[player] = np.nan
                df_ratings.loc["initial_rating", player] = 1500.0
                df_ratings = df_ratings.copy()

        # 天鳳計算式 (https://tenhou.net/man/#RATING)
        rank_list = (x.p1_rank, x.p2_rank, x.p3_rank, x.p4_rank,)
        rating_list = [last_ratings[player] for player in player_list]
        rating_avg = 1500.0 if np.mean(rating_list) < 1500.0 else np.mean(rating_list)

        for i, player in enumerate(player_list):
            rating = float(rating_list[i])
            rank = str(rank_list[i])

            correction_value: float = (rating_avg - rating) / 40
            if df_ratings[player].count() >= 400:
                match_correction = 0.2
            else:
                match_correction = 1 - df_ratings[player].count() * 0.002

            new_rating = rating + match_correction * (score_mapping[rank] + correction_value)

            last_ratings[player] = new_rating
            df_ratings.loc[x.Index, player] = new_rating

    return (df_ratings)


# レポート
def matrix_table():
    """対局対戦マトリックス表の作成

    Returns:
        pd.DataFrame: 集計結果
    """

    # データ収集
    df = read_data(os.path.join(g.script_dir, "lib/queries/report/matrix_table.sql")).set_index("playtime")

    # 結果に含まれるプレイヤーのリスト
    plist = sorted(list(set(
        df["p1_name"].tolist() + df["p2_name"].tolist() + df["p3_name"].tolist() + df["p4_name"].tolist()
    )))

    # 順位テーブルの作成
    l_data: dict = {}
    for pname in plist:
        if g.params.get("individual"):  # 個人集計
            l_name = c.member.name_replace(pname)
            # プレイヤー指定があるなら対象以外をスキップ
            if g.params["player_list"]:
                if l_name not in g.params["player_list"].values():
                    continue
            # ゲスト置換
            if g.params.get("guest_skip"):  # ゲストあり
                l_name = c.member.name_replace(pname, add_mark=True)
            else:  # ゲストなし
                if pname == g.cfg.member.guest_name:
                    continue
        else:  # チーム集計
            l_name = pname

        l_data[l_name] = []
        for x in df.itertuples():
            match pname:
                case x.p1_name:
                    l_data[l_name] += [x.p1_rank]
                case x.p2_name:
                    l_data[l_name] += [x.p2_rank]
                case x.p3_name:
                    l_data[l_name] += [x.p3_rank]
                case x.p4_name:
                    l_data[l_name] += [x.p4_rank]
                case _:
                    l_data[l_name] += [None]

    # 規定打数以下を足切り
    if g.params["stipulated"]:
        for pname in list(l_data.keys()):
            if sum(x is not None for x in l_data[pname]) <= g.params["stipulated"]:
                l_data.pop(pname)

    rank_df = pd.DataFrame(
        l_data.values(),
        columns=list(df.index),
        index=list(l_data.keys())
    )

    # 対象リストが0件になった場合は空のデータフレームを返す
    if rank_df.empty:
        return (rank_df)

    # 対局対戦マトリックス表の作成
    mtx_df = pd.DataFrame(
        index=list(l_data.keys()),
        columns=list(l_data.keys()) + ["total"]
    )
    sorting_df = pd.DataFrame(
        index=list(l_data.keys()),
        columns=["win_per", "count"]
    )

    for idx1 in range(len(rank_df)):
        p1 = rank_df.iloc[idx1]
        t_game_count = 0
        t_win = 0
        for idx2 in range(len(rank_df)):
            p2 = rank_df.iloc[idx2]
            if p1.name == p2.name:
                mtx_df.loc[f"{p1.name}", f"{p2.name}"] = "---"
            else:
                game_count = len(pd.concat([p1, p2], axis=1).dropna())
                win = (p1 < p2).sum()
                t_game_count += game_count
                t_win += win

                if game_count:
                    winning_per = str(round(float(win / game_count * 100), 1))
                else:
                    winning_per = "--.-"
                mtx_df.loc[f"{p1.name}", f"{p2.name}"] = f"{win}-{game_count - win} ({winning_per}%)"

        if t_game_count:
            t_winning_per = str(round(float(t_win / t_game_count * 100), 1))
        else:
            t_winning_per = "--.-"
        mtx_df.loc[f"{p1.name}", "total"] = f"{t_win}-{t_game_count - t_win} ({t_winning_per}%)"
        sorting_df.loc[f"{p1.name}", "win_per"] = t_winning_per
        sorting_df.loc[f"{p1.name}", "count"] = t_game_count

    # 勝率で並び替え
    sorting_df["win_per"] = pd.to_numeric(sorting_df["win_per"], errors="coerce")
    sorting_df["count"] = pd.to_numeric(sorting_df["count"], errors="coerce")
    sorting_df = sorting_df.sort_values(by=["win_per", "count"], ascending=[False, False])
    mtx_df = mtx_df.reindex(
        index=list(sorting_df.index),
        columns=list(sorting_df.index) + ["total"]
    )

    return (mtx_df)
