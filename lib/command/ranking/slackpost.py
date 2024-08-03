import math

import pandas as pd

import lib.function as f
import lib.command as c
import lib.database as d
from lib.function import global_value as g


def main(client, channel, argument):
    """
    ランキングをslackにpostする

    Parameters
    ----------
    client : obj

    channel : str
        post先のチャンネルID or ユーザーID

    argument : list
        slackから受け取った引数
        解析対象のプレイヤー、検索範囲などが指定される
    """

    command_option = f.configure.command_option_initialization("ranking")
    _, _, _, command_option = f.common.argument_analysis(argument, command_option)

    g.logging.info(f"{argument=}")
    g.logging.info(f"{command_option=}")

    msg1, msg2 = aggregation(argument, command_option)
    res = f.slack_api.post_message(client, channel, msg1)
    if msg2:
        f.slack_api.post_multi_message(client, channel, msg2, res["ts"])


def aggregation(argument, command_option):
    """
    ランキングデータを生成

    Parameters
    ----------
    argument : list
        slackから受け取った引数

    command_option : dict
        コマンドオプション

    Returns
    -------
    msg1 : text
        ランキングの集計情報

    msg2 : dict
        各ランキングの情報
    """

    # --- データ取得
    params , game_info = f.common.game_info(argument, command_option)

    if params["game_count"] == 0: # 結果が0件のとき
        return(f.message.no_hits(params), None)

    if command_option["stipulated"] == 0: # 規定打数が指定されない場合はレートから計算
        command_option["stipulated"] = math.ceil(params["game_count"] * command_option["stipulated_rate"]) + 1

    result_df = d.aggregate.personal_results(argument, command_option)
    record_df = d.aggregate.personal_record(argument, command_option)
    result_df = pd.merge(result_df, record_df, on = ["プレイヤー名", "表示名"], suffixes = ["", "_x"])

    # --- 集計
    result_df["ゲーム参加率"] = result_df["ゲーム数"] / params["game_count"]
    result_df["総ゲーム数"] = params["game_count"]
    result_df["最大素点"] = result_df["最大素点"] * 100
    result_df.rename(columns = {"1位率": "トップ率"}, inplace = True)
    result_df = result_df.query("ゲーム数 >= @command_option['stipulated']")
    result_df = result_df.reset_index(drop = True)

    data = {
        # order: True -> 小さい値が上位 / False -> 大きい値が上位
        # threshold : 表示閾値
        "ゲーム参加率": {"order": False, "threshold": 0,
            "str": "{:>6.2%} ( {:3d} / {:4d} ゲーム )",
            "params": ["ゲーム参加率", "ゲーム数", "総ゲーム数"],
        },
        "通算ポイント": {"order": False, "threshold": -999999999,
            "str": "{:>7.1f} pt ( {:3d} ゲーム )",
            "params": ["通算ポイント", "ゲーム数"],
        },
        "平均ポイント": {"order": False, "threshold": -999999999,
            "str": "{:>5.1f} pt ( {:>7.1f} pt / {:3d} ゲーム )",
            "params": ["平均ポイント", "通算ポイント", "ゲーム数"],
        },
        "平均収支": {"order": False, "threshold": -999999999,
            "str": "{:>8.0f} 点 ( {:>5.0f} 点 / {:3d} ゲーム )",
            "params": ["平均収支", "平均最終素点", "ゲーム数"],
        },
        "トップ率": {"order": False, "threshold": 0,
            "str": "{:>3.2f}% ( {:3d} / {:3d} ゲーム )",
            "params": ["トップ率", "1位", "ゲーム数"],
        },
        "連対率": {"order": False, "threshold": 0,
            "str": "{:>3.2f}% ( {:3d} / {:3d} ゲーム )",
            "params": ["連対率", "連対", "ゲーム数"],
        },
        "ラス回避率": {"order": False, "threshold": 0,
            "str": "{:>3.2f}% ( {:3d} / {:3d} ゲーム )",
            "params": ["ラス回避率", "ラス回避", "ゲーム数"],
        },
        "トビ率": {"order": True, "threshold": 0,
            "str": "{:>3.2f}% ( {:3d} / {:3d} ゲーム )",
            "params": ["トビ率", "トビ","ゲーム数" ],
        },
        "平均順位": {"order": True, "threshold": 0,
            "str": "{:>4.2f} ( {:3d} ゲーム )",
            "params": ["平均順位", "ゲーム数"],
        },
        "役満和了率": {"order": False, "threshold": 1,
            "str": "{:>3.2}% ( {:3d} / {:3d} ゲーム )",
            "params": ["役満和了率", "役満和了", "ゲーム数"],
        },
        "最大素点": {"order": False, "threshold": -999999999,
            "str": "{:>5.0f} 点 ( {:>5.1f} pt )",
            "params": ["最大素点", "最大獲得ポイント"],
        },
        "連続トップ": {"order": False, "threshold": 2,
            "str": "{:>2d} 連続 ( {:>2d} ゲーム中 )",
            "params": ["連続トップ", "ゲーム数"],
        },
        "連続連対": {"order": False, "threshold": 2,
            "str": "{:>2d} 連続 ( {:>2d} ゲーム中 )",
            "params": ["連続連対", "ゲーム数"],
        },
        "連続ラス回避": {"order": False, "threshold": 2,
            "str": "{:>2d} 連続 ( {:>2d} ゲーム中 )",
            "params": ["連続ラス回避", "ゲーム数"],
        },
    }

    for k in data.keys(): # ランク付け
        result_df[f"{k}_rank"] = result_df[k].rank(
            method = "dense",
            ascending = data[k]["order"]
        )

    for x in ["連続トップ", "連続連対", "連続ラス回避"]: # 型変換
        result_df[x] = result_df[x].astype(int)

    # --- 表示
    msg1 = "\n*【ランキング】*\n"
    msg1 += f.message.header(game_info, command_option, params, "", 1)
    msg2 = {}

    for k in data.keys():
        msg2[k] = f"\n*{k}*\n"
        tmp_df = result_df.sort_values([f"{k}_rank", "ゲーム数"], ascending =[True, False])
        tmp_df = tmp_df.query(f"{k}_rank <= @command_option['ranked'] and {k} >= @data['{k}']['threshold']")

        for _, s in tmp_df.drop_duplicates(subset = "プレイヤー名").iterrows():
            msg2[k] += ("\t{:3d}： {}\t" + data[k]["str"] + "\n").format(
                int(s[f"{k}_rank"]), s["表示名"],
                *[s[x] for x in data[k]["params"]]
            ).replace("-", "▲")

        if msg2[k].strip().count("\n") == 0: # 対象者がいなければ項目を削除
            msg2.pop(k)

    return(msg1, msg2)
