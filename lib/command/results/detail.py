"""
lib/command/results/detail.py
"""

import re
import textwrap

import pandas as pd

import lib.global_value as g
from lib import command as c
from lib import database as d
from lib import function as f


def aggregation():
    """個人/チーム成績詳細を集計して返す

    Returns:
        dict: slackにpostするデータ
    """

    # 検索動作を合わせる
    g.opt.guest_skip = g.opt.guest_skip2

    if g.prm.player_name in [x["team"] for x in g.team_list]:
        g.opt.individual = False
    elif g.prm.player_name in g.member_list:
        g.opt.individual = True

    if not g.opt.individual and not c.team.get_teammates():
        return ("登録されていないチームです", {})

    # --- データ収集
    msg_data: dict = {}
    game_info = d.aggregate.game_info()

    if game_info["game_count"] == 0:
        msg_data["検索範囲"] = f"{g.prm.starttime_hms} ～ {g.prm.endtime_hms}"
        msg_data["特記事項"] = "、".join(f.message.remarks())
        msg_data["検索ワード"] = f.message.search_word()
        msg_data["対戦数"] = f"0 戦 (0 勝 0 敗 0 分) {f.common.badge_status(0, 0)}"
        return (message_build(msg_data), {})

    if g.opt.anonymous:
        player_name = c.member.name_replace(g.prm.player_name, add_mark=True)
        for idx, name in enumerate(g.opt.target_player):
            g.opt.target_player[idx] = c.member.name_replace(name)
    else:
        player_name = c.member.name_replace(g.prm.player_name, add_mark=True)

    result_df = d.aggregate.game_results()
    record_df = d.aggregate.ranking_record()
    result_df = pd.merge(
        result_df, record_df,
        on=["name", "name"],
        suffixes=["", "_x"]
    )
    data = result_df.to_dict(orient="records")[0]

    # --- 表示内容
    msg_data.update(get_headline(data, game_info, player_name))
    msg_data.update(get_totalization(data))

    msg2: dict = {}
    msg2["座席データ"] = get_seat_data(data)
    msg2.update(get_record(data))  # ベスト/ワーストレコード
    msg2.update(get_regulations())  # レギュレーション

    if g.opt.game_results:  # 戦績
        msg2["戦績"] = get_game_results()

    if g.opt.versus_matrix:  # 対戦結果
        msg2["対戦"] = get_versus_matrix()

    # 非表示項目
    if g.cfg.config["mahjong"].getboolean("ignore_flying", False):
        g.cfg.dropitems.results.append("トビ")
    if "トビ" in g.cfg.dropitems.results:
        msg2["座席データ"] = re.sub(r"/ .* /", "/", msg2["座席データ"], flags=re.MULTILINE)
    if "役満" in g.cfg.dropitems.results:
        msg2["座席データ"] = msg2["座席データ"].replace(" / 役満", "")
        msg2["座席データ"] = re.sub(r" / [0-9]+$", "", msg2["座席データ"], flags=re.MULTILINE)
        msg2.pop("役満和了", None)

    if not g.opt.statistics:  # 統計
        for k in ("座席データ", "ベストレコード", "ワーストレコード"):
            msg2.pop(k, None)

    for k in list(msg2.keys()):
        if k in g.cfg.dropitems.results:
            msg2.pop(k)

    return (message_build(msg_data), msg2)


def get_headline(data, game_info, player_name):
    ret: dict = {}

    if g.opt.individual:
        ret["title"] = "*【個人成績】*"
        ret["プレイヤー名"] = f"{player_name} {f.common.badge_degree(data["ゲーム数"])}"
        team = c.team.which_team(g.prm.player_name)
        if team:
            ret["所属チーム"] = team
    else:
        ret["title"] = "*【チーム成績】*"
        ret["チーム名"] = f"{g.prm.player_name} {f.common.badge_degree(data["ゲーム数"])}"
        ret["登録メンバー"] = "、".join(c.team.get_teammates())

    badge_status = f.common.badge_status(data["ゲーム数"], data["win"])
    ret["検索範囲"] = f.message.item_search_range(kind="str").strip()
    ret["集計範囲"] = f.message.item_aggregation_range(game_info, kind="str").strip()
    ret["特記事項"] = "、".join(f.message.remarks())
    ret["検索ワード"] = f.message.search_word()
    ret["対戦数"] = f"{data["ゲーム数"]} 戦 ({data["win"]} 勝 {data["lose"]} 敗 {data["draw"]} 分) {badge_status}"
    ret["_blank1"] = True

    return (ret)


def get_totalization(data):
    ret: dict = {}

    ret["通算ポイント"] = f"{data['通算ポイント']:+.1f}pt".replace("-", "▲")
    ret["平均ポイント"] = f"{data['平均ポイント']:+.1f}pt".replace("-", "▲")
    ret["平均順位"] = f"{data['平均順位']:1.2f}"
    ret["1位"] = f"{data['1位']:2} 回 ({data['1位率']:6.2f}%)"
    ret["2位"] = f"{data['2位']:2} 回 ({data['2位率']:6.2f}%)"
    ret["3位"] = f"{data['3位']:2} 回 ({data['3位率']:6.2f}%)"
    ret["4位"] = f"{data['4位']:2} 回 ({data['4位率']:6.2f}%)"
    ret["トビ"] = f"{data['トビ']:2} 回 ({data['トビ率']:6.2f}%)"
    ret["役満"] = f"{data['役満和了']:2} 回 ({data['役満和了率']:6.2f}%)"

    return (ret)


def get_seat_data(data: dict):
    ret: str = textwrap.dedent(f"""\
        *【座席データ】*
        \t# 席：順位分布(平均順位) / トビ / 役満 #
        \t{data["東家-順位分布"]:22s} / {data["東家-トビ"]} / {data["東家-役満和了"]}
        \t{data["南家-順位分布"]:22s} / {data["南家-トビ"]} / {data["南家-役満和了"]}
        \t{data["西家-順位分布"]:22s} / {data["西家-トビ"]} / {data["西家-役満和了"]}
        \t{data["北家-順位分布"]:22s} / {data["北家-トビ"]} / {data["北家-役満和了"]}
    """).replace("0.00", "-.--")

    return (ret)


def get_record(data: dict):
    ret: dict = {}

    ret["ベストレコード"] = textwrap.dedent(f"""\
        *【ベストレコード】*
        \t連続トップ：{data["連続トップ"]} 連続
        \t連続連対：{data["連続連対"]} 連続
        \t連続ラス回避：{data["連続ラス回避"]} 連続
        \t最大素点：{data["最大素点"] * 100}点
        \t最大獲得ポイント：{data["最大獲得ポイント"]}pt
    """).replace("-", "▲").replace("：0 連続", "：----").replace("：1 連続", "：----")

    ret["ワーストレコード"] = textwrap.dedent(f"""\
        *【ワーストレコード】*
        \t連続ラス：{data['連続ラス']} 連続
        \t連続逆連対：{data['連続逆連対']} 連続
        \t連続トップなし：{data['連続トップなし']} 連続
        \t最小素点：{data['最小素点'] * 100}点
        \t最小獲得ポイント：{data['最小獲得ポイント']}pt
    """).replace("-", "▲").replace("：0 連続", "：----").replace("：1 連続", "：----")

    return (ret)


def get_regulations():
    df_grandslam = d.aggregate.remark_count("grandslam")
    df_regulations = d.aggregate.remark_count("regulation")

    ret: dict = {}

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

    return (ret)


def get_game_results():
    ret: str = "\n*【戦績】*\n"
    data: dict = {}
    target_player = c.member.name_replace(g.opt.target_player[0], add_mark=True)  # pylint: disable=unused-variable  # noqa: F841
    p_list: list = []
    df = d.common.read_data("lib/queries/summary/details.sql").fillna(value="")

    if g.opt.verbose:
        data["p0"] = df.filter(items=["playtime", "guest_count", "same_team"]).drop_duplicates().set_index("playtime")
        for idx, prefix in enumerate(["p1", "p2", "p3", "p4"]):  # pylint: disable=unused-variable  # noqa: F841
            tmp_df = df.query("seat == @idx + 1").filter(
                items=["playtime", "name", "rpoint", "rank", "point", "grandslam", "name"]
            )

            for x in tmp_df["name"].unique().tolist():
                if x not in p_list:
                    p_list.append(x)

            data[prefix] = tmp_df.rename(
                columns={
                    "name": f"{prefix}_name",
                    "rpoint": f"{prefix}_rpoint",
                    "rank": f"{prefix}_rank",
                    "point": f"{prefix}_point",
                    "grandslam": f"{prefix}_gs",
                }
            ).set_index("playtime")

        max_len = c.member.count_padding(p_list)
        df_data = pd.concat([data["p1"], data["p2"], data["p3"], data["p4"], data["p0"]], axis=1)
        df_data = df_data.query("p1_name == @target_player or p2_name == @target_player or p3_name == @target_player or p4_name == @target_player")

        for x in df_data.itertuples():
            vs_guest = ""
            if x.guest_count >= 2 and g.opt.individual:
                vs_guest = "(2ゲスト戦)"
            if x.same_team == 1 and not g.opt.individual:
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
                x.p1_name, " " * (max_len - f.common.len_count(x.p1_name)), x.p1_rank, int(x.p1_rpoint) * 100, x.p1_point, x.p1_gs,
                x.p2_name, " " * (max_len - f.common.len_count(x.p2_name)), x.p2_rank, int(x.p2_rpoint) * 100, x.p2_point, x.p2_gs,
                x.p3_name, " " * (max_len - f.common.len_count(x.p3_name)), x.p3_rank, int(x.p3_rpoint) * 100, x.p3_point, x.p3_gs,
                x.p4_name, " " * (max_len - f.common.len_count(x.p4_name)), x.p4_rank, int(x.p4_rpoint) * 100, x.p4_point, x.p4_gs,
            ).replace(" -", "▲")
    else:
        df_data = df.query("name == @target_player").set_index("playtime")
        for x in df_data.itertuples():
            vs_guest = ""
            if x.guest_count >= 2 and g.opt.individual:
                vs_guest = g.cfg.setting.guest_mark
            if x.same_team == 1 and not g.opt.individual:
                vs_guest = g.cfg.setting.guest_mark

            ret += "\t{}{}  {}位 {:8d}点 ({:7.1f}pt) {}\n".format(  # pylint: disable=consider-using-f-string
                vs_guest, x.Index.replace("-", "/"),
                x.rank, int(x.rpoint) * 100, x.point, x.grandslam,
            ).replace("-", "▲")

    return (ret)


def get_versus_matrix() -> str:
    """対戦結果を返す

    Returns:
        str: 集計結果
    """

    ret: str = "\n*【対戦結果】*\n"
    df = d.common.read_data("lib/queries/summary/versus_matrix.sql")
    max_len = c.member.count_padding(df["vs_name"].unique().tolist())

    for _, r in df.iterrows():
        padding = max_len - f.common.len_count(r["vs_name"])
        ret += f"\t{r["vs_name"]}{" " * padding} ： "
        ret += f"{r["game"]:3d} 戦 {r["win"]:3d} 勝 {r["lose"]:3d} 敗 ({r["win%"]:6.2f}%)\n"

    return (ret)


def message_build(data: dict):
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

    return (msg.strip())
