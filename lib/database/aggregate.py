import sqlite3
from datetime import datetime

import numpy as np
import pandas as pd

import lib.command as c
import lib.database as d
import lib.function as f
from lib.function import global_value as g


def _disp_name(df, adjust=0):
    """
    ゲスト置換/パディング付与

    Parameters
    ----------
    df : DataFrame
        変更対象のデータ

    adjust : int
        パディング数の調整

    Returns
    -------
    df : DataFrame
        置換後のデータ
    """

    player_list = list(df.unique())

    replace_list = []
    for name in list(df.unique()):
        replace_list.append(
            c.member.NameReplace(name, add_mark=True)
        )

    max_padding = c.member.CountPadding(replace_list)
    for i in range(len(replace_list)):
        padding = " " * (
            max_padding - f.common.len_count(replace_list[i]) + adjust
        )
        replace_list[i] = f"{replace_list[i]}{padding}"

    return (df.replace(player_list, replace_list))


def _guest_filter(df: pd.DataFrame):
    if g.opt.unregistered_replace:
        if g.opt.guest_skip:  # ゲストあり(2ゲスト戦除外)
            df = df.query("guest_count <= 2")
        else:  # ゲストなし(ゲスト除外)
            df = df.query("guest == 0")

    return (df)


def game_info():
    """
    指定条件を満たすゲーム数のカウント、最初と最後の時刻とコメントを取得

    Returns
    -------
    ret : dict
        game_count : int
        first_game : datetime
        last_game : datetime
        first_comment : str
        last_comment : str
    """

    # データ収集
    df = pd.read_sql(
        d.generate.game_info(),
        sqlite3.connect(g.database_file),
        params=g.prm.to_dict()
    )

    ret = {
        "game_count": int(df["count"].to_string(index=False)),
        "first_game": datetime.now(),
        "last_game": datetime.now(),
        "first_comment": None,
        "last_comment": None,
    }

    if ret["game_count"] >= 1:
        ret["first_game"] = datetime.fromisoformat(
            df["first_game"].to_string(index=False)
        )
        ret["last_game"] = datetime.fromisoformat(
            df["last_game"].to_string(index=False)
        )
        ret["first_comment"] = df["first_comment"].to_string(index=False)
        ret["last_comment"] = df["last_comment"].to_string(index=False)

    g.logging.info(f"return: {ret=}")
    return (ret)


def game_summary():
    """
    指定条件を満たすゲーム結果をサマライズする

    Returns
    -------
    df : DataFrame
    """

    # データ収集
    df = pd.read_sql(
        d.generate.game_results(),
        sqlite3.connect(g.database_file),
        params=g.prm.to_dict(),
    )

    # ヘッダ修正
    df = df.rename(
        columns={
            "count": "ゲーム数",
            "pt_total": "通算",
            "pt_avg": "平均",
            "rank_distr": "順位分布",
            "rank_avg": "平順",
            "flying": "トビ",
            "1st": "1位",
            "2nd": "2位",
            "3rd": "3位",
            "4th": "4位",
        }
    )

    # 点数差分
    df["点差"] = df["通算"].diff().abs().round(2)

    # ゲスト置換
    df["プレイヤー名"] = df["name"].apply(
        lambda x: c.member.NameReplace(x, add_mark=True)
    )

    # インデックスの振り直し
    df = df.reset_index(drop=True)
    df.index = df.index + 1

    return (df.fillna(value="*****"))


def game_details():
    """
    ゲーム結果を集計する

    Returns
    -------
    df : DataFrame
    """

    df = pd.read_sql(
        d.generate.game_details(),
        sqlite3.connect(g.database_file),
        params=g.prm.to_dict(),
    )

    # ゲスト置換
    df["表示名"] = _disp_name(df["プレイヤー名"])

    return (df.fillna(value=""))


def personal_record():
    """
    個人記録を集計する

    Returns
    -------
    df : DataFrame
    """

    # データ収集
    gamedata = pd.read_sql(
        d.generate.record_count(),
        sqlite3.connect(g.database_file),
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
        for pname in gamedata["プレイヤー名"].unique():
            tmp_df = pd.DataFrame()
            tmp_df["flg"] = gamedata.query(
                "プレイヤー名 == @pname"
            )["順位"].replace(rank_mask[k])
            tmp_df[k] = tmp_df["flg"].groupby(
                (tmp_df["flg"] != tmp_df["flg"].shift()).cumsum()
            ).cumcount() + 1
            tmp_df.loc[tmp_df["flg"] == 0, k] = 0
            gamedata.update(tmp_df)

    # 最大値/最小値の格納
    df = pd.DataFrame()
    for pname in gamedata["プレイヤー名"].unique():
        tmp_df = gamedata.query(
            "プレイヤー名 == @pname"
        ).max().to_frame().transpose()
        tmp_df.rename(
            columns={
                "最終素点": "最大素点",
                "獲得ポイント": "最大獲得ポイント",
            },
            inplace=True,
        )
        tmp_df["ゲーム数"] = len(gamedata.query("プレイヤー名 == @pname"))
        tmp_df["最小素点"] = gamedata.query("プレイヤー名 == @pname")["最終素点"].min()
        tmp_df["最小獲得ポイント"] = gamedata.query("プレイヤー名 == @pname")["獲得ポイント"].min()
        df = pd.concat([df, tmp_df])

    # ゲスト置換
    df["表示名"] = _disp_name(df["プレイヤー名"])

    df = df.drop(columns=["playtime", "順位"])

    # インデックスの振り直し
    df = df.reset_index(drop=True)
    df.index = df.index + 1

    return (df)


def personal_results():
    """
    個人成績を集計する

    Returns
    -------
    df : DataFrame
    """

    # データ収集
    df = pd.read_sql(
        d.generate.personal_results(),
        sqlite3.connect(g.database_file),
        params=g.prm.to_dict(),
    )

    # Nullが返ってきたときにobject型になるので型変換
    df = df.astype({
        "東家-平均順位": "float", "南家-平均順位": "float", "西家-平均順位": "float", "北家-平均順位": "float",
        "東家-役満和了": "Int64", "南家-役満和了": "Int64", "西家-役満和了": "Int64", "北家-役満和了": "Int64",
    }).fillna(0)

    # ゲスト置換
    df["表示名"] = _disp_name(df["プレイヤー名"])

    # インデックスの振り直し
    df = df.reset_index(drop=True)
    df.index = df.index + 1

    return (df)


def versus_matrix():
    # データ収集
    df = pd.read_sql(
        d.generate.versus_matrix(),
        sqlite3.connect(g.database_file),
        params=g.prm.to_dict(),
    )

    # ゲスト置換
    df["my_表示名"] = _disp_name(df["my_name"])
    df["vs_表示名"] = _disp_name(df["vs_name"])

    return (df)


def personal_gamedata():
    # データ収集
    df = pd.read_sql(
        d.generate.personal_gamedata(),
        sqlite3.connect(g.database_file),
        params=g.prm.to_dict(),
    )

    # ゲスト置換
    df["プレイヤー名"] = df["name"].apply(
        lambda x: c.member.NameReplace(x, add_mark=True)
    )

    return (df)


def team_gamedata():
    # データ収集
    df = pd.read_sql(
        d.generate.team_gamedata(),
        sqlite3.connect(g.database_file),
        params=g.prm.to_dict(),
    )

    return (df)


def monthly_report():
    # データ収集
    df = pd.read_sql(
        d.generate.monthly_report(),
        sqlite3.connect(g.database_file),
        params=g.prm.to_dict(),
    )

    return (df)


def winner_report():
    # データ収集
    df = pd.read_sql(
        d.generate.winner_report(),
        sqlite3.connect(g.database_file),
        params=g.prm.to_dict(),
    ).fillna(value=np.nan)

    # ゲスト置換
    for i in range(1, 6):
        df[f"pname{i}"] = df[f"name{i}"].apply(
            lambda x: "該当者なし" if type(x) is float else c.member.NameReplace(x, add_mark=True)
        )

    return (df)


def team_total():
    """
    チーム集計

    Returns
    -------
    df : DataFrame
    """

    # データ収集
    df = pd.read_sql(
        d.generate.team_total(),
        sqlite3.connect(g.database_file),
        params=g.prm.to_dict(),
    )

    # インデックスの振り直し
    df = df.reset_index(drop=True)
    df.index = df.index + 1

    return (df)


def grandslam_count():
    # データ収集
    df = pd.read_sql(
        d.generate.remark_count(),
        sqlite3.connect(g.database_file),
        params=g.prm.to_dict(),
    ).query("type != type or type == 0")

    # ゲスト置換
    df["プレイヤー名"] = df["name"].apply(
        lambda x: c.member.NameReplace(x, add_mark=True)
    )

    df = df.filter(items=["プレイヤー名", "matter", "count"])

    return (df)


def regulations_count():
    # データ収集
    df = pd.read_sql(
        d.generate.remark_count(),
        sqlite3.connect(g.database_file),
        params=g.prm.to_dict(),
    ).query("type == 1")

    # ゲスト置換
    df["プレイヤー名"] = df["name"].apply(
        lambda x: c.member.NameReplace(x, add_mark=True)
    )

    df = df.filter(items=["プレイヤー名", "matter", "count", "ex_point"])

    return (df)


def matrix_table():
    """
    対局対戦マトリックス表の作成
    """

    # データ収集
    df = pd.read_sql(
        d.generate.matrix_table(),
        sqlite3.connect(g.database_file),
        params=g.prm.to_dict()
    ).set_index("playtime")

    # 結果に含まれるプレイヤーのリスト
    plist = sorted(list(set(
        df["p1_name"].tolist() + df["p2_name"].tolist() + df["p3_name"].tolist() + df["p4_name"].tolist()
    )))

    # 順位テーブルの作成
    l_data = {}
    for pname in plist:
        l_name = c.member.NameReplace(pname)

        # プレイヤー指定があるなら対象以外をスキップ
        if g.prm.player_list:
            if l_name not in g.prm.player_list.values():
                continue

        # ゲスト置換
        if g.opt.guest_skip:  # ゲストあり
            l_name = c.member.NameReplace(pname, add_mark=True)
        else:  # ゲストなし
            if pname == g.prm.guest_name:
                continue

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

    return (mtx_df)
