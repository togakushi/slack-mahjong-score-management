"""
lib/utils/dictutil.py
"""

import re
from typing import TYPE_CHECKING

import lib.global_value as g
from lib.utils import textutil

if TYPE_CHECKING:
    from cls.subcom import SubCommand


def analysis_argument(argument: list) -> dict:
    """引数解析

    Args:
        argument (list): 引数

    Returns:
        dict: 更新フラグ/パラメータ
    """

    ret: dict = {}

    # コマンドオプションフラグ変更
    unknown_command: list = []
    search_range: list = []

    if g.cfg.comment.search_word:
        ret.update(search_word=g.cfg.comment.search_word)
        ret.update(group_length=g.cfg.comment.group_length)

    for keyword in argument:
        check_word = textutil.str_conv(keyword.lower(), "h2k")  # カタカナ、小文字に統一
        check_word = check_word.replace("無シ", "ナシ").replace("有リ", "アリ")  # 表記統一

        if g.search_word.find(keyword):
            search_range.append(keyword)
            continue

        if re.match(r"^([0-9]{8}|[0-9/.-]{8,10})$", keyword):
            search_range.append(keyword)
            continue

        match check_word:
            case check_word if re.search(r"^ゲストナシ$", check_word):
                ret.update(guest_skip=False)
                ret.update(guest_skip2=False)
                ret.update(unregistered_replace=True)
            case check_word if re.search(r"^ゲストアリ$", check_word):
                ret.update(guest_skip=True)
                ret.update(guest_skip2=True)
                ret.update(unregistered_replace=True)
            case check_word if re.search(r"^ゲスト無効$", check_word):
                ret.update(unregistered_replace=False)
            case check_word if re.search(r"^(全員|all)$", check_word):
                ret.update(all_player=True)
            case check_word if re.search(r"^(比較|点差|差分)$", check_word):
                ret.update(score_comparisons=True)
            case check_word if re.search(r"^(戦績)$", check_word):
                ret.update(game_results=True)
            case check_word if re.search(r"^(対戦|対戦結果)$", check_word):
                ret.update(versus_matrix=True)
            case check_word if re.search(r"^(詳細|verbose)$", check_word):
                ret.update(verbose=True)
            case check_word if re.search(r"^(順位)$", check_word):
                ret.update(order=True)
            case check_word if re.search(r"^(統計)$", check_word):
                ret.update(statistics=True)
            case check_word if re.search(r"^(レート|レーティング|rate|ratings?)$", check_word):
                ret.update(rating=True)
            case check_word if re.search(r"^(個人|個人成績)$", check_word):
                ret.update(individual=True)
            case check_word if re.search(r"^(チーム|チーム成績|team)$", check_word):
                ret.update(individual=False)
            case check_word if re.search(r"^(直近)([0-9]+)$", check_word):
                ret.update(target_count=int(re.sub(r"^(直近)([0-9]+)$", r"\2", check_word)))
            case check_word if re.search(r"^(トップ|上位|top)([0-9]+)$", check_word):
                ret.update(ranked=int(re.sub(r"^(トップ|上位|top)([0-9]+)$", r"\2", check_word)))
            case check_word if re.search(r"^(規定数|規定打数)([0-9]+)$", check_word):
                ret.update(stipulated=int(re.sub(r"^(規定数|規定打数)([0-9]+)$", r"\2", check_word)))
            case check_word if re.search(r"^(区間|区切リ?|interval)([0-9]+)$", check_word):
                ret.update(interval=int(re.sub(r"^(区間|区切リ?|interval)([0-9]+)$", r"\2", check_word)))
            case check_word if re.search(r"^(チーム同卓アリ|コンビアリ|同士討チ)$", check_word):
                ret.update(friendly_fire=True)
            case check_word if re.search(r"^(チーム同卓ナシ|コンビナシ)$", check_word):
                ret.update(friendly_fire=False)
            case check_word if re.search(r"^(コメント|comment)(.+)$", check_word):
                ret.update(search_word=re.sub(r"^(コメント|comment)(.+)$", r"\2", check_word))
            case check_word if re.search(r"^(daily|デイリー|日次)$", check_word):
                ret.update(collection="daily")
            case check_word if re.search(r"^(monthly|マンスリー|月次)$", check_word):
                ret.update(collection="monthly")
            case check_word if re.search(r"^(yearly|イヤーリー|年次)$", check_word):
                ret.update(collection="yearly")
            case check_word if re.search(r"^(全体)$", check_word):
                ret.update(collection="all")
            case check_word if re.search(r"^(集約)([0-9]+)$", check_word):
                ret.update(group_length=int(re.sub(r"^(集約)([0-9]+)$", r"\2", check_word)))
            case check_word if re.search(r"^(ルール|rule)(.+)$", check_word):
                ret.update(rule_version=re.sub(r"^(ルール|rule)(.+)$", r"\2", keyword))
            case check_word if re.search(r"^(csv|text|txt)$", check_word):
                ret.update(format=check_word)
            case check_word if re.search(r"^(filename:|ファイル名)(.+)$", check_word):
                ret.update(filename=re.sub(r"^(filename:|ファイル名)(.+)$", r"\2", keyword))
            case check_word if re.search(r"^(匿名|anonymous)$", check_word):
                ret.update(anonymous=True)
            case _:
                unknown_command.append(keyword)

    ret.update(search_range=search_range)
    ret.update(unknown_command=unknown_command)
    return (ret)


def placeholder(subcom: "SubCommand") -> dict:
    """プレースホルダに使用する辞書を生成

    Args:
        subcom (SubCommand): パラメータ

    Returns:
        dict: プレースホルダ用辞書
    """

    ret_dict: dict = {}
    ret_dict.update(command=subcom.section)
    ret_dict.update(g.cfg.mahjong.to_dict())
    ret_dict.update(guest_name=g.cfg.member.guest_name)
    ret_dict.update(analysis_argument(g.msg.argument))
    ret_dict.update(subcom.update(g.msg.argument))
    ret_dict.update(subcom.to_dict())
    ret_dict.update(starttime=ret_dict["search_range"]["starttime"])
    ret_dict.update(endtime=ret_dict["search_range"]["endtime"])
    ret_dict.update(onday=ret_dict["search_range"]["onday"])

    if ret_dict.get("search_word"):
        ret_dict.update(search_word=f"%{ret_dict["search_word"]}%")

    if not ret_dict.get("interval"):
        ret_dict.update(interval=g.cfg.interval)

    # プレイヤーリスト/対戦相手リスト
    if ret_dict["player_list"]:
        for k, v in ret_dict["player_list"].items():
            ret_dict[k] = v
    if ret_dict["competition_list"]:
        for k, v in ret_dict["competition_list"].items():
            ret_dict[k] = v

    # 利用しない要素は削除
    drop_keys: list = [
        "config",
        "rank_point",
        "aggregation_range",
        "regulations_type2",
        "search_range",
        "unknown_command",
    ]
    for key in drop_keys:
        if key in ret_dict:
            ret_dict.pop(key)

    return (ret_dict)
