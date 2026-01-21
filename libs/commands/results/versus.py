"""
libs/commands/results/versus.py
"""

import textwrap
from typing import TYPE_CHECKING, cast

import pandas as pd

import libs.global_value as g
from libs.data import loader
from libs.functions import compose
from libs.types import StyleOptions
from libs.utils import converter, formatter

if TYPE_CHECKING:
    from integrations.protocols import MessageParserProtocol
    from libs.types import MessageType


def aggregation(m: "MessageParserProtocol"):
    """直接対戦結果を集計して返す

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    # 検索動作を合わせる
    g.params.update({"guest_skip": g.params["guest_skip2"]})

    # --- データ収集
    data: "MessageType"
    df_vs = loader.read_data("SUMMARY_VERSUS_MATRIX")
    df_game = loader.read_data("SUMMARY_DETAILS").fillna(value="")
    df_data = pd.DataFrame(columns=df_game.columns)  # ファイル出力用

    my_name = formatter.name_replace(g.params["player_name"], add_mark=True)
    vs_list = [formatter.name_replace(x, add_mark=True) for x in g.params["competition_list"].values()]

    # --- 匿名化
    if g.params.get("anonymous"):
        mapping_dict = formatter.anonymous_mapping([my_name] + vs_list)
        my_name = mapping_dict[my_name]
        vs_list = [mapping_dict[name] for name in vs_list]
        df_vs["my_name"] = df_vs["my_name"].replace(mapping_dict)
        df_vs["vs_name"] = df_vs["vs_name"].replace(mapping_dict)

    # --- 表示内容
    if g.params.get("all_player"):
        vs = "全員"
    else:
        vs = ",".join(vs_list)

    game_result: dict = {}  # 対戦結果格納用
    drop_name: list = []  # 対戦記録なしプレイヤー

    if len(df_vs) == 0:  # 検索結果なし
        m.post.headline = {"直接対戦": "対戦記録が見つかりません。"}
        m.status.result = False
        return

    m.post.headline = {"直接対戦": tmpl_header(my_name, vs)}
    for vs_name in vs_list:
        title = f"{my_name} vs {vs_name}"
        if vs_name in vs_list:
            data = df_vs.query("my_name == @my_name and vs_name == @vs_name")
            if data.empty:
                if len(vs_list) <= 5 and not g.params.get("all_player"):
                    drop_name.append(vs_name)
                    game_result[title] = "対戦記録はありません。"
                continue

            game_result[title] = tmpl_vs_table(data.to_dict(orient="records")[0])

            # ゲーム結果
            if g.params.get("game_results"):
                count = 0
                my_score = df_game.query("name == @my_name")
                vs_score = df_game.query("name == @vs_name")
                my_playtime = my_score["playtime"].to_list()
                vs_playtime = vs_score["playtime"].to_list()

                for playtime in sorted(set(my_playtime + vs_playtime)):
                    if playtime in my_playtime and playtime in vs_playtime:
                        current_game = df_game.query("playtime == @playtime")
                        df_data = current_game if df_data.empty else pd.concat([df_data, current_game])
                        count += 1
        else:  # 対戦記録なし
            game_result[title] = "\t対戦相手が見つかりません。\n\n"
    # 結果
    if len(game_result):
        for k, v in game_result.items():
            m.set_data(v, StyleOptions(title=k))
    else:
        m.set_data("対戦記録が見つかりません。", StyleOptions(title="対戦記録が見つかりません。", key_title=False))
        m.status.result = False
        return

    # --- ファイル出力
    if len(df_data) != 0:
        df_data["座席"] = df_data["seat"].apply(lambda x: ["東家", "南家", "西家", "北家"][x - 1])
        df_data["rpoint"] = df_data["rpoint"] * 100
    df_data = formatter.df_rename2(
        df_data.filter(items=["playtime", "座席", "name", "rank", "rpoint", "point", "yakuman"]).drop_duplicates(),
        StyleOptions(),
    )

    namelist = list(cast(dict, g.params["competition_list"]).values())  # noqa: F841
    df_vs["対戦相手"] = df_vs["vs_name"].apply(lambda x: str(x).strip())
    df_vs["my_rpoint_avg"] = (df_vs["my_rpoint_avg"] * 100).astype("int")
    df_vs["vs_rpoint_avg"] = (df_vs["vs_rpoint_avg"] * 100).astype("int")
    df_vs = formatter.df_rename2(df_vs, StyleOptions())
    df_vs2 = (
        df_vs.query("vs_name == @namelist")
        .filter(
            items=[
                "対戦相手",
                "対戦結果",
                "勝率",
                "獲得ポイント(自分)",
                "平均ポイント(自分)",
                "平均素点(自分)",
                "順位分布(自分)",
                "平均順位(自分)",
                "獲得ポイント(相手)",
                "平均ポイント(相手)",
                "平均素点(相手)",
                "順位分布(相手)",
                "平均順位(相手)",
            ]
        )
        .drop_duplicates()
    )

    match str(g.params.get("format", "default")).lower():
        case "csv":
            m.set_data(converter.save_output(df_data, StyleOptions(format_type="csv", base_name="result")), StyleOptions(title="対戦結果"))
            m.set_data(converter.save_output(df_vs2, StyleOptions(format_type="csv", base_name="versus")), StyleOptions(title="成績"))
        case "text" | "txt":
            m.set_data(converter.save_output(df_data, StyleOptions(format_type="txt", base_name="result")), StyleOptions(title="対戦結果"))
            m.set_data(converter.save_output(df_vs2, StyleOptions(format_type="txt", base_name="versus")), StyleOptions(title="成績"))
        case _:
            pass


def tmpl_header(my_name: str, vs_name: str) -> str:
    """ヘッダテンプレート

    Args:
        my_name (str): 自分の名前
        vs_name (str): 相手の名前

    Returns:
        str: 出力データ
    """
    ret = textwrap.dedent(
        f"""\
        \tプレイヤー名：{my_name}
        \t対戦相手：{vs_name}
        \t集計範囲：{compose.text_item.search_range()}
        \t{compose.text_item.remarks(True)}
        """
    ).rstrip()

    return ret


def tmpl_vs_table(data: dict) -> str:
    """直接対決結果表示テンプレート

    Args:
        data (dict): 結果データ

    Returns:
        str: 出力データ
    """

    ret = textwrap.indent(
        "".join(
            [
                textwrap.dedent(
                    f"""\
                    対戦数：{data["game"]} 戦 {data["win"]} 勝 {data["lose"]} 敗 ({data["win%"]:.2f}%)
                    平均素点差：{(data["my_rpoint_avg"] - data["vs_rpoint_avg"]) * 100:+.0f} 点
                    獲得ポイント合計(自分)：{data["my_point_sum"]:+.1f}pt
                    獲得ポイント合計(相手)：{data["vs_point_sum"]:+.1f}pt
                    """.replace("-", "▲")
                ),
                textwrap.dedent(
                    f"""\
                    順位分布(自分)：{data["my_1st"]}-{data["my_2nd"]}-{data["my_3rd"]}-{data["my_4th"]} ({data["my_rank_avg"]:1.2f})
                    順位分布(相手)：{data["vs_1st"]}-{data["vs_2nd"]}-{data["vs_3rd"]}-{data["vs_4th"]} ({data["vs_rank_avg"]:1.2f})
                    """  # noqa: E501
                ),
            ]
        ),
        "\t",
    )

    return ret.rstrip() + "\n"
