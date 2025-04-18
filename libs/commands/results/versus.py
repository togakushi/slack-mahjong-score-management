"""
libs/commands/results/versus.py
"""

import os
import textwrap

import pandas as pd

import libs.global_value as g
from libs.data import loader
from libs.functions import message
from libs.utils import dateutil, formatter


def aggregation():
    """直接対戦結果を集計して返す

    Returns:
        Tuple[str, dict, dict]
        - str: ヘッダ情報
        - dict: 集計データ
        - dict: 生成ファイル情報
    """

    # 検索動作を合わせる
    g.params.update(guest_skip=g.params.get("guest_skip2"))

    # --- データ収集
    df_vs = loader.read_data(os.path.join(g.cfg.script_dir, "libs/queries/summary/versus_matrix.sql"))
    df_game = loader.read_data(os.path.join(g.cfg.script_dir, "libs/queries/summary/details.sql")).fillna(value="")
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

    msg1 = tmpl_header(my_name, vs)
    msg2: dict = {}  # 対戦結果格納用

    tmp_msg: dict = {}
    drop_name: list = []  # 対戦記録なしプレイヤー
    if len(df_vs) == 0:  # 検索結果なし
        msg2[""] = "対戦記録が見つかりません。\n"
        return (msg1, msg2, "")

    for vs_name in vs_list:
        tmp_msg[vs_name] = {}
        if vs_name in vs_list:
            data = df_vs.query("my_name == @my_name and vs_name == @vs_name")
            if data.empty:
                drop_name.append(vs_name)
                tmp_msg[vs_name]["info"] = f"*【{my_name} vs {vs_name}】*\n\t対戦記録はありません。"
                continue

            tmp_msg[vs_name]["info"] = tmpl_vs_table(data.to_dict(orient="records")[0])

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
                        guest_count = current_game["guest"].sum()
                        df_data = current_game if df_data.empty else pd.concat([df_data, current_game])

                        tmp_msg[vs_name][count] = f"{"" if count else "【戦績】\n"}"
                        if g.params.get("verbose"):  # 詳細表示
                            tmp_msg[vs_name][count] += tmpl_result_verbose(current_game, playtime, guest_count)
                        else:  # 簡易表示
                            tmp_msg[vs_name][count] += tmpl_result_simple(my_score, vs_score, playtime, guest_count)
                        count += 1
                        df_data = current_game if df_data.empty else pd.concat([df_data, current_game])
        else:  # 対戦記録なし
            tmp_msg[vs_name]["info"] = f"*【{my_name} vs {vs_name}】*\n\t対戦相手が見つかりません。\n\n"

    # --- データ整列&まとめ
    for key, val in tmp_msg.items():
        if key in drop_name and len(vs_list) > 5 and not g.params.get("all_player"):
            continue
        msg2[f"{key}_info"] = val.pop("info") + "\n"
        if val:
            for x in val:
                msg2[f"{key}_{x}"] = textwrap.indent(val[x], "\t")
            msg2[f"{key}_blank"] += "\n"

    # --- ファイル出力
    if len(df_data) != 0:
        df_data["座席"] = df_data["seat"].apply(lambda x: ["東家", "南家", "西家", "北家"][x - 1])
        df_data["rpoint"] = df_data["rpoint"] * 100
    df_data = formatter.df_rename(
        df_data.filter(items=["playtime", "座席", "name", "rank", "rpoint", "point", "grandslam"]).drop_duplicates(),
        short=False
    )

    namelist = list(g.params["competition_list"].values())  # pylint: disable=unused-variable  # noqa: F841
    df_vs["対戦相手"] = df_vs["vs_name"].apply(lambda x: x.strip())
    df_vs["my_rpoint_avg"] = (df_vs["my_rpoint_avg"] * 100).astype("int")
    df_vs["vs_rpoint_avg"] = (df_vs["vs_rpoint_avg"] * 100).astype("int")
    df_vs = formatter.df_rename(df_vs)
    df_vs2 = df_vs.query("vs_name == @namelist").filter(
        items=[
            "対戦相手", "対戦結果", "勝率",
            "獲得ポイント(自分)", "平均ポイント(自分)", "平均素点(自分)", "順位分布(自分)", "平均順位(自分)",
            "獲得ポイント(相手)", "平均ポイント(相手)", "平均素点(相手)", "順位分布(相手)", "平均順位(相手)",
        ]
    ).drop_duplicates()

    match g.params.get("format", "default").lower().lower():
        case "csv":
            file_list = {
                "対戦結果": formatter.save_output(df_data, "csv", "result.csv"),
                "成績": formatter.save_output(df_vs2, "csv", "versus.csv"),
            }
        case "text" | "txt":
            file_list = {
                "対戦結果": formatter.save_output(df_data, "txt", "result.txt"),
                "成績": formatter.save_output(df_vs2, "txt", "versus.txt"),
            }
        case _:
            file_list = {}

    return (msg1, msg2, file_list)


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
        *【直接対戦結果】*
        \tプレイヤー名：{my_name}
        \t対戦相手：{vs_name}
        \t{message.item_search_range()}
        \t{message.remarks(True)}
        """
    ).strip()

    return (message.del_blank_line(ret))


def tmpl_vs_table(data: dict) -> str:
    """直接対決結果表示テンプレート

    Args:
        data (dict): 結果データ

    Returns:
        str: 出力データ
    """

    ret = f"*【{data["my_name"].strip()} vs {data["vs_name"].strip()}】*\n"
    ret += textwrap.indent(
        "".join([
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
                """
            )
        ]),
        "\t"
    )

    return (ret.strip())


def tmpl_result_verbose(current_game: pd.DataFrame, playtime: str, guest_count: int) -> str:
    """詳細結果テンプレート

    Args:
        current_game (pd.DataFrame): 成績
        playtime (str): プレイ時間
        guest_count (int): ゲスト人数

    Returns:
        str: 出力データ
    """

    s1 = current_game.query("seat == 1").to_dict(orient="records")[0]
    s2 = current_game.query("seat == 2").to_dict(orient="records")[0]
    s3 = current_game.query("seat == 3").to_dict(orient="records")[0]
    s4 = current_game.query("seat == 4").to_dict(orient="records")[0]

    ret = textwrap.dedent(
        f"""\
        {dateutil.ts_conv(playtime, "hms")} {"(2ゲスト戦)" if guest_count >= 2 else ""}
        \t東家：{s1["name"]} {s1["rank"]}位 {s1["rpoint"] * 100:>7} 点 ({s1["point"]:>+5.1f}pt) {s1["grandslam"]}
        \t南家：{s2["name"]} {s2["rank"]}位 {s2["rpoint"] * 100:>7} 点 ({s2["point"]:>+5.1f}pt) {s2["grandslam"]}
        \t西家：{s3["name"]} {s3["rank"]}位 {s3["rpoint"] * 100:>7} 点 ({s3["point"]:>+5.1f}pt) {s3["grandslam"]}
        \t北家：{s4["name"]} {s4["rank"]}位 {s4["rpoint"] * 100:>7} 点 ({s4["point"]:>+5.1f}pt) {s4["grandslam"]}
        """.replace("-", "▲")
    )

    return (ret.strip())


def tmpl_result_simple(my_score: pd.DataFrame, vs_score: pd.DataFrame, playtime: str, guest_count: int) -> str:
    """簡易結果テンプレート

    Args:
        my_score (pd.DataFrame): 自分の成績
        vs_score (pd.DataFrame): 相手の成績
        playtime (str): プレイ時間
        guest_count (int): ゲスト人数

    Returns:
        str: 出力データ
    """
    a1 = my_score.query("playtime == @playtime").to_dict(orient="records")[0]
    a2 = vs_score.query("playtime == @playtime").to_dict(orient="records")[0]
    ret = textwrap.dedent(
        f"""\
        {playtime.replace("-", "/")} {"(2ゲスト戦)" if guest_count >= 2 else ""}
        \t{a1["name"]}：{a1["rank"]}位 {a1["rpoint"] * 100:>7} 点 ({a1["point"]:>+5.1f}pt) {a1["grandslam"]}
        \t{a2["name"]}：{a2["rank"]}位 {a2["rpoint"] * 100:>7} 点 ({a2["point"]:>+5.1f}pt) {a2["grandslam"]}
        """.replace("-", "▲")
    )

    return (ret.strip())
