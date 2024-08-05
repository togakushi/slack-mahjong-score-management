import sqlite3
from datetime import datetime

import pandas as pd
import numpy as np

import lib.function as f
import lib.command as c
import lib.database as d
from lib.function import global_value as g


def _disp_name(df, command_option, adjust = 0):
    """
    ゲスト置換/パディング付与

    Parameters
    ----------
    df : DataFrame
        変更対象のデータ

    command_option : dict
        コマンドオプション

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
            c.member.NameReplace(name, command_option, add_mark = True)
        )

    max_padding = c.member.CountPadding(replace_list)
    for i in range(len(replace_list)):
        padding = " " * (max_padding - f.common.len_count(replace_list[i]) + adjust)
        replace_list[i] = f"{replace_list[i]}{padding}"

    return(df.replace(player_list, replace_list))


def _extending(params = {}):
    """
    入れ子になった辞書の展開
    """

    for k in list(params.keys()):
        if type(params[k]) == dict:
            tmp_dict = params.pop(k)
            params.update(tmp_dict)

    return(params)


def game_info(argument, command_option):
    """
    指定条件を満たすゲーム数のカウント、最初と最後の時刻とコメントを取得

    Parameters
    ----------
    argument : list
        slackから受け取った引数

    command_option : dict
        コマンドオプション

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
        d.generate.game_info(argument, command_option),
        sqlite3.connect(g.database_file),
        params = _extending(f.configure.get_parameters(argument, command_option))
    )

    ret = {
        "game_count": int(df["count"].to_string(index = False)),
        "first_game": datetime.now(),
        "last_game": datetime.now(),
        "first_comment": None,
        "last_comment": None,
    }

    if ret["game_count"] >= 1:
        ret["first_game"] = datetime.fromisoformat(df["first_game"].to_string(index = False))
        ret["last_game"] = datetime.fromisoformat(df["last_game"].to_string(index = False))
        ret["first_comment"] = df["first_comment"].to_string(index = False)
        ret["last_comment"] = df["last_comment"].to_string(index = False)

    g.logging.info(f"return: {ret=}")
    return(ret)


def game_summary(argument, command_option):
    """
    指定条件を満たすゲーム結果をサマライズする

    Parameters
    ----------
    argument : list
        slackから受け取った引数

    command_option : dict
        コマンドオプション

    Returns
    -------
    df : DataFrame
    """

    # データ収集
    df = pd.read_sql(
        d.generate.game_results(argument, command_option),
        sqlite3.connect(g.database_file),
        params = _extending(f.configure.get_parameters(argument, command_option))
    )

    # ヘッダ修正
    df = df.rename(
        columns = {
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
        lambda x: c.member.NameReplace(x, command_option, add_mark = True)
    )

    # インデックスの振り直し
    df = df.reset_index(drop = True)
    df.index = df.index + 1

    return(df.fillna(value = "*****"))


def game_details(argument, command_option):
    """
    ゲーム結果を集計する

    Parameters
    ----------
    argument : list
        slackから受け取った引数

    command_option : dict
        コマンドオプション

    Returns
    -------
    df : DataFrame
    """

    df = pd.read_sql(
        d.generate.game_details(argument, command_option),
        sqlite3.connect(g.database_file),
        params = _extending(f.configure.get_parameters(argument, command_option))
    )

    # ゲスト置換
    df["表示名"] = _disp_name(df["プレイヤー名"], command_option)

    return(df.fillna(value = ""))


def game_data(argument, command_option):
    """
    ゲーム結果を返す

    Parameters
    ----------
    argument : list
        slackから受け取った引数

    command_option : dict
        コマンドオプション

    Returns
    -------
    df : DataFrame
    """

    df = pd.read_sql(
        d.generate.game_data(argument, command_option),
        sqlite3.connect(g.database_file),
        params = _extending(f.configure.get_parameters(argument, command_option))
    )

    # ゲスト置換
    df["p1_name"] = _disp_name(df["p1_name"], command_option)
    df["p2_name"] = _disp_name(df["p2_name"], command_option)
    df["p3_name"] = _disp_name(df["p3_name"], command_option)
    df["p4_name"] = _disp_name(df["p4_name"], command_option)

    # インデックスの振り直し
    df = df.reset_index(drop = True)
    df.index = df.index + 1

    return(df.fillna(value = ""))


def personal_record(argument, command_option):
    """
    個人記録を集計する

    Parameters
    ----------
    argument : list
        slackから受け取った引数

    command_option : dict
        コマンドオプション

    Returns
    -------
    df : DataFrame
    """

    # データ収集
    gamedata = pd.read_sql(
        d.generate.record_count(argument, command_option),
        sqlite3.connect(g.database_file),
        params = _extending(f.configure.get_parameters(argument, command_option))
    )

    # 連続順位カウント
    rank_mask = {
        "連続トップ":     {1: 1, 2: 0, 3: 0, 4: 0},
        "連続連対":       {1: 1, 2: 1, 3: 0, 4: 0},
        "連続ラス回避":   {1: 1, 2: 1, 3: 1, 4: 0},
        "連続トップなし": {1: 0, 2: 1, 3: 1, 4: 1},
        "連続逆連対":     {1: 0, 2: 0, 3: 1, 4: 1},
        "連続ラス":       {1: 0, 2: 0, 3: 0, 4: 1},
    }

    for k in rank_mask.keys():
        gamedata[k] = None
        for pname in gamedata["プレイヤー名"].unique():
            tmp_df = pd.DataFrame()
            tmp_df["flg"] = gamedata.query("プレイヤー名 == @pname")["順位"].replace(rank_mask[k])
            tmp_df[k] = tmp_df["flg"].groupby((tmp_df["flg"] != tmp_df["flg"].shift()).cumsum()).cumcount() + 1
            tmp_df.loc[tmp_df["flg"] == 0, k] = 0
            gamedata.update(tmp_df)

    # 最大値/最小値の格納
    df = pd.DataFrame()
    for pname in gamedata["プレイヤー名"].unique():
        tmp_df = gamedata.query("プレイヤー名 == @pname").max().to_frame().transpose()
        tmp_df.rename(
            columns = {
                "最終素点": "最大素点",
                "獲得ポイント": "最大獲得ポイント",
            },
            inplace = True,
        )
        tmp_df["ゲーム数"] = len(gamedata.query("プレイヤー名 == @pname"))
        tmp_df["最小素点"] = gamedata.query("プレイヤー名 == @pname")["最終素点"].min()
        tmp_df["最小獲得ポイント"] = gamedata.query("プレイヤー名 == @pname")["獲得ポイント"].min()
        df = pd.concat([df, tmp_df])

    # ゲスト置換
    df["表示名"] = _disp_name(df["プレイヤー名"], command_option)

    df = df.drop(columns = ["playtime", "順位"])
 
    # インデックスの振り直し
    df = df.reset_index(drop = True)
    df.index = df.index + 1

    return(df)


def personal_results(argument, command_option):
    """
    個人成績を集計する

    Parameters
    ----------
    argument : list
        slackから受け取った引数

    command_option : dict
        コマンドオプション

    Returns
    -------
    df : DataFrame
    """

    # データ収集
    df = pd.read_sql(
        d.generate.personal_results(argument, command_option),
        sqlite3.connect(g.database_file),
        params = _extending(f.configure.get_parameters(argument, command_option))
    )

    # Nullが返ってきたときにobject型になるのでfloat型に変換
    df["東家-平均順位"] = df["東家-平均順位"].astype(float)
    df["南家-平均順位"] = df["南家-平均順位"].astype(float)
    df["西家-平均順位"] = df["西家-平均順位"].astype(float)
    df["北家-平均順位"] = df["北家-平均順位"].astype(float)
    df = df.fillna(0)

    # ゲスト置換
    df["表示名"] = _disp_name(df["プレイヤー名"], command_option)

    # インデックスの振り直し
    df = df.reset_index(drop = True)
    df.index = df.index + 1

    return(df)


def versus_matrix(argument, command_option):
    # データ収集
    df = pd.read_sql(
        d.generate.versus_matrix(argument, command_option),
        sqlite3.connect(g.database_file),
        params = _extending(f.configure.get_parameters(argument, command_option))
    )

    # ゲスト置換
    df["my_表示名"] = _disp_name(df["my_name"], command_option)
    df["vs_表示名"] = _disp_name(df["vs_name"], command_option)

    return(df)


def personal_gamedata(argument, command_option):
    # データ収集
    if command_option["daily"]:
        df = pd.read_sql(
            d.generate.personal_gamedata_daily(argument, command_option),
            sqlite3.connect(g.database_file),
            params = _extending(f.configure.get_parameters(argument, command_option))
        )
    else:
        df = pd.read_sql(
            d.generate.personal_gamedata(argument, command_option),
            sqlite3.connect(g.database_file),
            params = _extending(f.configure.get_parameters(argument, command_option))
        )

    # ゲスト置換
    df["プレイヤー名"] = df["name"].apply(
        lambda x: c.member.NameReplace(x, command_option, add_mark = True)
    )

    return(df)


def team_gamedata(argument, command_option):
    # データ収集
    if command_option["daily"]:
        df = pd.read_sql(
            d.generate.team_gamedata_daily(argument, command_option),
            sqlite3.connect(g.database_file),
            params = _extending(f.configure.get_parameters(argument, command_option))
        )
    else:
        df = pd.read_sql(
            d.generate.team_gamedata(argument, command_option),
            sqlite3.connect(g.database_file),
            params = _extending(f.configure.get_parameters(argument, command_option))
        )

    return(df)


def monthly_report(argument, command_option):
    # データ収集
    df = pd.read_sql(
        d.generate.monthly_report(argument, command_option),
        sqlite3.connect(g.database_file),
        params = _extending(f.configure.get_parameters(argument, command_option))
    )

    return(df)


def winner_report(argument, command_option):
    # データ収集
    df = pd.read_sql(
        d.generate.winner_report(argument, command_option),
        sqlite3.connect(g.database_file),
        params = _extending(f.configure.get_parameters(argument, command_option))
    ).fillna(value=np.nan)

    # ゲスト置換
    for i in range(1,6):
        df[f"pname{i}"] = df[f"name{i}"].apply(
            lambda x: "該当者なし" if type(x) == float else c.member.NameReplace(x, command_option, add_mark = True)
        )

    return(df)


def team_total(argument, command_option):
    """
    チーム集計

    Parameters
    ----------
    argument : list
        slackから受け取った引数

    command_option : dict
        コマンドオプション

    Returns
    -------
    df : DataFrame
    """

    # データ収集
    df = pd.read_sql(
        d.generate.team_total(argument, command_option),
        sqlite3.connect(g.database_file),
        params = _extending(f.configure.get_parameters(argument, command_option))
    )
    #if command_option["daily"]:
    #    df = pd.read_sql(
    #        d.generate.team_total_daily(argument, command_option),
    #        sqlite3.connect(g.database_file),
    #        params = _extending(f.configure.get_parameters(argument, command_option))
    #    )
    #else:
    #    df = pd.read_sql(
    #        d.generate.team_total(argument, command_option),
    #        sqlite3.connect(g.database_file),
    #        params = _extending(f.configure.get_parameters(argument, command_option))
    #    )

    # インデックスの振り直し
    df = df.reset_index(drop = True)
    df.index = df.index + 1

    return(df)
