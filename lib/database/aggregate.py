import sqlite3
from datetime import datetime

import pandas as pd

import lib.command as c
import lib.database as d
from lib.function import global_value as g


def game_count(argument, command_option):
    """
    指定条件を満たすゲーム数をカウントする

    Parameters
    ----------
    argument : list
        slackから受け取った引数

    command_option : dict
        コマンドオプション

    Returns
    -------
    count : int
    first : datetime
    last : datetime
    """

    # データ収集
    df = pd.read_sql(
        d.generate.game_count(argument, command_option),
        sqlite3.connect(g.database_file),
        params = d.common.placeholder_params(argument, command_option)
    )

    count = int(df["count"].to_string(index = False))
    first = datetime.now()
    last = datetime.now()

    if count >= 1:
        first = datetime.fromisoformat(df["first_game"].to_string(index = False))
        last = datetime.fromisoformat(df["last_game"].to_string(index = False))

    g.logging.info(f"return: count: {count}, first: {first}, last: {last}")
    return(count, first, last)


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
        params = d.common.placeholder_params(argument, command_option)
    )

    #点数差分
    df["pt_diff"] = df["pt_total"].diff().abs()

    # ゲスト置換
    if not command_option["unregistered_replace"]:
        player_name = df["name"].map(lambda x:
            c.member.NameReplace(x, command_option, add_mark = True)
        )
        player_name = player_name.rename("name")
        df.update(player_name)

    # インデックスの振り直し
    df = df.reset_index(drop = True)
    df.index = df.index + 1

    return(df)


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
        params = d.common.placeholder_params(argument, command_option),
    )

    # ゲスト置換
    for i in ("p1_name", "p2_name", "p3_name", "p4_name"):
        player_name = df[i].map(lambda x:
            c.member.NameReplace(x, command_option, add_mark = True)
        )
        player_name = player_name.rename(i)
        df.update(player_name)

    return(df)


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
        params = d.common.placeholder_params(argument, command_option)
    )

    # 連続順位カウント
    rank_mask = {
        "連続トップ":     {1: 0, 2: 1, 3: 1, 4: 1},
        "連続連対":       {1: 0, 2: 0, 3: 1, 4: 1},
        "連続ラス回避":   {1: 0, 2: 0, 3: 0, 4: 1},
        "連続トップなし": {1: 1, 2: 0, 3: 0, 4: 0},
        "連続逆連対":     {1: 1, 2: 1, 3: 0, 4: 0},
        "連続ラス":       {1: 1, 2: 1, 3: 1, 4: 0},
    }

    for k in rank_mask.keys():
        gamedata[k] = 0
        for pname in gamedata["プレイヤー名"].unique():
            tmp_df = gamedata.query("プレイヤー名 == @pname")["順位"].replace(rank_mask[k])
            tmp_df = tmp_df.groupby(tmp_df.cumsum()).cumcount()
            tmp_df = tmp_df.rename(k)
            gamedata.update(tmp_df)

    # 最大値/最小値の格納
    df = pd.DataFrame()
    for pname in gamedata["プレイヤー名"].unique():
        tmp_df = gamedata.query("プレイヤー名 == @pname").max().to_frame().transpose()
        tmp_df.rename(
            columns = {
                "最終素点": "最大素点",
                "獲得ポイント": "最大獲得ポイント",
                "playtime": "最終ゲーム時間",
            },
            inplace = True,
        )
        tmp_df["最小素点"] = gamedata.query("プレイヤー名 == @pname")["最終素点"].min()
        tmp_df["最小獲得ポイント"] = gamedata.query("プレイヤー名 == @pname")["獲得ポイント"].min()
        df = pd.concat([df, tmp_df])

    # ゲスト置換
    if not command_option["unregistered_replace"]:
        player_name = df["プレイヤー名"].map(lambda x:
            c.member.NameReplace(x, command_option, add_mark = True)
        )
        player_name = player_name.rename("プレイヤー名")
        df.update(player_name)

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
        params = d.common.placeholder_params(argument, command_option)
    )

    # ゲスト置換
    if not command_option["unregistered_replace"]:
        player_name = df["プレイヤー名"].map(lambda x:
            c.member.NameReplace(x, command_option, add_mark = True)
        )
        player_name = player_name.rename("プレイヤー名")
        df.update(player_name)

    # インデックスの振り直し
    df = df.reset_index(drop = True)
    df.index = df.index + 1

    return(df)
