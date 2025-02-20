import math

import pandas as pd

import lib.global_value as g
from lib import database as d
from lib import function as f


def main():
    """ランキングをslackにpostする
    """

    g.opt.initialization("ranking", g.msg.argument)
    g.prm.update(g.opt)

    msg1, msg2 = aggregation()
    res = f.slack_api.post_message(msg1)
    if msg2:
        f.slack_api.post_multi_message(msg2, res["ts"])


def aggregation():
    """ランキングデータを生成

    Returns:
        Tuple[str, dict]:
            - str: ランキングの集計情報
            - dict: 各ランキングの情報
    """

    # --- データ取得
    game_info = d.aggregate.game_info()

    if game_info["game_count"] == 0:  # 結果が0件のとき
        return (f.message.reply(message="no_hits"), None)

    if g.opt.stipulated == 0:  # 規定打数が指定されない場合はレートから計算
        g.opt.stipulated = (
            math.ceil(game_info["game_count"] * g.opt.stipulated_rate) + 1
        )
        g.prm.update(g.opt)

    result_df = d.aggregate.game_results()
    record_df = d.aggregate.ranking_record()
    result_df = pd.merge(
        result_df, record_df,
        on=["name", "name"],
        suffixes=["", "_x"]
    )

    # --- 集計
    result_df["ゲーム参加率"] = result_df["ゲーム数"] / game_info["game_count"]
    result_df["総ゲーム数"] = game_info["game_count"]
    result_df["最大素点"] = result_df["最大素点"] * 100
    result_df.rename(columns={"1位率": "トップ率"}, inplace=True)
    result_df = result_df.query("ゲーム数 >= @g.opt.stipulated")
    result_df = result_df.reset_index(drop=True)

    data = {
        # order: True -> 小さい値が上位 / False -> 大きい値が上位
        # column : 閾値対象のカラム名
        # threshold : 表示閾値
        # str: 表示文字列
        # params: 表示内容
        "ゲーム参加率": {
            "order": False, "column": "ゲーム数", "threshold": 0,  # 足切り済み
            "str": "{:>6.2%} ( {:3d} / {:4d} ゲーム )",
            "params": ["ゲーム参加率", "ゲーム数", "総ゲーム数"],
        },
        "通算ポイント": {
            "order": False, "column": "通算ポイント", "threshold": -999999999,
            "str": "{:>7.1f} pt ( {:3d} ゲーム )",
            "params": ["通算ポイント", "ゲーム数"],
        },
        "平均ポイント": {
            "order": False, "column": "平均ポイント", "threshold": -999999999,
            "str": "{:>5.1f} pt ( {:>7.1f} pt / {:3d} ゲーム )",
            "params": ["平均ポイント", "通算ポイント", "ゲーム数"],
        },
        "平均収支": {
            "order": False, "column": "平均収支", "threshold": -999999999,
            "str": "{:>8.0f} 点 ( {:>5.0f} 点 / {:3d} ゲーム )",
            "params": ["平均収支", "平均最終素点", "ゲーム数"],
        },
        "トップ率": {
            "order": False, "column": "トップ率", "threshold": 0,
            "str": "{:>5.2f}% ( {:3d} / {:3d} ゲーム )",
            "params": ["トップ率", "1位", "ゲーム数"],
        },
        "連対率": {
            "order": False, "column": "連対率", "threshold": 0,
            "str": "{:>5.2f}% ( {:3d} / {:3d} ゲーム )",
            "params": ["連対率", "連対", "ゲーム数"],
        },
        "ラス回避率": {
            "order": False, "column": "ラス回避率", "threshold": 0,
            "str": "{:>5.2f}% ( {:3d} / {:3d} ゲーム )",
            "params": ["ラス回避率", "ラス回避", "ゲーム数"],
        },
        "トビ率": {
            "order": True, "column": "トビ率", "threshold": 0,
            "str": "{:>5.2f}% ( {:3d} / {:3d} ゲーム )",
            "params": ["トビ率", "トビ", "ゲーム数"],
        },
        "平均順位": {
            "order": True, "column": "平均順位", "threshold": 0,
            "str": "{:>4.2f} ( {:3d} ゲーム )",
            "params": ["平均順位", "ゲーム数"],
        },
        "役満和了率": {
            "order": False, "column": "役満和了", "threshold": 1,
            "str": "{:>3.2f}% ( {:3d} / {:3d} ゲーム )",
            "params": ["役満和了率", "役満和了", "ゲーム数"],
        },
        "最大素点": {
            "order": False, "column": "最大素点", "threshold": -999999999,
            "str": "{:>6.0f} 点 ( {:>5.1f} pt )",
            "params": ["最大素点", "最大獲得ポイント"],
        },
        "連続トップ": {
            "order": False, "column": "連続トップ", "threshold": 2,
            "str": "{:>2d} 連続 ( {:>2d} ゲーム中 )",
            "params": ["連続トップ", "ゲーム数"],
        },
        "連続連対": {
            "order": False, "column": "連続連対", "threshold": 2,
            "str": "{:>2d} 連続 ( {:>2d} ゲーム中 )",
            "params": ["連続連対", "ゲーム数"],
        },
        "連続ラス回避": {
            "order": False, "column": "連続ラス回避", "threshold": 2,
            "str": "{:>2d} 連続 ( {:>2d} ゲーム中 )",
            "params": ["連続ラス回避", "ゲーム数"],
        },
    }

    for key, val in data.items():  # ランク付け
        result_df[f"{key}_rank"] = result_df[key].rank(
            method="dense",
            ascending=val["order"]
        )

    for x in ["連続トップ", "連続連対", "連続ラス回避"]:  # 型変換
        result_df[x] = result_df[x].astype(int)

    if g.cfg.config["mahjong"].getboolean("ignore_flying", False):
        data.pop("トビ率")

    # --- 表示
    if g.opt.individual:  # 個人集計
        msg1 = "\n*【ランキング】*\n"
    else:  # チーム集計
        msg1 = "\n*【チームランキング】*\n"

    msg1 += f.message.header(game_info, "", 1)
    msg2 = {}

    for key, val in data.items():
        if key in g.cfg.dropitems.ranking:  # 非表示項目
            continue

        msg2[key] = f"\n*{key}*\n"
        tmp_df = result_df.sort_values(
            [f"{key}_rank", "ゲーム数"],
            ascending=[True, False]
        ).query(
            f"{key}_rank <= @g.opt.ranked and {val['column']} >= {val['threshold']}"
        )

        for _, s in tmp_df.drop_duplicates(subset="name").iterrows():
            msg2[key] += ("\t{:3d}：{}\t" + val["str"] + "\n").format(
                int(s[f"{key}_rank"]), s["表示名"],
                *[s[x] for x in val["params"]]
            ).replace("-", "▲")

        if msg2[key].strip().count("\n") == 0:  # 対象者がいなければ項目を削除
            msg2.pop(key)

    return (msg1, msg2)
