"""
libs/commands/results/rating.py
"""

import pandas as pd

import libs.global_value as g
from cls.types import GameInfoDict
from integrations.protocols import MessageParserProtocol
from libs.data import aggregate, loader
from libs.functions import compose, message
from libs.utils import formatter


def aggregation(m: MessageParserProtocol):
    """レーティングを集計して返す

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    # 情報ヘッダ
    add_text: str = ""
    headline: str = "*【レーティング】*\n"

    # データ収集
    # g.params.update(guest_skip=False)  # 2ゲスト戦強制取り込み
    game_info: GameInfoDict = aggregate.game_info()

    if not game_info["game_count"]:  # 検索結果が0件のとき
        m.post.message = headline + message.random_reply(m, "no_hits")
        m.post.file_list = [{"dummy": ""}]
        return

    df_results = loader.read_data("ranking/results.sql").set_index("name")
    df_ratings = aggregate.calculation_rating()

    # 最終的なレーティング
    final = df_ratings.ffill().tail(1).transpose()
    final.columns = ["rate"]
    final["name"] = final.copy().index

    df = pd.merge(df_results, final, on=["name"]).sort_values(by="rate", ascending=False)
    df = df.query("count >= @g.params['stipulated']").copy()  # 足切り

    # 集計対象外データの削除
    if g.params.get("unregistered_replace"):  # 個人戦
        for player in df.itertuples():
            if player.name not in g.member_list:
                df = df.copy().drop(player.Index)

    if not g.params.get("individual"):  # チーム戦
        df = df.copy().query("name != '未所属'")

    # 順位偏差 / 得点偏差
    df["point_dev"] = (df["rpoint_avg"] - df["rpoint_avg"].mean()) / df["rpoint_avg"].std(ddof=0) * 10 + 50
    df["rank_dev"] = (df["rank_avg"] - df["rank_avg"].mean()) / df["rank_avg"].std(ddof=0) * -10 + 50

    # 段位
    if g.cfg.badge.grade.display:
        for idx in df.index:
            name = str(df.at[idx, "name"]).replace(f"({g.cfg.setting.guest_mark})", "")
            df.at[idx, "grade"] = compose.badge.grade(name, False)

    # 表示
    if g.params.get("anonymous"):
        mapping_dict = formatter.anonymous_mapping(df["name"].unique().tolist())
        df["name"] = df["name"].replace(mapping_dict)

    if df.empty:
        m.post.message = headline + message.random_reply(m, "no_target")
        m.post.file_list = [{"dummy": ""}]
        return

    headline += message.header(game_info, m, add_text, 1)
    df = formatter.df_rename(df.filter(
        items=[
            "name", "rate", "rank_distr", "rank_avg", "rank_dev", "rpoint_avg", "point_dev", "grade"
        ]
    ), short=False).copy()
    df = df.drop(columns=[x for x in g.cfg.dropitems.ranking if x in df.columns.to_list()])  # 非表示項目

    msg: dict = {}
    table_param: dict = {
        "index": False,
        "tablefmt": "simple",
        "numalign": "right",
        "floatfmt": ["", ".1f", "", ".2f", ".0f", ".1f", ".0f"],
    }

    step = 30
    length = len(df)
    for i in range(int(length / step) + 1):
        s = step * i
        e = step * (i + 1)
        if e + step / 2 > length:
            table = df[s:].to_markdown(**table_param)
            msg[s] = f"```\n{table}\n```\n"
            break

        table = df[s:e].to_markdown(**table_param)
        msg[s] = f"```\n{table}\n```\n"

    prefix_rating = str(g.params.get("filename", "rating"))
    match str(g.params.get("format", "default")).lower():
        case "csv":
            save_file = formatter.save_output(df, "csv", f"{prefix_rating}.csv", headline)
        case "text" | "txt":
            save_file = formatter.save_output(df, "txt", f"{prefix_rating}.txt", headline)
        case _:
            save_file = ""

    m.post.headline = headline
    m.post.message = msg
    m.post.file_list = [{"レーティング": save_file}]
    m.post.summarize = False
