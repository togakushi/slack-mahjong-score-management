import re
import textwrap

import pandas as pd

import global_value as g
from lib import command as c
from lib import database as d
from lib import function as f


def aggregation():
    """
    個人/チーム成績詳細を集計して返す

    Returns
    -------
    msg1 : text
        slackにpostするデータ

    msg2 : dict
        slackにpostするデータ(スレッドに返す)
    """

    # 検索動作を合わせる
    g.opt.guest_skip = g.opt.guest_skip2

    if g.prm.player_name in [x["team"] for x in g.team_list]:
        g.opt.individual = False
    elif g.prm.player_name in g.member_list:
        g.opt.individual = True

    # --- データ収集
    game_info = d.aggregate.game_info()
    df_grandslam = d.aggregate.remark_count("grandslam")
    df_regulations = d.aggregate.remark_count("regulation")

    msg_data = {}
    if g.opt.individual:
        msg_data["title"] = "*【個人成績】*"
        msg_data["プレイヤー名"] = f"{g.prm.player_name} {f.common.badge_degree(0)}"
        team = c.team.which_team(g.prm.player_name)
        if team:
            msg_data["所属チーム"] = team
    else:
        member = c.team.get_teammates()
        if member:
            msg_data["title"] = "*【チーム成績】*"
            msg_data["チーム名"] = f"{g.prm.player_name} {f.common.badge_degree(0)}"
            msg_data["登録メンバー"] = "、".join(member)
        else:
            return ("登録されていないチームです", {})

    if game_info["game_count"] == 0:
        msg_data["検索範囲"] = f"{g.prm.starttime_hms} ～ {g.prm.endtime_hms}"
        msg_data["特記事項"] = "、".join(f.message.remarks())
        msg_data["検索ワード"] = f.message.search_word()
        msg_data["対戦数"] = f"0 戦 (0 勝 0 敗 0 分) {f.common.badge_status(0, 0)}"

        return (message_build(msg_data), {})

    result_df = d.aggregate.game_results()
    record_df = d.aggregate.ranking_record()
    result_df = pd.merge(
        result_df, record_df,
        on=["name", "表示名"],
        suffixes=["", "_x"]
    )
    data = result_df.to_dict(orient="records")[0]

    # --- 表示内容
    msg2 = {}
    badge_degree = f.common.badge_degree(data["ゲーム数"])
    badge_status = f.common.badge_status(data["ゲーム数"], data["win"])
    if g.opt.individual:  # degree更新
        msg_data["プレイヤー名"] = f"{g.prm.player_name} {badge_degree}"
    else:
        msg_data["チーム名"] = f"{g.prm.player_name} {badge_degree}"

    msg_data["検索範囲"] = f.message.item_search_range(kind="str").strip()
    msg_data["集計範囲"] = f.message.item_aggregation_range(game_info, kind="str").strip()
    msg_data["特記事項"] = "、".join(f.message.remarks())
    msg_data["検索ワード"] = f.message.search_word()
    msg_data["対戦数"] = f"{data["ゲーム数"]} 戦 ({data["win"]} 勝 {data["lose"]} 敗 {data["draw"]} 分) {badge_status}"
    msg_data["_blank1"] = True

    # --- 成績データ
    if g.cfg.config["mahjong"].getboolean("ignore_flying", False):
        g.cfg.dropitems.results.append("トビ")

    msg_data["通算ポイント"] = f"{data['通算ポイント']:+.1f}pt".replace("-", "▲")
    msg_data["平均ポイント"] = f"{data['平均ポイント']:+.1f}pt".replace("-", "▲")
    msg_data["平均順位"] = f"{data['平均順位']:1.2f}"
    msg_data["1位"] = f"{data['1位']:2} 回 ({data['1位率']:6.2f}%)"
    msg_data["2位"] = f"{data['2位']:2} 回 ({data['2位率']:6.2f}%)"
    msg_data["3位"] = f"{data['3位']:2} 回 ({data['3位率']:6.2f}%)"
    msg_data["4位"] = f"{data['4位']:2} 回 ({data['4位率']:6.2f}%)"
    msg_data["トビ"] = f"{data['トビ']:2} 回 ({data['トビ率']:6.2f}%)"
    msg_data["役満"] = f"{data['役満和了']:2} 回 ({data['役満和了率']:6.2f}%)"

    # --- 座席データ
    msg2["座席データ"] = textwrap.dedent(f"""
        *【座席データ】*
        \t# 席：順位分布(平均順位) / トビ / 役満 #
        \t{data["東家-順位分布"]:22s} / {data["東家-トビ"]} / {data["東家-役満和了"]}
        \t{data["南家-順位分布"]:22s} / {data["南家-トビ"]} / {data["南家-役満和了"]}
        \t{data["西家-順位分布"]:22s} / {data["西家-トビ"]} / {data["西家-役満和了"]}
        \t{data["北家-順位分布"]:22s} / {data["北家-トビ"]} / {data["北家-役満和了"]}
    """).replace("0.00", "-.--")

    # --- 記録
    msg2["ベストレコード"] = textwrap.dedent(f"""
        *【ベストレコード】*
        \t連続トップ：{data["連続トップ"]} 連続
        \t連続連対：{data["連続連対"]} 連続
        \t連続ラス回避：{data["連続ラス回避"]} 連続
        \t最大素点：{data["最大素点"] * 100}点
        \t最大獲得ポイント：{data["最大獲得ポイント"]}pt
    """).replace("-", "▲").replace("：0 連続", "：----").replace("：1 連続", "：----")

    msg2["ワーストレコード"] = textwrap.dedent(f"""
        *【ワーストレコード】*
        \t連続ラス：{data['連続ラス']} 連続
        \t連続逆連対：{data['連続逆連対']} 連続
        \t連続トップなし：{data['連続トップなし']} 連続
        \t最小素点：{data['最小素点'] * 100}点
        \t最小獲得ポイント：{data['最小獲得ポイント']}pt
    """).replace("-", "▲").replace("：0 連続", "：----").replace("：1 連続", "：----")

    if not df_grandslam.empty:
        msg2["役満和了"] = "\n*【役満和了】*\n"
        for x in df_grandslam.itertuples():
            msg2["役満和了"] += f"\t{x.matter}\t{x.count}回\n"

    if not df_regulations.query("type == 1").empty:
        msg2["卓外ポイント"] = "\n*【卓外ポイント】*\n"
        for x in df_regulations.query("type == 1").itertuples():
            ex_point = str(x.ex_point).replace("-", "▲")
            msg2["卓外ポイント"] += f"\t{x.matter}\t{x.count}回 ({ex_point}pt)\n"

    if not df_regulations.query("type != 1").empty:
        msg2["その他"] = "\n*【その他】*\n"
        for x in df_regulations.query("type != 1").itertuples():
            msg2["その他"] += f"\t{x.matter}\t{x.count}回\n"

    # --- 戦績
    if g.opt.game_results:
        msg2["戦績"] = "\n*【戦績】*\n"
        data = {}
        target_player = g.opt.target_player[0]  # noqa: F841
        df = d.aggregate.game_details()

        if g.opt.verbose:
            data["p0"] = df.filter(items=["playtime", "guest_count"]).drop_duplicates().set_index("playtime")
            for idx, prefix in enumerate(["p1", "p2", "p3", "p4"]):
                data[prefix] = df.query("seat == @idx + 1").filter(
                    items=["playtime", "表示名", "rpoint", "rank", "point", "grandslam", "name"]
                ).rename(
                    columns={
                        "name": f"{prefix}_x",
                        "表示名": f"{prefix}_name",
                        "rpoint": f"{prefix}_rpoint",
                        "rank": f"{prefix}_rank",
                        "point": f"{prefix}_point",
                        "grandslam": f"{prefix}_gs",
                    }
                ).set_index("playtime")

            df_data = pd.concat([data["p1"], data["p2"], data["p3"], data["p4"], data["p0"]], axis=1)
            df_data = df_data.query("p1_x == @target_player or p2_x == @target_player or p3_x == @target_player or p4_x == @target_player")

            for x in df_data.itertuples():
                vs_guest = ""
                if x.guest_count >= 2:
                    vs_guest = "(2ゲスト戦)"
                msg2["戦績"] += textwrap.dedent(
                    """
                    {} {}
                    \t東家：{} {}位 {:7d}点 ({:6.1f}pt) {}
                    \t南家：{} {}位 {:7d}点 ({:6.1f}pt) {}
                    \t西家：{} {}位 {:7d}点 ({:6.1f}pt) {}
                    \t北家：{} {}位 {:7d}点 ({:6.1f}pt) {}"""
                ).format(
                    x.Index.replace("-", "/"), vs_guest,
                    x.p1_name, x.p1_rank, int(x.p1_rpoint) * 100, x.p1_point, x.p1_gs,
                    x.p2_name, x.p2_rank, int(x.p2_rpoint) * 100, x.p2_point, x.p2_gs,
                    x.p3_name, x.p3_rank, int(x.p3_rpoint) * 100, x.p3_point, x.p3_gs,
                    x.p4_name, x.p4_rank, int(x.p4_rpoint) * 100, x.p4_point, x.p4_gs,
                ).replace("-", "▲")
        else:
            df_data = df.query("name == @target_player").set_index("playtime")
            for x in df_data.itertuples():
                vs_guest = ""
                if x.guest_count >= 2:
                    vs_guest = "*"
                msg2["戦績"] += "\t{}{}  {}位 {:7d}点 ({:6.1f}pt) {}\n".format(
                    vs_guest, x.Index.replace("-", "/"),
                    x.rank, int(x.rpoint) * 100, x.point, x.grandslam,
                ).replace("-", "▲")

    # --- 対戦結果
    if g.opt.versus_matrix:
        df = d.aggregate.versus_matrix()
        msg2["対戦"] = "\n*【対戦結果】*\n"
        for _, r in df.iterrows():
            msg2["対戦"] += f"\t{r['vs_表示名']}：{r['game']} 戦 {r['win']} 勝 {r['lose']} 敗 ({r['win%']:6.2f}%)\n"

    # 非表示項目
    if "トビ" in g.cfg.dropitems.results:
        msg2["座席データ"] = re.sub(r"/ .* /", "/", msg2["座席データ"], flags=re.MULTILINE)
    if "役満" in g.cfg.dropitems.results:
        msg2["座席データ"] = msg2["座席データ"].replace(" / 役満", "")
        msg2["座席データ"] = re.sub(r" / [0-9]+$", "", msg2["座席データ"], flags=re.MULTILINE)
        msg2.pop("役満和了") if "役満和了" in msg2 else None

    if not g.opt.statistics:  # 統計
        for k in ("座席データ", "ベストレコード", "ワーストレコード"):
            msg2.pop(k) if k in msg2 else None

    for k in list(msg2.keys()):
        if k in g.cfg.dropitems.results:
            msg2.pop(k)

    return (message_build(msg_data), msg2)


def message_build(data: dict):
    """
    表示する内容をテキストに起こす
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
