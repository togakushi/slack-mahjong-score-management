import logging
import random
import re
import textwrap

import global_value as g
from lib import database as d
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
    """)

    # 検索範囲
    msg += "\n\n*検索範囲に指定できるキーワード*\n"
    for x in g.search_word.list().splitlines():
        msg += f"\t{x}\n"

    # ルール識別子
    rule = d.common.rule_version()
    if rule:
        msg += "\n\n*ルール識別子*\n"
        for x in rule.keys():
            msg += f"\t{x}： {rule[x]['first_time']} ～ {rule[x]['last_time']}\n"

    # メモ機能
    msg += textwrap.dedent(f"""
        *メモ機能*
        \t`登録キーワード <対象メンバー> <登録ワード>`
        \t登録キーワード： {g.cfg.cw.remarks_word}
    """)

    rule = d.common.word_list(1)
    if rule:
        msg += "\n\t*卓外ポイントワード(個人清算)*\n"
        for word, ex_point in rule:
            msg += "\t\t{}： {}pt\n".format(
                word,
                str(f"{ex_point:.1f}").replace("-", "▲"),
            )

    words = [word for word, _ in d.common.word_list(2)]
    if g.undefined_word == 2:
        words += ["未登録ワードのすべてを個別にカウント"]
    if words:
        msg += f"\n\t*個別カウントワード*\n\t\t{'、'.join(words)}\n"

    words = [word for word, _ in d.common.word_list(0)]
    if g.undefined_word == 0:
        words += ["未登録ワードのすべてを和了役としてカウント"]
    if words:
        msg += f"\n\t*役満カウントワード*\n\t\t{'、'.join(words)}\n"

    msg = re.sub(r"\n\n\n", "\n\n", msg, flags=re.MULTILINE)

    return (msg.strip())


def reply(message=None, mention=False, rpoint_sum=0):
    """
    メッセージをランダムに返す

    Parameters
    ----------
    message : str
        選択するメッセージ

    mention : bool
        メンションにする

    rpoint_sum : int
        素点合計(1/100)

    Returns
    -------
    msg : str
        メッセージ
    """

    correct_score = g.prm.origin_point * 4  # 配給原点
    rpoint_diff = abs(correct_score - rpoint_sum)

    default_message = {
        "invalid_argument": "使い方が間違っています。",
        "no_hits": "{start} ～ {end} に≪{keyword}≫はありません。",
        "invalid_score": "素点合計： {rpoint_sum}\n点数差分： {rpoint_diff}",
        "restricted_channel": "この投稿はデータベースに反映されません。",
        "inside_thread": "スレッド内から成績登録はできません。",
    }

    msg = default_message.get(message, "")

    if g.cfg.config.has_section("custom_message"):
        key_list = []
        for i in g.cfg.config["custom_message"]:
            if i.startswith(message):
                key_list.append(i)
        if key_list:
            msg = g.cfg.config["custom_message"][random.choice(key_list)]

    if mention:
        msg = "<@{user_id}> " + msg

    try:
        msg = msg.format(
            user_id=g.msg.user_id,
            keyword=g.cfg.search.keyword,
            start=g.prm.starttime_hm,
            end=g.prm.endtime_hm,
            rpoint_diff=rpoint_diff * 100,
            rpoint_sum=rpoint_sum * 100,
        )
    except Exception as err:
        logging.error(f"{err}: {msg}")
        msg = msg.replace("{user_id}", g.msg.user_id)

    return (msg)


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
        msg += f"{f.message.reply(message='no_hits')}"
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
