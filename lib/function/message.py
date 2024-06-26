import random

import lib.function as f
from lib.function import global_value as g


def help(command):
    """
    スラッシュコマンド用ヘルプ
    """

    msg = f"```使い方："
    msg += f"\n\t{command} help          このメッセージ"
    msg += f"\n\t{command} results       成績出力"
    msg += f"\n\t{command} ranking       ランキング出力"
    msg += f"\n\t{command} graph         ポイント推移グラフを表示"
    msg += f"\n\t{command} report        レポート表示"
    msg += f"\n\t{command} check         データ突合"
    msg += f"\n\t{command} download      データベースダウンロード"
    msg += f"\n\t{command} member        登録されているメンバー"
    msg += f"\n\t{command} add | del     メンバーの追加/削除"
    msg += f"```"
    return(msg)


def help_message():
    """
    チャンネル内呼び出しキーワード用ヘルプ
    """

    results_option = f.configure.command_option_initialization("results")
    graph_option = f.configure.command_option_initialization("graph")
    ranking_option = f.configure.command_option_initialization("ranking")
    report_option = f.configure.command_option_initialization("report")

    msg = [
        "*機能呼び出し構文*",
        "\t`呼び出しキーワード [検索範囲] [対象メンバー] [オプション]`",

        "\n" + "-" * 30,

        "\n*成績サマリ*",
        f"\t呼び出しキーワード： {g.commandword['results']}",
        f"\t検索範囲デフォルト： {results_option['aggregation_range'][0]}",
        "\t詳細説明： https://github.com/togakushi/slack-mahjong-score-management/blob/main/docs/functions/summary.md",

        "\n*成績グラフ*",
        f"\t呼び出しキーワード： {g.commandword['graph']}",
        f"\t検索範囲デフォルト： {graph_option['aggregation_range'][0]}",
        "\t詳細説明： https://github.com/togakushi/slack-mahjong-score-management/blob/main/docs/functions/graph.md",

        "\n*ランキング*",
        f"\t呼び出しキーワード： {g.commandword['ranking']}",
        f"\t検索範囲デフォルト： {ranking_option['aggregation_range'][0]}",
        f"\t規定打数デフォルト： 全体ゲーム数 × {ranking_option['stipulated_rate']} ＋ 1",
        f"\t出力制限デフォルト： 上位 {ranking_option['ranked']} 名",
        "\t詳細説明： https://github.com/togakushi/slack-mahjong-score-management/blob/main/docs/functions/ranking.md",

        "\n*レポート*",
        f"\t呼び出しキーワード： {g.commandword['report']}",
        f"\t検索範囲デフォルト： {report_option['aggregation_range'][0]}",
        "\t詳細説明： https://github.com/togakushi/slack-mahjong-score-management/blob/main/docs/functions/report.md",

        "\n" + "-" * 30,

        "*オプション*",
        "\t詳細説明： https://github.com/togakushi/slack-mahjong-score-management/blob/main/docs/functions/argument_keyword.md",
    ]
    return("\n".join(msg))


def invalid_argument():
    """
    引数解析失敗時のメッセージ
    """

    msg = f"使い方が間違っています。"

    if g.config.has_section("custom_message"):
        key_list = []
        for i in g.config["custom_message"]:
            if i.startswith("invalid_argument"):
                key_list.append(i)
        if key_list:
            msg = g.config["custom_message"][random.choice(key_list)]

    return(msg)


def restricted_channel():
    """
    制限チャンネルでキーワードを検出したときのメッセージ
    """

    msg = f"この投稿はデータベースに反映されません。"

    if g.config.has_section("custom_message"):
        key_list = []
        for i in g.config["custom_message"]:
            if i.startswith("restricted_channel"):
                key_list.append(i)
        if key_list:
            msg = g.config["custom_message"][random.choice(key_list)]

    return(msg)


def invalid_score(user_id, rpoint_sum, correct_score):
    """
    ゲーム終了時の素点合計が配給原点合計と異なる場合の警告メッセージ
    """

    rpoint_diff = abs(correct_score - rpoint_sum)
    msg = f"素点合計： {rpoint_sum}\n点数差分： {rpoint_diff}"

    if g.config.has_section("custom_message"):
        key_list = []
        for i in g.config["custom_message"]:
            if i.startswith("invalid_score"):
                key_list.append(i)
        if key_list:
            msg = g.config["custom_message"][random.choice(key_list)]

    return(f"<@{user_id}> " + msg.format(
        rpoint_diff = rpoint_diff * 100,
        rpoint_sum = rpoint_sum * 100,
    ))


def no_hits(argument, command_option):
    """
    指定範囲に記録用キーワードが見つからなかった場合のメッセージ
    """

    target_days, _, _, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)
    if not(starttime and endtime):
        return(invalid_argument)

    keyword = g.config["search"].get("keyword", "終局")
    start = starttime.strftime("%Y/%m/%d %H:%M")
    end = endtime.strftime("%Y/%m/%d %H:%M")
    msg = f"{start} ～ {end} に≪{keyword}≫はありません。"

    if g.config.has_section("custom_message"):
        key_list = []
        for i in g.config["custom_message"]:
            if i.startswith("no_hits"):
                key_list.append(i)
        if key_list:
            msg = g.config["custom_message"][random.choice(key_list)]

    return(msg.format(keyword = keyword, start = start, end = end))


def remarks(command_option):
    """
    引数で指定された集計方法を注記にまとめる
    """

    ret = ""
    remark = []

    if not command_option["guest_skip"]:
        remark.append("2ゲスト戦の結果を含む")
    if not command_option["unregistered_replace"]:
        remark.append("ゲスト置換なし("+ g.guest_mark + "：未登録プレイヤー)")
    if remark:
        ret = f"特記：" + "、".join(remark)

    return(ret)
