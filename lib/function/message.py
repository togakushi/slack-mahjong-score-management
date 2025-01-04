import random
import re
import textwrap

import global_value as g
from lib import function as f


def help(command):
    """
    スラッシュコマンド用ヘルプ
    """

    msg = "```使い方："
    msg += f"\n\t{command} help          このメッセージ"
    msg += "\n\t--- 成績管理 ---"
    msg += f"\n\t{command} results       成績出力"
    msg += f"\n\t{command} ranking       ランキング出力"
    msg += f"\n\t{command} graph         ポイント推移グラフを表示"
    msg += f"\n\t{command} report        レポート表示"
    msg += "\n\t--- データベース操作 ---"
    msg += f"\n\t{command} check         データ突合"
    msg += f"\n\t{command} download      データベースダウンロード"
    msg += "\n\t--- メンバー管理 ---"
    msg += f"\n\t{command} member        登録されているメンバー"
    msg += f"\n\t{command} add | del     メンバーの追加/削除"
    msg += "\n\t--- チーム管理 ---"
    msg += f"\n\t{command} team_create <チーム名>            チームの新規作成"
    msg += f"\n\t{command} team_del <チーム名>               チームの削除"
    msg += f"\n\t{command} team_add <チーム名> <メンバー名>  チームにメンバーを登録"
    msg += f"\n\t{command} team_remove <メンバー名>          指定したメンバーを未所属にする"
    msg += f"\n\t{command} team_list                         チーム名と所属メンバーを表示"
    msg += f"\n\t{command} team_clear                        チームデータをすべて削除"
    msg += "```"

    return (msg)


def help_message():
    """
    チャンネル内呼び出しキーワード用ヘルプ
    """

    results_option = f.configuration.command_option()
    results_option.initialization("results")
    graph_option = f.configuration.command_option()
    graph_option.initialization("graph")
    ranking_option = f.configuration.command_option()
    ranking_option.initialization("ranking")
    report_option = f.configuration.command_option()
    report_option.initialization("report")

    words = g.cfg.config["mahjong"].get("regulations_type2", None)
    if words:
        words_list = set([x.strip() for x in words.split(",")])
        meg_wordcount = "個別カウントワード： " + ", ".join(words_list)

    msg = textwrap.dedent(f"""
        *成績記録キーワード*
        \t{g.cfg.search.keyword}

        *機能呼び出し*
        \t`呼び出しキーワード [検索範囲] [対象メンバー] [オプション]`

        \t*成績サマリ*
        \t\t呼び出しキーワード： {g.cfg.cw.results}
        \t\t検索範囲デフォルト： {results_option.aggregation_range[0]}
        \t*成績グラフ*
        \t\t呼び出しキーワード： {g.cfg.cw.graph}
        \t\t検索範囲デフォルト： {graph_option.aggregation_range[0]}
        \t*ランキング*
        \t\t呼び出しキーワード： {g.cfg.cw.ranking}
        \t\t検索範囲デフォルト： {ranking_option.aggregation_range[0]}
        \t\t規定打数デフォルト： 全体ゲーム数 × {ranking_option.stipulated_rate} ＋ 1
        \t\t出力制限デフォルト： 上位 {ranking_option.ranked} 名
        \t*レポート*
        \t\t呼び出しキーワード： {g.cfg.cw.report}
        \t\t検索範囲デフォルト： {report_option.aggregation_range[0]}
        \t*メンバー一覧*
        \t\t呼び出しキーワード： {g.cfg.cw.member}
        \t*チーム一覧*
        \t\t呼び出しキーワード： {g.cfg.cw.team}

        \t*メモ*
        \t\t登録キーワード： {g.cfg.cw.remarks_word}
        {"\t\t" + meg_wordcount if words else ""}
    """)

    # 追加ルール（卓外ポイント）
    if g.cfg.config.has_section("regulations"):
        additional_rule = "\n\n*追加ルール*\n"
        for word, ex_point in g.cfg.config.items("regulations"):
            additional_rule += f"\t{word}： {ex_point}pt\n"
        msg += additional_rule

    # 検索範囲
    msg += "\n*検索範囲に指定できるキーワード*\n"
    for x in g.search_word.list().splitlines():
        msg += f"\t{x}\n"

    # 追加説明
    msg += textwrap.dedent("""
        *その他オプション詳細説明*
        \thttps://github.com/togakushi/slack-mahjong-score-management/blob/main/docs/functions/argument_keyword.md
    """)

    msg = re.sub(r"\n\n\n", "\n\n", msg, flags=re.MULTILINE)

    return (msg.strip())


def invalid_argument():
    """
    引数解析失敗時のメッセージ
    """

    msg = "使い方が間違っています。"

    if g.cfg.config.has_section("custom_message"):
        key_list = []
        for i in g.cfg.config["custom_message"]:
            if i.startswith("invalid_argument"):
                key_list.append(i)
        if key_list:
            msg = g.cfg.config["custom_message"][random.choice(key_list)]

    return (msg)


def restricted_channel():
    """
    制限チャンネルでキーワードを検出したときのメッセージ
    """

    msg = "この投稿はデータベースに反映されません。"

    if g.cfg.config.has_section("custom_message"):
        key_list = []
        for i in g.cfg.config["custom_message"]:
            if i.startswith("restricted_channel"):
                key_list.append(i)
        if key_list:
            msg = g.cfg.config["custom_message"][random.choice(key_list)]

    return (msg)


def invalid_score(user_id, rpoint_sum, correct_score):
    """
    ゲーム終了時の素点合計が配給原点合計と異なる場合の警告メッセージ
    """

    rpoint_diff = abs(correct_score - rpoint_sum)
    msg = f"素点合計： {rpoint_sum}\n点数差分： {rpoint_diff}"

    if g.cfg.config.has_section("custom_message"):
        key_list = []
        for i in g.cfg.config["custom_message"]:
            if i.startswith("invalid_score"):
                key_list.append(i)
        if key_list:
            msg = g.cfg.config["custom_message"][random.choice(key_list)]

    return (f"<@{user_id}> " + msg.format(
        rpoint_diff=rpoint_diff * 100,
        rpoint_sum=rpoint_sum * 100,
    ))


def no_hits():
    """
    指定範囲に記録用キーワードが見つからなかった場合のメッセージ
    """

    start = g.prm.starttime_hm
    end = g.prm.endtime_hm
    msg = f"{start} ～ {end} に≪{g.cfg.search.keyword}≫はありません。"

    if g.cfg.config.has_section("custom_message"):
        key_list = []
        for i in g.cfg.config["custom_message"]:
            if i.startswith("no_hits"):
                key_list.append(i)
        if key_list:
            msg = g.cfg.config["custom_message"][random.choice(key_list)]

    return (msg.format(keyword=g.cfg.search.keyword, start=start, end=end))


def remarks(headword=False):
    """
    引数で指定された集計方法を注記にまとめる
    """

    remark = []

    if not g.opt.guest_skip:
        remark.append("2ゲスト戦の結果を含む")
    if not g.opt.unregistered_replace:
        if g.opt.individual:  # 個人集計時のみ表示
            remark.append("ゲスト置換なし(" + g.cfg.setting.guest_mark + "：未登録プレイヤー)")
    if g.opt.stipulated:
        remark.append(f"規定打数 {g.opt.stipulated} G以上")
    if g.opt.rule_version:
        remark.append(f"集計対象ルール {g.opt.rule_version}")

    if headword:
        if remark:
            return ("特記事項： " + "、".join(remark))

    return (remark)


def search_word(headword=False):
    if g.prm.search_word:
        ret = g.prm.search_word.replace("%", "")
        # 集約条件
        if g.prm.group_length:
            ret += f"（{g.prm.group_length}文字集約）"
    else:
        ret = ""

    if headword:
        if ret:
            return (f"検索ワード： {ret}")

    return (ret)


def header(game_info, add_text="", indent=1):
    msg = ""

    # 集計範囲
    if g.opt.search_word:  # コメント検索の場合はコメントで表示
        game_range1 = f"最初のゲーム：{game_info['first_comment']}\n"
        game_range1 += f"最後のゲーム：{game_info['last_comment']}\n"
    else:
        game_range1 = f"最初のゲーム：{game_info['first_game']}\n".replace("-", "/")
        game_range1 += f"最後のゲーム：{game_info['last_game']}\n".replace("-", "/")
    game_range2 = item_aggregation_range(game_info)

    # ゲーム数
    if game_info["game_count"] == 0:
        msg += f"{f.message.no_hits()}"
    else:
        match g.opt.command:
            case "results":
                if g.opt.target_count:  # 直近指定がない場合は検索範囲を付ける
                    msg += game_range1
                    msg += f"総ゲーム数：{game_info['game_count']} 回{add_text}\n"
                else:
                    msg += item_search_range()
                    msg += game_range1
                    msg += f"ゲーム数：{game_info['game_count']} 回{add_text}\n"
            case "ranking" | "report":
                msg += game_range2
                msg += f"集計ゲーム数：{game_info['game_count']}\n"
            case _:
                msg += game_range2
                msg += f"総ゲーム数：{game_info['game_count']} 回\n"

        if f.message.remarks():
            msg += "特記事項：" + "、".join(f.message.remarks()) + "\n"
        if f.message.search_word():
            msg += "検索ワード：" + f.message.search_word() + "\n"

    return (textwrap.indent(msg, "\t" * indent))


def del_blank_line(text: str):
    """
    空行を取り除く
    """

    new_text = []
    for x in text.split("\n"):
        if x.strip() == "":
            continue
        if x.strip() == "\t":
            continue
        new_text.append(x)

    return ("\n".join(new_text))


def item_search_range(kind=None, time_pattern=None):
    """
    検索範囲を返す（ヘッダ出力用）
    """

    match time_pattern:
        case "day":
            starttime = g.prm.starttime
            endtime = g.prm.endtime
        case "time":
            starttime = g.prm.starttime_hm
            endtime = g.prm.endtime_hm
        case _:
            starttime = g.prm.starttime_hms
            endtime = g.prm.endtime_hms

    match kind:
        case "list":
            return ([starttime, endtime])
        case "str":
            return (f"{starttime} ～ {endtime}\n")
        case _:
            return (f"検索範囲： {starttime} ～ {endtime}\n")


def item_aggregation_range(game_info, kind=None):
    """
    集計範囲を返す（ヘッダ出力用）
    """

    if g.opt.search_word:  # コメント検索の場合はコメントで表示
        first = game_info["first_comment"]
        last = game_info["last_comment"]
    else:
        first = game_info["first_game"].replace("-", "/")
        last = game_info["last_game"].replace("-", "/")

    match kind:
        case "list":
            return ([first, last])
        case "str":
            return (f"{first} ～ {last}\n")
        case _:
            return (f"集計範囲： {first} ～ {last}\n")
