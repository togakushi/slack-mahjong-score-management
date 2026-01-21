"""
libs/commands/results/detail.py
"""

import textwrap
from typing import TYPE_CHECKING, cast

import numpy as np
import pandas as pd
from table2ascii import Alignment, PresetStyle, table2ascii

import libs.global_value as g
from cls.stats import StatsInfo
from libs.data import loader
from libs.datamodels import GameInfo
from libs.functions import compose, message
from libs.types import StyleOptions
from libs.utils import converter, formatter

if TYPE_CHECKING:
    from integrations.protocols import MessageParserProtocol
    from libs.types import MessageType


def aggregation(m: "MessageParserProtocol"):
    """成績詳細を集計

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    # --- パラメータ更新
    g.params.update({"guest_skip": g.params["guest_skip2"]})  # 検索動作を合わせる

    if rule_version := g.params.get("rule_version"):
        g.params.update(
            {
                "mode": int(g.cfg.rule.to_dict(rule_version).get("mode", 4)),
                "rule_version": str(g.cfg.rule.to_dict(rule_version).get("rule_version", "")),
                "origin_point": int(g.cfg.rule.to_dict(rule_version).get("origin_point", 250)),
                "return_point": int(g.cfg.rule.to_dict(rule_version).get("return_point", 300)),
            }
        )
        if (target_mode := g.params.get("target_mode")) and target_mode != g.cfg.rule.get_mode(rule_version):
            m.post.headline = {"集計矛盾検出": message.random_reply(m, "rule_mismatch")}
            m.status.result = False
            return
    if g.params["player_name"] in g.cfg.team.lists:
        g.params.update({"individual": False})
    elif g.params["player_name"] in g.cfg.member.lists:
        g.params.update({"individual": True})

    # --- データ収集
    game_info = GameInfo()
    msg_data: dict = {}
    mapping_dict: dict = {}

    # タイトル
    if g.params.get("individual"):
        title = "個人成績詳細"
    else:
        title = "チーム成績詳細"

    if game_info.count == 0:
        if g.params.get("individual"):
            msg_data["検索範囲"] = f"{compose.text_item.search_range(time_pattern='time')}"
            msg_data["特記事項"] = "、".join(compose.text_item.remarks())
            msg_data["検索ワード"] = compose.text_item.search_word()
            msg_data["対戦数"] = f"0 戦 (0 勝 0 敗 0 分) {compose.badge.status(0, 0)}"
            m.post.headline = {title: message_build(msg_data)}
        else:
            m.post.headline = {title: "登録されていないチームです。"}
        m.status.result = False
        return

    stats = StatsInfo()
    stats.read(cast(dict, g.params))

    if stats.result_df.empty or stats.record_df.empty:
        m.post.headline = {title: message.random_reply(m, "no_target")}
        m.status.result = False
        return

    player_name = formatter.name_replace(g.params["player_name"], add_mark=True)
    if g.params.get("anonymous"):
        mapping_dict = formatter.anonymous_mapping(stats.result_df["name"].unique().tolist())
        stats.result_df["name"] = stats.result_df["name"].replace(mapping_dict)
        player_name = mapping_dict[player_name]

    # --- 表示内容
    msg_data.update(get_headline(stats, game_info, player_name))
    msg_data.update(get_totalization(stats))
    mode = g.params.get("mode", 4)

    # 統計
    seat_data = pd.DataFrame(
        {  # 座席データ
            "席": ["東家", "南家", "西家", "北家"][:mode],
            "順位分布": stats.rank_distr_list2,
            "平均順位": [f"{x:.2f}".replace("0.00", "-.--") for x in stats.rank_avg_list],
            "トビ": stats.flying_list,
            "役満和了": stats.yakuman_list,
        }
    )

    if g.cfg.mahjong.ignore_flying or g.cfg.dropitems.results & g.cfg.dropitems.flying:
        seat_data.drop(columns=["トビ"], inplace=True)
    if g.cfg.dropitems.results & g.cfg.dropitems.yakuman:
        seat_data.drop(columns=["役満和了"], inplace=True)

    if mode == 3:
        balance_data = textwrap.dedent(
            f"""\
            全体：{stats.seat0.avg_balance("all"):+.1f}点
            1着終了時：{stats.seat0.avg_balance("rank1"):+.1f}点
            2着終了時：{stats.seat0.avg_balance("rank2"):+.1f}点
            3着終了時：{stats.seat0.avg_balance("rank3"):+.1f}点
            """.replace("+0.0点", "記録なし")
        ).replace("-", "▲")
    else:
        balance_data = textwrap.dedent(
            f"""\
            全体：{stats.seat0.avg_balance("all"):+.1f}点
            連対時：{stats.seat0.avg_balance("top2"):+.1f}点
            逆連対時：{stats.seat0.avg_balance("lose2"):+.1f}点
            1着終了時：{stats.seat0.avg_balance("rank1"):+.1f}点
            2着終了時：{stats.seat0.avg_balance("rank2"):+.1f}点
            3着終了時：{stats.seat0.avg_balance("rank3"):+.1f}点
            4着終了時：{stats.seat0.avg_balance("rank4"):+.1f}点
            """.replace("+0.0点", "記録なし")
        ).replace("-", "▲")

    if g.params.get("statistics"):
        m.set_data(seat_data, StyleOptions(title="座席データ"))
        m.set_data(stats.seat0.best_record(), StyleOptions(title="ベストレコード"))
        m.set_data(stats.seat0.worst_record(), StyleOptions(title="ワーストレコード"))
        m.set_data(textwrap.indent(balance_data.strip(), "\t"), StyleOptions(title="平均収支"))

    # レギュレーション
    remarks_df = loader.read_data("REMARKS_INFO")
    count_df = remarks_df.groupby("matter").agg(matter_count=("matter", "count"), ex_total=("ex_point", "sum"), type=("type", "max"))
    count_df["matter"] = count_df.index

    if not g.cfg.dropitems.results & g.cfg.dropitems.yakuman:
        work_df = count_df.query("type == 0").filter(items=["matter", "matter_count"])
        m.set_data(formatter.df_rename(work_df, StyleOptions(rename_type=StyleOptions.DataKind.REMARKS_YAKUMAN)), StyleOptions(title="役満和了"))

    if not g.cfg.dropitems.results & g.cfg.dropitems.regulation:
        if g.params.get("individual"):
            work_df = count_df.query("type == 2").filter(items=["matter", "matter_count", "ex_total"])
        else:
            work_df = count_df.query("type == 2 or type == 3").filter(items=["matter", "matter_count", "ex_total"])
        m.set_data(formatter.df_rename(work_df, StyleOptions(rename_type=StyleOptions.DataKind.REMARKS_REGULATION)), StyleOptions(title="卓外清算"))

    if not g.cfg.dropitems.results & g.cfg.dropitems.other:
        work_df = count_df.query("type == 1").filter(items=["matter", "matter_count"])
        m.set_data(formatter.df_rename(work_df, StyleOptions(rename_type=StyleOptions.DataKind.REMARKS_OTHER)), StyleOptions(title="その他"))

    # 戦績
    if g.params.get("game_results"):
        if g.params.get("verbose"):
            m.set_data(get_results_details(mapping_dict), StyleOptions(title="戦績"))
        else:
            m.set_data(get_results_simple(mapping_dict), StyleOptions(title="戦績"))

    if g.params.get("versus_matrix"):
        m.set_data(get_versus_matrix(mapping_dict), StyleOptions(title="対戦結果"))

    # 非表示項目を除外
    m.post.message = [(data, options) for data, options in m.post.message if options.title not in g.cfg.dropitems.results]

    m.post.headline = {title: message_build(msg_data)}


def comparison(m: "MessageParserProtocol"):
    """成績詳細を比較

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    # 検索動作を合わせる
    g.params.update({"guest_skip": g.params["guest_skip2"]})

    if g.params["player_name"] in g.cfg.team.lists:
        g.params.update({"individual": False})
    elif g.params["player_name"] in g.cfg.member.lists:
        g.params.update({"individual": True})

    # データ収集
    data: "MessageType"
    game_info = GameInfo()

    # タイトル
    title = "成績詳細比較"
    if game_info:
        m.post.headline = {title: message.header(game_info, m, "", 1)}
    else:
        m.post.headline = {"0": message.random_reply(m, "no_hits")}
        m.status.result = False
        return

    stats_df = pd.DataFrame()
    x_result_df = loader.read_data("RESULTS_INFO")
    x_record_df = loader.read_data("RECORD_INFO")
    for name in x_result_df.query("id==0").sort_values("total_point", ascending=False)["name"]:
        work_stats = StatsInfo()
        work_params = g.params.copy()
        work_params["player_name"] = name
        work_stats.set_parameter(**work_params)
        work_stats.set_data(x_result_df.query("name == @name"))
        work_stats.set_data(x_record_df.query("name == @name"))
        stats_df = pd.concat([stats_df, work_stats.summary])

    if g.params.get("anonymous"):
        mapping_dict = formatter.anonymous_mapping(stats_df["name"].unique().tolist())
        stats_df["name"] = stats_df["name"].replace(mapping_dict)

    if stats_df.empty:
        m.post.headline = {"0": message.random_reply(m, "no_target")}
        m.status.result = False
        return

    # 非表示項目
    stats_df = stats_df.drop(columns=[x for x in g.cfg.dropitems.results if x in stats_df.columns.to_list()])
    if g.cfg.mahjong.ignore_flying or g.cfg.dropitems.results & g.cfg.dropitems.flying:
        stats_df = stats_df.drop(columns=["flying_rate-count"])
    if g.cfg.dropitems.results & g.cfg.dropitems.yakuman:
        stats_df = stats_df.drop(columns=["yakuman_rate-count"])

    # 出力
    options: StyleOptions = StyleOptions(
        title=title,
        base_name=title,
        show_index=True,
        codeblock=True,
        transpose=True,
    )

    match cast(str, g.params.get("format", "default")).lower():
        case "csv":
            options.format_type = "csv"
            data = converter.save_output(stats_df, options, m.post.headline)
        case "text" | "txt":
            options.format_type = "txt"
            data = converter.save_output(stats_df, options, m.post.headline)
        case _:
            options.key_title = False
            data = formatter.df_rename(stats_df, options).T

    m.set_data(data, options)
    m.post.thread = True


def get_headline(data: StatsInfo, game_info: GameInfo, player_name: str) -> dict:
    """ヘッダメッセージ生成

    Args:
        data (dict): 生成内容が格納された辞書
        game_info (GameInfo): ゲーム集計情報
        player_name (str): プレイヤー名

    Returns:
        dict: 集計データ
    """

    ret: dict = {}

    if g.params.get("individual"):
        ret["プレイヤー名"] = f"{player_name} {compose.badge.degree(data.seat0.count)}"
        if team_name := g.cfg.team.which(g.params["player_name"]):
            ret["所属チーム"] = team_name
    else:
        ret["チーム名"] = f"{g.params['player_name']} {compose.badge.degree(data.seat0.count)}"
        ret["登録メンバー"] = "、".join(g.cfg.team.member(g.params["player_name"]))

    badge_status = compose.badge.status(data.seat0.count, data.seat0.win)
    ret["検索範囲"] = compose.text_item.search_range(time_pattern="time")
    ret["集計範囲"] = str(compose.text_item.aggregation_range(game_info))
    ret["特記事項"] = "、".join(compose.text_item.remarks())
    ret["検索ワード"] = compose.text_item.search_word()
    ret["対戦数"] = f"{data.seat0.war_record()} {badge_status}"
    ret["_blank1"] = True

    return ret


def get_totalization(data: StatsInfo) -> dict:
    """集計トータルメッセージ生成

    Args:
        data (StatsInfo): 成績情報

    Returns:
        dict: 生成メッセージ
    """

    ret: dict = {}

    ret["通算ポイント"] = f"{data.seat0.total_point:+.1f}pt".replace("-", "▲")
    ret["平均ポイント"] = f"{data.seat0.avg_point:+.1f}pt".replace("-", "▲")
    ret["平均順位"] = f"{data.seat0.rank_avg:1.2f}"
    if g.params.get("individual") and g.adapter.conf.badge_grade:
        ret["段位"] = compose.badge.grade(g.params["player_name"])
    ret["_blank2"] = True
    ret["1位"] = f"{data.seat0.rank1:2} 回 ({data.seat0.rank1_rate:7.2%})"
    ret["2位"] = f"{data.seat0.rank2:2} 回 ({data.seat0.rank2_rate:7.2%})"
    ret["3位"] = f"{data.seat0.rank3:2} 回 ({data.seat0.rank3_rate:7.2%})"
    if g.params.get("mode", 4) == 4:
        ret["4位"] = f"{data.seat0.rank4:2} 回 ({data.seat0.rank4_rate:7.2%})"
    ret["トビ"] = f"{data.seat0.flying:2} 回 ({data.seat0.flying_rate:7.2%})"
    ret["役満"] = f"{data.seat0.yakuman:2} 回 ({data.seat0.yakuman_rate:7.2%})"

    return ret


def get_results_simple(mapping_dict: dict) -> pd.DataFrame:
    """戦績(簡易)データ取得

    Args:
        mapping_dict (dict): 匿名化オプション用マップ

    Returns:
        pd.DataFrame: 戦績データ
    """

    target_player = formatter.name_replace(g.params["target_player"][0], add_mark=True)

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
    df_data = formatter.df_rename(df_data.filter(items=["playtime", "seat", "rank", "rpoint", "point", "remarks", "備考"]), StyleOptions())

    return df_data


def get_results_details(mapping_dict: dict) -> pd.DataFrame:
    """戦績(詳細)データ取得

    Args:
        mapping_dict (dict): 匿名化オプション用マップ

    Returns:
        pd.DataFrame: 戦績データ
    """

    target_player = formatter.name_replace(g.params["target_player"][0], add_mark=True)  # noqa: F841

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

    match g.params.get("mode"):
        case 3:
            df.drop(columns=["p4_name", "p4_rpoint", "p4_rank", "p4_point", "p4_remarks"], inplace=True)
            df_data = df.query(
                "p1_name == @target_player or p2_name == @target_player or p3_name == @target_player"  # noqa: E501
            )
        case 4:
            df_data = df.query(
                "p1_name == @target_player or p2_name == @target_player or p3_name == @target_player or p4_name == @target_player"  # noqa: E501
            )
        case _:
            return pd.DataFrame()

    pd.options.mode.copy_on_write = True
    if g.params.get("individual"):
        df_data.loc[:, "備考"] = np.where(df_data["guest_count"] >= 2, "2ゲスト戦", "")
    else:
        df_data.loc[:, "備考"] = np.where(df_data["same_team"] == 1, "チーム同卓", "")
    df_data = formatter.df_rename(df_data.drop(columns=["guest_count", "same_team"]), StyleOptions())

    return df_data


def get_versus_matrix(mapping_dict: dict) -> str:
    """対戦結果データ出力用メッセージ生成

    Returns:
        str: 出力メッセージ
    """

    df = loader.read_data("SUMMARY_VERSUS_MATRIX")

    if df.empty:
        return ""

    if g.params.get("anonymous"):
        mapping_dict.update(formatter.anonymous_mapping(df["vs_name"].unique().tolist(), len(mapping_dict)))
        df["my_name"] = df["my_name"].replace(mapping_dict)
        df["vs_name"] = df["vs_name"].replace(mapping_dict)

    data_list: list = []
    for _, r in df.iterrows():
        data_list.append([r["vs_name"], f"{r['game']} 戦", f"{r['win']} 勝", f"{r['lose']} 敗", f"({r['win%']:6.2f}%)"])

    output = table2ascii(
        # header=["対戦相手", "ゲーム数", "勝", "負", "勝率"],
        body=data_list,
        alignments=[Alignment.LEFT, Alignment.RIGHT, Alignment.RIGHT, Alignment.RIGHT, Alignment.RIGHT],
        style=PresetStyle.ascii_borderless,
        cell_padding=0,
    )

    return output


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
