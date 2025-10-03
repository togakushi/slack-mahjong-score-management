"""
libs/commands/results/detail.py
"""

import textwrap
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

import libs.global_value as g
from libs.data import aggregate, loader, lookup
from libs.functions import compose, message
from libs.utils import formatter, textutil

if TYPE_CHECKING:
    from cls.types import GameInfoDict
    from integrations.protocols import MessageParserProtocol


def aggregation(m: MessageParserProtocol) -> bool:
    """個人/チーム成績詳細を集計して返す

    Args:
        m (MessageParserProtocol): メッセージデータ
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

    # タイトル
    if g.params.get("individual"):
        title = "個人成績詳細"
    else:
        title = "チーム成績詳細"

    if game_info["game_count"] == 0:
        if g.params.get("individual"):
            msg_data["検索範囲"] = f"{compose.text_item.search_range(time_pattern="time")}"
            msg_data["特記事項"] = "、".join(compose.text_item.remarks())
            msg_data["検索ワード"] = compose.text_item.search_word()
            msg_data["対戦数"] = f"0 戦 (0 勝 0 敗 0 分) {compose.badge.status(0, 0)}"
            m.post.headline = {title: message_build(msg_data)}
        else:
            m.post.headline = {title: "登録されていないチームです。"}
        return False

    result_df = aggregate.game_results()
    record_df = aggregate.ranking_record()

    if result_df.empty or record_df.empty:
        m.post.headline = {title: message.random_reply(m, "no_target", False)}
        return False

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

    msg: dict = {}
    msg["座席データ"] = pd.DataFrame({
        "席": ["東家", "南家", "西家", "北家"],
        "順位分布": [v for k, v in data.items() if str(k).endswith("-順位分布")],
        "平均順位": [v for k, v in data.items() if str(k).endswith("-平均順位")],
        "トビ": [v for k, v in data.items() if str(k).endswith("-トビ")],
        "役満和了": [v for k, v in data.items() if str(k).endswith("-役満和了")],
    })

    msg.update(get_record(data))  # ベスト/ワーストレコード

    # レギュレーション
    remarks_df = loader.read_data("REMARKS_INFO")
    count_df = remarks_df.groupby("matter").agg(count=("matter", "count"), total=("ex_point", "sum"), type=("type", "max"))
    count_df["matter"] = count_df.index

    work_df = count_df.query("type == 0").filter(items=["matter", "count"])
    if not work_df.empty:
        msg["役満和了"] = work_df.rename(columns={"matter": "和了役", "count": "回数"})

    work_df = count_df.query("type == 1").filter(items=["matter", "count", "total"])
    if not work_df.empty:
        msg["卓外ポイント"] = work_df.rename(columns={"matter": "内容", "count": "回数", "total": "ポイント合計"})

    work_df = count_df.query("type == 2").filter(items=["matter", "count"])
    if not work_df.empty:
        msg["その他"] = work_df.rename(columns={"matter": "内容", "count": "回数"})

    # 戦績
    if g.params.get("game_results"):
        if g.params.get("verbose"):
            msg["戦績"] = get_results_details(mapping_dict)
        else:
            msg["戦績"] = get_results_simple(mapping_dict)

    if g.params.get("versus_matrix"):
        msg["対戦結果"] = get_versus_matrix(mapping_dict)

    # 非表示項目
    if g.cfg.mahjong.ignore_flying:
        g.cfg.dropitems.results.append("トビ")
    if "トビ" in g.cfg.dropitems.results:
        msg["座席データ"].drop(columns=["トビ"], inplace=True)
    if "役満" in g.cfg.dropitems.results:
        msg["座席データ"].drop(columns=["役満和了"], inplace=True)
        msg.pop("役満和了", None)

    if not g.params.get("statistics"):  # 統計
        for k in ("座席データ", "ベストレコード", "ワーストレコード"):
            msg.pop(k, None)

    for k in list(msg.keys()):
        if k in g.cfg.dropitems.results:
            msg.pop(k)

    m.post.headline = {title: message_build(msg_data)}
    m.post.message = msg
    return True


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
        ret["プレイヤー名"] = f"{player_name} {compose.badge.degree(data["ゲーム数"])}"
        if (team_list := lookup.internal.which_team(g.params["player_name"])):
            ret["所属チーム"] = team_list
    else:
        ret["チーム名"] = f"{g.params["player_name"]} {compose.badge.degree(data["ゲーム数"])}"
        ret["登録メンバー"] = "、".join(lookup.internal.get_teammates(g.params["player_name"]))

    badge_status = compose.badge.status(data["ゲーム数"], data["win"])
    ret["検索範囲"] = compose.text_item.search_range(time_pattern="time")
    ret["集計範囲"] = str(compose.text_item.aggregation_range(game_info))
    ret["特記事項"] = "、".join(compose.text_item.remarks())
    ret["検索ワード"] = compose.text_item.search_word()
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
    # df = pd.DataFrame.from_dict(data, orient="index")

    ret["通算ポイント"] = f"{data["通算ポイント"]:+.1f}pt".replace("-", "▲")
    ret["平均ポイント"] = f"{data["平均ポイント"]:+.1f}pt".replace("-", "▲")
    ret["平均順位"] = f"{data["平均順位"]:1.2f}"
    if g.params.get("individual") and g.adapter.conf.badge_grade:
        ret["段位"] = compose.badge.grade(g.params["player_name"])
    ret["_blank2"] = True
    ret["1位"] = f"{data["1位"]:2} 回 ({data["1位率"]:6.2f}%)"
    ret["2位"] = f"{data["2位"]:2} 回 ({data["2位率"]:6.2f}%)"
    ret["3位"] = f"{data["3位"]:2} 回 ({data["3位率"]:6.2f}%)"
    ret["4位"] = f"{data["4位"]:2} 回 ({data["4位率"]:6.2f}%)"
    ret["トビ"] = f"{data["トビ"]:2} 回 ({data["トビ率"]:6.2f}%)"
    ret["役満"] = f"{data["役満和了"]:2} 回 ({data["役満和了率"]:6.2f}%)"

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
    work_text = textwrap.dedent(f"""\
        連続トップ：{current_data(data["c_top"])} ({max_data(data["連続トップ"], data["c_top"])})
        連続連対：{current_data(data["c_top2"])} ({max_data(data["連続連対"], data["c_top2"])})
        連続ラス回避：{current_data(data["c_top3"])} ({max_data(data["連続ラス回避"], data["c_top3"])})
        最大素点：{data["最大素点"] * 100}点
        最大獲得ポイント：{data["最大獲得ポイント"]}pt
    """).replace("-", "▲").replace("*****", "-----")
    ret["ベストレコード"] = textwrap.indent(work_text, "\t")

    work_text = textwrap.dedent(f"""\
        連続ラス：{current_data(data["c_low4"])} ({max_data(data["連続ラス"], data["c_low4"])})
        連続逆連対：{current_data(data["c_low2"])} ({max_data(data["連続逆連対"], data["c_low2"])})
        連続トップなし：{current_data(data["c_low"])} ({max_data(data["連続トップなし"], data["c_low"])})
        最小素点：{data["最小素点"] * 100}点
        最小獲得ポイント：{data["最小獲得ポイント"]}pt
    """).replace("-", "▲").replace("*****", "-----")
    ret["ワーストレコード"] = textwrap.indent(work_text, "\t")

    return ret


def get_results_simple(mapping_dict: dict) -> pd.DataFrame:
    """戦績(簡易)データ取得

    Args:
        mapping_dict (dict): 匿名化オプション用マップ

    Returns:
        pd.DataFrame: 戦績データ
    """

    target_player = formatter.name_replace(g.params["target_player"][0], add_mark=True)  # pylint: disable=unused-variable  # noqa: F841

    df = loader.read_data("SUMMARY_DETAILS").fillna(value="")
    if g.params.get("anonymous"):
        mapping_dict.update(formatter.anonymous_mapping(df["name"].unique().tolist(), len(mapping_dict)))
        df["name"] = df["name"].replace(mapping_dict)
        target_player = mapping_dict.get(target_player, target_player)

    df_data = df.query("name == @target_player")
    df_data["seat"] = df_data.apply(lambda v: ["東家", "南家", "西家", "北家"][(v["seat"] - 1)], axis=1)
    df_data["rpoint"] = df_data["rpoint"] * 100
    pd.options.mode.copy_on_write = True
    if g.params.get("individual"):
        df_data.loc[:, "備考"] = np.where(df_data["guest_count"] >= 2, "2ゲスト戦", "")
    else:
        df_data.loc[:, "備考"] = np.where(df_data["same_team"] == 1, "チーム同卓", "")
    df_data = formatter.df_rename(df_data.filter(items=["playtime", "seat", "rank", "rpoint", "point", "grandslam", "備考"]), short=False)

    return df_data


def get_results_details(mapping_dict: dict) -> pd.DataFrame:
    """戦績(詳細)データ取得

    Args:
        mapping_dict (dict): 匿名化オプション用マップ

    Returns:
        pd.DataFrame: 戦績データ
    """

    target_player = formatter.name_replace(g.params["target_player"][0], add_mark=True)  # pylint: disable=unused-variable  # noqa: F841

    df = loader.read_data("SUMMARY_DETAILS2").fillna(value="")
    if g.params.get("anonymous"):
        name_list: list = []
        name_list.extend(df["p1_name"].unique().tolist())
        name_list.extend(df["p2_name"].unique().tolist())
        name_list.extend(df["p3_name"].unique().tolist())
        name_list.extend(df["p4_name"].unique().tolist())
        mapping_dict.update(formatter.anonymous_mapping(list(set(name_list)), len(mapping_dict)))
        df["p1_name"] = df["p1_name"].replace(mapping_dict)
        df["p2_name"] = df["p2_name"].replace(mapping_dict)
        df["p3_name"] = df["p3_name"].replace(mapping_dict)
        df["p4_name"] = df["p4_name"].replace(mapping_dict)
        target_player = mapping_dict.get(target_player, target_player)

    df_data = df.query("p1_name == @target_player or p2_name == @target_player or p3_name == @target_player or p4_name == @target_player")

    pd.options.mode.copy_on_write = True
    if g.params.get("individual"):
        df_data.loc[:, "備考"] = np.where(df_data["guest_count"] >= 2, "2ゲスト戦", "")
    else:
        df_data.loc[:, "備考"] = np.where(df_data["same_team"] == 1, "チーム同卓", "")
    df_data = formatter.df_rename(df_data.drop(columns=["guest_count", "same_team"]))

    return df_data


def get_versus_matrix(mapping_dict: dict) -> str:
    """対戦結果データ出力用メッセージ生成

    Returns:
        str: 出力メッセージ
    """

    ret: str = ""
    df = loader.read_data("SUMMARY_VERSUS_MATRIX")

    if g.params.get("anonymous"):
        mapping_dict.update(formatter.anonymous_mapping(df["vs_name"].unique().tolist(), len(mapping_dict)))
        df["my_name"] = df["my_name"].replace(mapping_dict)
        df["vs_name"] = df["vs_name"].replace(mapping_dict)

    max_len = textutil.count_padding(df["vs_name"].unique().tolist())

    for _, r in df.iterrows():
        padding = max_len - textutil.len_count(r["vs_name"])
        ret += f"\t{r["vs_name"]}{" " * padding} ："
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
            case k if str(k).startswith("_blank"):
                msg += "\n"
            case "title":
                msg += f"{v}\n"
            case _:
                msg += f"{k}：{v}\n"

    return textwrap.indent(msg.strip(), "\t")
