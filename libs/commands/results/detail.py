"""
libs/commands/results/detail.py
"""

import re
import textwrap
from typing import cast

import pandas as pd

import libs.global_value as g
from cls.timekit import ExtendedDatetime as ExtDt
from cls.types import GameInfoDict
from libs.data import aggregate, loader, lookup
from libs.functions import message
from libs.utils import formatter, textutil


def aggregation():
    """個人/チーム成績詳細を集計して返す
    Returns:
        dict: slackにpostするデータ
    """

    # 検索動作を合わせる
    g.params.update(guest_skip=g.params.get("guest_skip2"))

    if g.params["player_name"] in lookup.internal.get_team():
        g.params.update(individual=False)
    elif g.params["player_name"] in g.member_list:
        g.params.update(individual=True)

    # --- データ収集
    game_info: GameInfoDict = aggregate.game_info()
    msg_data: dict = {}
    mapping_dict: dict = {}

    if game_info["game_count"] == 0:
        if g.params.get("individual"):
            msg_data["検索範囲"] = f"{ExtDt(g.params["starttime"]).format("ymdhm")}"
            msg_data["検索範囲"] += f" ～ {ExtDt(g.params["endtime"]).format("ymdhm")}"
            msg_data["特記事項"] = "、".join(message.remarks())
            msg_data["検索ワード"] = message.search_word()
            msg_data["対戦数"] = f"0 戦 (0 勝 0 敗 0 分) {message.badge_status(0, 0)}"
            return (message_build(msg_data), {})
        return ("登録されていないチームです", {})

    result_df = aggregate.game_results()
    record_df = aggregate.ranking_record()

    if result_df.empty or record_df.empty:
        return (message.reply(message="no_target"), {})

    result_df = pd.merge(
        result_df, record_df,
        on=["name", "name"],
        suffixes=["", "_x"]
    )

    player_name = formatter.name_replace(g.params["player_name"], add_mark=True)
    if g.params.get("anonymous"):
        mapping_dict = formatter.anonymous_mapping(result_df["name"].unique().tolist())
        result_df["name"] = result_df["name"].replace(mapping_dict)
        player_name = mapping_dict[player_name]

    result_df = formatter.df_rename(result_df)
    data = result_df.to_dict(orient="records")[0]

    # --- 表示内容
    msg_data.update(get_headline(data, game_info, player_name))
    msg_data.update(get_totalization(data))

    msg2: dict = {}
    msg2["座席データ"] = get_seat_data(data)
    msg2.update(get_record(data))  # ベスト/ワーストレコード
    msg2.update(get_regulations(mapping_dict))  # レギュレーション

    if g.params.get("game_results"):  # 戦績
        msg2["戦績"] = get_game_results(mapping_dict)

    if g.params.get("versus_matrix"):  # 対戦結果
        msg2["対戦"] = get_versus_matrix(mapping_dict)

    # 非表示項目
    if g.cfg.mahjong.ignore_flying:
        g.cfg.dropitems.results.append("トビ")
    if "トビ" in g.cfg.dropitems.results:
        msg2["座席データ"] = re.sub(r"/ .* /", "/", msg2["座席データ"], flags=re.MULTILINE)
    if "役満" in g.cfg.dropitems.results:
        msg2["座席データ"] = msg2["座席データ"].replace(" / 役満", "")
        msg2["座席データ"] = re.sub(r" / [0-9]+$", "", msg2["座席データ"], flags=re.MULTILINE)
        msg2.pop("役満和了", None)

    if not g.params.get("statistics"):  # 統計
        for k in ("座席データ", "ベストレコード", "ワーストレコード"):
            msg2.pop(k, None)

    for k in list(msg2.keys()):
        if k in g.cfg.dropitems.results:
            msg2.pop(k)

    return (message_build(msg_data), msg2)


def get_headline(data: dict, game_info: GameInfoDict, player_name: str) -> dict:
    """ヘッダメッセージ生成

    Args:
        data (dict): 生成内容が格納された辞書
        game_info (GameInfoDict): ゲーム集計情報
        player_name (str): プレイヤー名

    Returns:
        dict: 集計データ
    """

    ret: dict = {}

    if g.params.get("individual"):
        ret["title"] = "*【個人成績】*"
        ret["プレイヤー名"] = f"{player_name} {message.badge_degree(data["ゲーム数"])}"
        if (team_list := lookup.internal.which_team(g.params["player_name"])):
            ret["所属チーム"] = team_list
    else:
        ret["title"] = "*【チーム成績】*"
        ret["チーム名"] = f"{g.params["player_name"]} {message.badge_degree(data["ゲーム数"])}"
        ret["登録メンバー"] = "、".join(lookup.internal.get_teammates(g.params["player_name"]))

    badge_status = message.badge_status(data["ゲーム数"], data["win"])
    ret["検索範囲"] = message.item_search_range(kind="str", time_pattern="time").strip()
    ret["集計範囲"] = message.item_aggregation_range(game_info, kind="str").strip()
    ret["特記事項"] = "、".join(message.remarks())
    ret["検索ワード"] = message.search_word()
    ret["対戦数"] = f"{data["ゲーム数"]} 戦 ({data["win"]} 勝 {data["lose"]} 敗 {data["draw"]} 分) {badge_status}"
    ret["_blank1"] = True

    return ret


def get_totalization(data: dict) -> dict:
    """集計トータルメッセージ生成

    Args:
        data (dict): 生成内容が格納された辞書

    Returns:
        dict: 生成メッセージ
    """

    ret: dict = {}

    ret["通算ポイント"] = f"{data['通算ポイント']:+.1f}pt".replace("-", "▲")
    ret["平均ポイント"] = f"{data['平均ポイント']:+.1f}pt".replace("-", "▲")
    ret["平均順位"] = f"{data['平均順位']:1.2f}"
    if g.params.get("individual") and g.cfg.badge.grade.display:
        ret["段位"] = message.badge_grade(g.params["player_name"])
    ret["_blank2"] = True
    ret["1位"] = f"{data['1位']:2} 回 ({data['1位率']:6.2f}%)"
    ret["2位"] = f"{data['2位']:2} 回 ({data['2位率']:6.2f}%)"
    ret["3位"] = f"{data['3位']:2} 回 ({data['3位率']:6.2f}%)"
    ret["4位"] = f"{data['4位']:2} 回 ({data['4位率']:6.2f}%)"
    ret["トビ"] = f"{data['トビ']:2} 回 ({data['トビ率']:6.2f}%)"
    ret["役満"] = f"{data['役満和了']:2} 回 ({data['役満和了率']:6.2f}%)"

    return ret


def get_seat_data(data: dict) -> str:
    """座席データメッセージ生成

    Args:
        data (dict): 生成内容が格納された辞書

    Returns:
        str: 生成メッセージ
    """

    ret: str = textwrap.dedent(f"""\
        *【座席データ】*
        \t# 席：順位分布(平均順位) / トビ / 役満 #
        \t{data["東家-順位分布"]:22s} / {data["東家-トビ"]} / {data["東家-役満和了"]}
        \t{data["南家-順位分布"]:22s} / {data["南家-トビ"]} / {data["南家-役満和了"]}
        \t{data["西家-順位分布"]:22s} / {data["西家-トビ"]} / {data["西家-役満和了"]}
        \t{data["北家-順位分布"]:22s} / {data["北家-トビ"]} / {data["北家-役満和了"]}
    """).replace("0.00", "-.--")

    return ret


def get_record(data: dict) -> dict:
    """レコード情報メッセージ生成

    Args:
        data (dict): 生成内容が格納された辞書

    Returns:
        dict: 集計データ
    """

    def current_data(count: int) -> str:
        if count == 0:
            ret = "0 回"
        elif count == 1:
            ret = "1 回目"
        else:
            ret = f"{count} 連続中"
        return ret

    def max_data(count: int, current: int) -> str:
        if count == 0:
            ret = "*****"
        elif count == 1:
            ret = "最大 1 回"
        else:
            ret = f"最大 {count} 連続"

        if count == current:
            if count:
                ret = "記録更新中"
            else:
                ret = "記録なし"

        return ret

    ret: dict = {}
    ret["ベストレコード"] = textwrap.dedent(f"""\
        *【ベストレコード】*
        \t連続トップ：{current_data(data["c_top"])} ({max_data(data["連続トップ"], data["c_top"])})
        \t連続連対：{current_data(data["c_top2"])} ({max_data(data["連続連対"], data["c_top2"])})
        \t連続ラス回避：{current_data(data["c_top3"])} ({max_data(data["連続ラス回避"], data["c_top3"])})
        \t最大素点：{data["最大素点"] * 100}点
        \t最大獲得ポイント：{data["最大獲得ポイント"]}pt
    """).replace("-", "▲").replace("*****", "-----")

    ret["ワーストレコード"] = textwrap.dedent(f"""\
        *【ワーストレコード】*
        \t連続ラス：{current_data(data["c_low4"])} ({max_data(data["連続ラス"], data["c_low4"])})
        \t連続逆連対：{current_data(data["c_low2"])} ({max_data(data["連続逆連対"], data["c_low2"])})
        \t連続トップなし：{current_data(data["c_low"])} ({max_data(data["連続トップなし"], data["c_low"])})
        \t最小素点：{data['最小素点'] * 100}点
        \t最小獲得ポイント：{data['最小獲得ポイント']}pt
    """).replace("-", "▲").replace("*****", "-----")

    return ret


def get_regulations(mapping_dict: dict) -> dict:
    """レギュレーション情報メッセージ生成

    Returns:
        dict: 集計データ
    """

    ret: dict = {}

    df_grandslam = aggregate.remark_count("grandslam")
    df_regulations = aggregate.remark_count("regulation")

    if g.params.get("anonymous"):
        new_list = list(set(df_grandslam["name"].unique().tolist() + df_regulations["name"].unique().tolist()))
        for name in new_list:
            if name in mapping_dict:
                new_list.remove(name)

        mapping_dict.update(formatter.anonymous_mapping(new_list, len(mapping_dict)))
        df_grandslam["name"] = df_grandslam["name"].replace(mapping_dict)
        df_regulations["name"] = df_regulations["name"].replace(mapping_dict)

    if not df_grandslam.empty:
        ret["役満和了"] = "\n*【役満和了】*\n"
        for x in df_grandslam.itertuples():
            ret["役満和了"] += f"\t{x.matter}\t{x.count}回\n"

    if not df_regulations.query("type == 1").empty:
        ret["卓外ポイント"] = "\n*【卓外ポイント】*\n"
        for x in df_regulations.query("type == 1").itertuples():
            ex_point = str(x.ex_point).replace("-", "▲")
            ret["卓外ポイント"] += f"\t{x.matter}\t{x.count}回 ({ex_point}pt)\n"

    if not df_regulations.query("type != 1").empty:
        ret["その他"] = "\n*【その他】*\n"
        for x in df_regulations.query("type != 1").itertuples():
            ret["その他"] += f"\t{x.matter}\t{x.count}回\n"

    return ret


def get_game_results(mapping_dict: dict) -> str:
    """戦績データ出力用メッセージ生成

    Returns:
        str: 出力メッセージ
    """

    ret: str = "\n*【戦績】*\n"
    data: dict = {}

    target_player = formatter.name_replace(g.params["target_player"][0], add_mark=True)
    df = loader.read_data("summary/details.sql").fillna(value="")

    if g.params.get("anonymous"):
        mapping_dict.update(formatter.anonymous_mapping(df["name"].unique().tolist(), len(mapping_dict)))
        df["name"] = df["name"].replace(mapping_dict)
        target_player = mapping_dict.get(target_player, target_player)

    p_list: dict = df["name"].unique().tolist()
    if g.params.get("verbose"):
        data["p0"] = df.filter(items=["playtime", "guest_count", "same_team"]).drop_duplicates().set_index("playtime")
        for idx, prefix in enumerate(["p1", "p2", "p3", "p4"]):  # pylint: disable=unused-variable  # noqa: F841
            tmp_df = df.query("seat == @idx + 1").filter(
                items=["playtime", "name", "rpoint", "rank", "point", "grandslam", "name"]
            )

            data[prefix] = tmp_df.rename(
                columns={
                    "name": f"{prefix}_name",
                    "rpoint": f"{prefix}_rpoint",
                    "rank": f"{prefix}_rank",
                    "point": f"{prefix}_point",
                    "grandslam": f"{prefix}_gs",
                }
            ).set_index("playtime")

        max_len = textutil.count_padding(p_list)
        df_data = pd.concat([data["p1"], data["p2"], data["p3"], data["p4"], data["p0"]], axis=1)
        df_data = df_data.query("p1_name == @target_player or p2_name == @target_player or p3_name == @target_player or p4_name == @target_player")

        for x in df_data.itertuples():
            vs_guest = ""
            if x.guest_count >= 2 and g.params["individual"]:
                vs_guest = "(2ゲスト戦)"
            if x.same_team == 1 and not g.params["individual"]:
                vs_guest = "(チーム同卓)"

            ret += textwrap.dedent(
                """\
                {} {}
                \t東家：{} {} {}位 {:8d}点 ({:7.1f}pt) {}
                \t南家：{} {} {}位 {:8d}点 ({:7.1f}pt) {}
                \t西家：{} {} {}位 {:8d}点 ({:7.1f}pt) {}
                \t北家：{} {} {}位 {:8d}点 ({:7.1f}pt) {}
                """
            ).format(
                x.Index.replace("-", "/"), vs_guest,
                x.p1_name, " " * (max_len - textutil.len_count(x.p1_name)), x.p1_rank, int(x.p1_rpoint) * 100, x.p1_point, x.p1_gs,
                x.p2_name, " " * (max_len - textutil.len_count(x.p2_name)), x.p2_rank, int(x.p2_rpoint) * 100, x.p2_point, x.p2_gs,
                x.p3_name, " " * (max_len - textutil.len_count(x.p3_name)), x.p3_rank, int(x.p3_rpoint) * 100, x.p3_point, x.p3_gs,
                x.p4_name, " " * (max_len - textutil.len_count(x.p4_name)), x.p4_rank, int(x.p4_rpoint) * 100, x.p4_point, x.p4_gs,
            ).replace(" -", "▲")
    else:
        df_data = df.query("name == @target_player").set_index("playtime")
        for x in df_data.itertuples():
            play_time = str(x.Index).replace("-", "/")
            rpoint = cast(int, x.rpoint) * 100
            point = cast(float, x.point)
            vs_guest = ""
            guest_count = cast(int, x.guest_count)
            same_team = cast(int, x.same_team)

            if guest_count >= 2 and g.params.get("individual"):
                vs_guest = g.cfg.setting.guest_mark
            if same_team == 1 and not g.params.get("individual"):
                vs_guest = g.cfg.setting.guest_mark

            ret += f"\t{vs_guest}{play_time}  {x.rank}位 {rpoint:8d}点 ({point:7.1f}pt) {x.grandslam}\n".replace("-", "▲")

    return ret


def get_versus_matrix(mapping_dict: dict) -> str:
    """対戦結果データ出力用メッセージ生成

    Returns:
        str: 出力メッセージ
    """

    ret: str = "\n*【対戦結果】*\n"
    df = loader.read_data("summary/versus_matrix.sql")

    if g.params.get("anonymous"):
        mapping_dict.update(formatter.anonymous_mapping(df["vs_name"].unique().tolist(), len(mapping_dict)))
        df["my_name"] = df["my_name"].replace(mapping_dict)
        df["vs_name"] = df["vs_name"].replace(mapping_dict)

    max_len = textutil.count_padding(df["vs_name"].unique().tolist())

    for _, r in df.iterrows():
        padding = max_len - textutil.len_count(r["vs_name"])
        ret += f"\t{r["vs_name"]}{" " * padding} ： "
        ret += f"{r["game"]:3d} 戦 {r["win"]:3d} 勝 {r["lose"]:3d} 敗 ({r["win%"]:6.2f}%)\n"

    return ret


def message_build(data: dict) -> str:
    """表示する内容をテキストに起こす

    Args:
        data (dict): 内容

    Returns:
        str: 表示するテキスト
    """

    msg = ""
    for k, v in data.items():
        if not v:  # 値がない項目は削除
            continue
        match k:
            case k if k in g.cfg.dropitems.results:  # 非表示
                pass
            case k if k.startswith("_blank"):
                msg += "\t\n"
            case "title":
                msg += f"{v}\n"
            case _:
                msg += f"\t{k}：{v}\n"

    return msg.strip()
