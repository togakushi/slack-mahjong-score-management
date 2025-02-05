import logging
import sqlite3
from datetime import datetime

import numpy as np
import pandas as pd

import global_value as g
from lib import command as c
from lib import function as f
from lib.database import query


def _disp_name(df, adjust=0, mark=True):
    """ゲスト置換/パディング付与

    Args:
        df (pd.DataFrame): 変更対象のデータ
        adjust (int, optional): パディング数の調整. Defaults to 0.
        mark (bool, optional): ゲストマークの表示. Defaults to True.

    Returns:
        pd.DataFrame: 置換後のデータ
    """

    player_list = list(df.unique())

    replace_list = []
    for name in list(df.unique()):
        if g.opt.individual:
            replace_list.append(c.member.name_replace(name, add_mark=mark))
        else:
            replace_list.append(name)

    max_padding = c.member.count_padding(replace_list)
    for i in range(len(replace_list)):
        padding = " " * (
            max_padding - f.common.len_count(replace_list[i]) + adjust
        )
        replace_list[i] = f"{replace_list[i]}{padding}"

    return (df.replace(player_list, replace_list))


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
    df = pd.read_sql(
        query.game.info(),
        sqlite3.connect(g.cfg.db.database_file),
        params=g.prm.to_dict()
    )

    ret = {
        "game_count": int(df["count"].to_string(index=False)),
        "first_game": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        "last_game": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        "first_comment": None,
        "last_comment": None,
    }

    if ret["game_count"] >= 1:
        ret["first_game"] = df["first_game"].to_string(index=False).replace("-", "/")
        ret["last_game"] = df["last_game"].to_string(index=False).replace("-", "/")
        ret["first_comment"] = df["first_comment"].to_string(index=False)
        ret["last_comment"] = df["last_comment"].to_string(index=False)

    logging.info(f"return: {ret=}")
    return (ret)


def game_summary():
    """指定条件を満たすゲーム結果をサマライズする

    Returns:
        pd.DataFrame: 集計結果
    """

    # データ収集
    df = pd.read_sql(
        query.summary.total(),
        sqlite3.connect(g.cfg.db.database_file),
        params=g.prm.to_dict(),
    )

    # ゲスト置換
    if g.opt.individual:
        df["name"] = df["name"].apply(
            lambda x: c.member.name_replace(x, add_mark=True)
        )

    # ヘッダ修正
    df = df.rename(
        columns={
            "name": "プレイヤー名",
            "team": "チーム名",
            "count": "ゲーム数",
            "pt_total": "通算",
            "pt_avg": "平均",
            "pt_diff": "差分",
            "rank_distr": "順位分布",
            "rank_avg": "平順",
            "flying": "トビ",
            "1st": "1位",
            "2nd": "2位",
            "3rd": "3位",
            "4th": "4位",
        }
    )

    # インデックスの振り直し
    df = df.reset_index(drop=True)
    df.index = df.index + 1

    logging.trace(df)
    return (df.fillna(value="*****"))


def game_details():
    """ゲーム結果を集計する

    Returns:
        pd.DataFrame: 集計結果
    """

    # データ収集
    df = pd.read_sql(
        query.summary.details(),
        sqlite3.connect(g.cfg.db.database_file),
        params=g.prm.to_dict(),
    )

    # ゲスト置換
    if g.opt.individual:
        df["name"] = df["name"].apply(
            lambda x: c.member.name_replace(x, add_mark=True)
        )

    df["表示名"] = _disp_name(df["name"], mark=False)

    logging.trace(df)
    return (df.fillna(value=""))


def remark_count(kind):
    """メモの内容を種別でカウント

    Args:
        kind (str): 集計種別

    Returns:
        pd.DataFrame: 集計結果
    """

    # データ収集
    df = pd.read_sql(
        query.game.remark_count(kind),
        sqlite3.connect(g.cfg.db.database_file),
        params=g.prm.to_dict(),
    )

    # ゲスト置換
    df["プレイヤー名"] = df["name"].apply(
        lambda x: c.member.name_replace(x, add_mark=True)
    )

    if kind == "grandslam":
        df = df.filter(items=["プレイヤー名", "matter", "count"])

    logging.trace(df)
    return (df)


def game_results():
    """成績を集計する

    Returns:
        pd.DataFrame: 集計結果
    """

    # データ収集
    df = pd.read_sql(
        query.summary.results(),
        sqlite3.connect(g.cfg.db.database_file),
        params=g.prm.to_dict(),
    )

    # Nullが返ってきたときにobject型になるので型変換
    df = df.astype({
        "東家-平均順位": "float", "南家-平均順位": "float", "西家-平均順位": "float", "北家-平均順位": "float",
        "東家-役満和了": "Int64", "南家-役満和了": "Int64", "西家-役満和了": "Int64", "北家-役満和了": "Int64",
    }).fillna(0)

    # ゲスト置換
    df["表示名"] = _disp_name(df["name"])

    # インデックスの振り直し
    df = df.reset_index(drop=True)
    df.index = df.index + 1

    logging.trace(df)
    return (df)


def personal_gamedata():
    """ゲーム結果集計(個人用)

    Returns:
        pd.DataFrame: 集計結果
    """

    # データ収集
    df = pd.read_sql(
        query.summary.gamedata(),
        sqlite3.connect(g.cfg.db.database_file),
        params=g.prm.to_dict(),
    )

    # ゲスト置換
    df["プレイヤー名"] = df["name"].apply(
        lambda x: c.member.name_replace(x, add_mark=True)
    )

    return (df)


def versus_matrix():
    """直接対戦結果集計

    Returns:
        pd.DataFrame: 集計結果
    """

    # データ収集
    df = pd.read_sql(
        query.summary.versus_matrix(),
        sqlite3.connect(g.cfg.db.database_file),
        params=g.prm.to_dict(),
    )

    # ゲスト置換
    if g.opt.individual:
        df["my_name"] = df["my_name"].apply(
            lambda x: c.member.name_replace(x, add_mark=True)
        )
        df["vs_name"] = df["vs_name"].apply(
            lambda x: c.member.name_replace(x, add_mark=True)
        )

    df["my_表示名"] = _disp_name(df["my_name"])
    df["vs_表示名"] = _disp_name(df["vs_name"])

    return (df)


# チーム
def team_gamedata():
    """ゲーム結果集計(チーム用)

    Returns:
        pd.DataFrame: 集計結果
    """
    # データ収集
    df = pd.read_sql(
        query.summary.gamedata(),
        sqlite3.connect(g.cfg.db.database_file),
        params=g.prm.to_dict(),
    )

    return (df)


# ランキング
def ranking_record():
    """ランキング集計

    Returns:
        pd.DataFrame: 集計結果
    """

    # データ収集
    gamedata = pd.read_sql(
        query.ranking.record_count(),
        sqlite3.connect(g.cfg.db.database_file),
        params=g.prm.to_dict(),
    )

    # 連続順位カウント
    rank_mask = {
        "連続トップ": {1: 1, 2: 0, 3: 0, 4: 0},
        "連続連対": {1: 1, 2: 1, 3: 0, 4: 0},
        "連続ラス回避": {1: 1, 2: 1, 3: 1, 4: 0},
        "連続トップなし": {1: 0, 2: 1, 3: 1, 4: 1},
        "連続逆連対": {1: 0, 2: 0, 3: 1, 4: 1},
        "連続ラス": {1: 0, 2: 0, 3: 0, 4: 1},
    }

    for k in rank_mask.keys():
        gamedata[k] = None
        for pname in gamedata["name"].unique():
            tmp_df = pd.DataFrame()
            tmp_df["flg"] = gamedata.query(
                "name == @pname"
            )["順位"].replace(rank_mask[k])
            tmp_df[k] = tmp_df["flg"].groupby(
                (tmp_df["flg"] != tmp_df["flg"].shift()).cumsum()
            ).cumcount() + 1
            tmp_df.loc[tmp_df["flg"] == 0, k] = 0
            gamedata.update(tmp_df)

    # 最大値/最小値の格納
    df = pd.DataFrame()
    for pname in gamedata["name"].unique():
        tmp_df = gamedata.query(
            "name == @pname"
        ).max().to_frame().transpose()
        tmp_df.rename(
            columns={
                "最終素点": "最大素点",
                "獲得ポイント": "最大獲得ポイント",
            },
            inplace=True,
        )
        tmp_df["ゲーム数"] = len(gamedata.query("name == @pname"))
        tmp_df["最小素点"] = gamedata.query("name == @pname")["最終素点"].min()
        tmp_df["最小獲得ポイント"] = gamedata.query("name == @pname")["獲得ポイント"].min()
        df = pd.concat([df, tmp_df])

    # ゲスト置換
    df["表示名"] = _disp_name(df["name"])

    df = df.drop(columns=["playtime", "順位"])

    # インデックスの振り直し
    df = df.reset_index(drop=True)
    df.index = df.index + 1

    logging.trace(df)
    return (df)


def calculation_rating():
    """レーティング集計

    Returns:
        pd.DataFrame: 集計結果
    """

    # データ収集
    df_results = pd.read_sql(
        query.ranking.ratings(),
        sqlite3.connect(g.cfg.db.database_file),
        params=g.prm.to_dict(),
    ).set_index("playtime")

    df_ratings = pd.DataFrame(index=["initial_rating"] + df_results.index.to_list())  # 記録用
    last_ratings = {}  # 最終値格納用

    # 獲得スコア
    score_mapping = {1: 30, 2: 10, 3: -10, 4: -30}

    for x in df_results.itertuples():
        player_list = (x.p1_name, x.p2_name, x.p3_name, x.p4_name)
        for player in player_list:
            if player not in df_ratings.columns:
                last_ratings[player] = 1500
                df_ratings[player] = np.nan
                df_ratings.loc["initial_rating", player] = 1500
                df_ratings = df_ratings.copy()

        # 天鳳計算式 (https://tenhou.net/man/#RATING)
        rank_list = (x.p1_rank, x.p2_rank, x.p3_rank, x.p4_rank,)
        rating_list = [last_ratings[player] for player in player_list]
        rating_avg = 1500 if np.mean(rating_list) < 1500 else np.mean(rating_list)

        for i, player in enumerate(player_list):
            rating = rating_list[i]
            rank = rank_list[i]

            correction_value = (rating_avg - rating) / 40
            # correction_value = (sum([rate for j, rate in enumerate(rating_list) if j != i]) / 3 - rating) / 40
            if df_ratings[player].count() >= 400:
                match_correction = 0.2
            else:
                match_correction = 1 - df_ratings[player].count() * 0.002

            new_rating = rating + match_correction * (score_mapping[rank] + correction_value)

            last_ratings[player] = new_rating
            df_ratings.loc[x.Index, player] = new_rating

    return (df_ratings)


def simple_results():
    """ゲーム結果集計(簡易版)

    Returns:
        pd.DataFrame: 集計結果
    """

    # データ収集
    df = pd.read_sql(
        query.ranking.results(),
        sqlite3.connect(g.cfg.db.database_file),
        params=g.prm.to_dict(),
    ).set_index("name")

    return (df)


# レポート
def monthly_report():
    """レポート生成用データ集計

    Returns:
        pd.DataFrame: 集計結果
    """

    # データ収集
    df = pd.read_sql(
        query.report.monthly(),
        sqlite3.connect(g.cfg.db.database_file),
        params=g.prm.to_dict(),
    )

    return (df)


def winner_report():
    """成績上位者

    Returns:
        pd.DataFrame: 集計結果
    """

    # データ収集
    df = pd.read_sql(
        query.report.winner(),
        sqlite3.connect(g.cfg.db.database_file),
        params=g.prm.to_dict(),
    ).fillna(value=np.nan)

    # ゲスト置換
    for i in range(1, 6):
        df[f"pname{i}"] = df[f"name{i}"].apply(
            lambda x: "該当者なし" if type(x) is float else c.member.name_replace(x, add_mark=True)
        )

    return (df)


def matrix_table():
    """対局対戦マトリックス表の作成

    Returns:
        pd.DataFrame: 集計結果
    """

    # データ収集
    df = pd.read_sql(
        query.report.matrix_table(),
        sqlite3.connect(g.cfg.db.database_file),
        params=g.prm.to_dict()
    ).set_index("playtime")

    # 結果に含まれるプレイヤーのリスト
    plist = sorted(list(set(
        df["p1_name"].tolist() + df["p2_name"].tolist() + df["p3_name"].tolist() + df["p4_name"].tolist()
    )))

    # 順位テーブルの作成
    l_data = {}
    for pname in plist:
        if g.opt.individual:  # 個人集計
            l_name = c.member.name_replace(pname)
            # プレイヤー指定があるなら対象以外をスキップ
            if g.prm.player_list:
                if l_name not in g.prm.player_list.values():
                    continue
            # ゲスト置換
            if g.opt.guest_skip:  # ゲストあり
                l_name = c.member.name_replace(pname, add_mark=True)
            else:  # ゲストなし
                if pname == g.prm.guest_name:
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
    if g.prm.stipulated:
        for pname in list(l_data.keys()):
            if sum([x is not None for x in l_data[pname]]) <= g.prm.stipulated:
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
                    winning_per = round(float(win / game_count * 100), 1)
                else:
                    winning_per = "--.-"
                mtx_df.loc[f"{p1.name}", f"{p2.name}"] = f"{win}-{game_count - win} ({winning_per}%)"

        if t_game_count:
            t_winning_per = round(float(t_win / t_game_count * 100), 1)
        else:
            t_winning_per = "--.-"
        mtx_df.loc[f"{p1.name}", "total"] = f"{t_win}-{t_game_count - t_win} ({t_winning_per}%)"
        sorting_df.loc[f"{p1.name}", "win_per"] = t_winning_per
        sorting_df.loc[f"{p1.name}", "count"] = t_game_count

    # 勝率で並び替え
    sorting_df = sorting_df.sort_values(["win_per", "count"], ascending=False)
    mtx_df = mtx_df.reindex(
        index=list(sorting_df.index),
        columns=list(sorting_df.index) + ["total"]
    )

    return (mtx_df)


def results_list():
    """成績一覧表

    Returns:
        pd.DataFrame: 集計結果
    """

    # データ収集
    df = pd.read_sql(
        query.report.results_list(),
        sqlite3.connect(g.cfg.db.database_file),
        params=g.prm.to_dict(),
    )

    # ゲスト置換
    if g.opt.individual:
        df["name"] = df["name"].apply(
            lambda x: c.member.name_replace(x, add_mark=True)
        )

    # インデックスの振り直し
    df = df.reset_index(drop=True)
    df.index = df.index + 1

    logging.trace(df)
    return (df)
