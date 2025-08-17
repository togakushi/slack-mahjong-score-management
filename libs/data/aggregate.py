"""
lib/database/aggregate.py
"""

import logging

import numpy as np
import pandas as pd

import libs.global_value as g
from cls.timekit import ExtendedDatetime as ExtDt
from cls.types import GameInfoDict
from libs.data import loader
from libs.utils import formatter


def game_info() -> GameInfoDict:
    """指定条件を満たすゲーム数のカウント、最初と最後の時刻とコメントを取得

    Returns:
        GameInfoDict: 取得したデータ
    """

    # データ収集
    df = loader.read_data("game.info.sql")
    ret: GameInfoDict = {
        "game_count": int(df["count"].to_string(index=False)),
        "first_game": ExtDt(),
        "last_game": ExtDt(),
        "first_comment": None,
        "last_comment": None,
    }

    if ret.get("game_count", 0) >= 1:
        ret["first_game"] = ExtDt(df["first_game"].to_string(index=False))
        ret["last_game"] = ExtDt(df["last_game"].to_string(index=False))
        ret["first_comment"] = df["first_comment"].to_string(index=False)
        ret["last_comment"] = df["last_comment"].to_string(index=False)

    # 規定打数更新
    if not g.params.get("stipulated", 0):
        match g.params.get("command", ""):
            case "results":
                g.params["stipulated"] = g.cfg.results.stipulated_calculation(ret["game_count"])
            case "graph":
                g.params["stipulated"] = g.cfg.graph.stipulated_calculation(ret["game_count"])
            case "ranking":
                g.params["stipulated"] = g.cfg.ranking.stipulated_calculation(ret["game_count"])
            case "report":
                g.params["stipulated"] = g.cfg.report.stipulated_calculation(ret["game_count"])

    logging.info("return: %s", ret)
    return ret


def game_summary(filter_items: list | None = None, drop_items: list | None = None) -> "pd.DataFrame":
    """ゲーム結果をサマライズする

    Args:
        filter_items (list | None, optional): 抽出するカラム. Defaults to None.
        drop_items (list | None, optional): 除外するカラム. Defaults to None.

    Returns:
        pd.DataFrame: 集計結果
    """

    # データ収集
    df = loader.read_data("summary/total.sql")

    if isinstance(filter_items, list):
        df = df.filter(items=filter_items)

    if isinstance(drop_items, list):
        df = df.drop(columns=drop_items)

    logging.trace(df)  # type: ignore
    return df


def game_results() -> pd.DataFrame:
    """成績を集計する

    Returns:
        pd.DataFrame: 集計結果
    """

    # データ収集
    df = loader.read_data("summary/results.sql")

    # Nullが返ってきたときにobject型になるので型変換
    df = df.astype({
        "東家-平均順位": "float", "南家-平均順位": "float", "西家-平均順位": "float", "北家-平均順位": "float",
        "東家-役満和了": "Int64", "南家-役満和了": "Int64", "西家-役満和了": "Int64", "北家-役満和了": "Int64",
    }).fillna(0)

    # インデックスの振り直し
    df = df.reset_index(drop=True)
    df.index = df.index + 1

    logging.trace(df)  # type: ignore
    return df


# ランキング
def ranking_record() -> pd.DataFrame:
    """ランキング集計

    Returns:
        pd.DataFrame: 集計結果
    """

    # データ収集
    gamedata = loader.read_data("ranking/record_count.sql")
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
            "c_top": [0 for _ in player_list],
            "c_top2": [0 for _ in player_list],
            "c_top3": [0 for _ in player_list],
            "c_low": [0 for _ in player_list],
            "c_low2": [0 for _ in player_list],
            "c_low4": [0 for _ in player_list],
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
            max_key = key.replace("c_", "max_")
            record_df.at[pname, max_key] = int(tmp_df[[key]].max().values[0])

            # 最終値
            record_df.at[pname, key] = tmp_df[key].iloc[-1]
            record_df[max_key] = record_df[max_key].fillna(0).copy().astype("int")

    # 最大値/最小値追加
    if not gamedata.empty:
        record_df["point_max"] = gamedata["point_max"].iloc[0]
        record_df["point_min"] = gamedata["point_min"].iloc[0]
        record_df["rpoint_max"] = gamedata["rpoint_max"].iloc[0]
        record_df["rpoint_min"] = gamedata["rpoint_min"].iloc[0]

    logging.trace(record_df)  # type: ignore
    return record_df


def calculation_rating() -> pd.DataFrame:
    """レーティング集計

    Returns:
        pd.DataFrame: 集計結果
    """

    # データ収集
    df_results = loader.read_data("ranking/ratings.sql").set_index("playtime")
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

    return df_ratings


def grade_promotion_check(grade_level: int, point: int, rank: int) -> tuple[int, int]:
    """昇段チェック

    Args:
        grade_level (int): 現在のレベル(段位)
        point (int): 現在の昇段ポイント
        rank (int): 獲得順位

    Returns:
        tuple[int, int]: チェック後の昇段ポイント, チェック後のレベル(段位)
    """

    tbl_data = g.cfg.badge.grade.table["table"]
    new_point = point + int(tbl_data[grade_level]["acquisition"][rank - 1])

    if new_point >= int(tbl_data[grade_level]["point"][1]):  # level up
        grade_level = min(grade_level + 1, len(tbl_data) - 1)
        new_point = int(tbl_data[grade_level]["point"][0])  # 初期値
    elif new_point < 0:  # level down
        new_point = int(0)
        if tbl_data[grade_level]["demote"]:
            grade_level = max(grade_level - 1, 0)
            new_point = int(tbl_data[grade_level]["point"][0])  # 初期値

    return (new_point, grade_level)


# レポート
def matrix_table() -> pd.DataFrame:
    """対局対戦マトリックス表の作成

    Returns:
        pd.DataFrame: 集計結果
    """

    # データ収集
    df = loader.read_data("report/matrix_table.sql").set_index("playtime")

    # 結果に含まれるプレイヤーのリスト
    plist = sorted(list(set(
        df["p1_name"].tolist() + df["p2_name"].tolist() + df["p3_name"].tolist() + df["p4_name"].tolist()
    )))

    # 順位テーブルの作成
    l_data: dict = {}
    for pname in plist:
        if g.params.get("individual"):  # 個人集計
            l_name = formatter.name_replace(pname)
            # プレイヤー指定があるなら対象以外をスキップ
            if g.params["player_list"]:
                if l_name not in g.params["player_list"].values():
                    continue
            # ゲスト置換
            if g.params.get("guest_skip"):  # ゲストあり
                l_name = formatter.name_replace(pname, add_mark=True)
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
        return rank_df

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

    return mtx_df
