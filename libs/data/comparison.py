"""
lib/data/comparison.py
"""

import logging
from typing import cast

import libs.global_value as g
from cls.timekit import ExtendedDatetime as ExtDt
from cls.types import ComparisonDict, ScoreDataDict, SlackSearchData
from libs.data import lookup, modify
from libs.functions import score, search, slack_api
from libs.utils import dictutil

SlackSearchDict = dict[str, SlackSearchData]


def main() -> None:
    """データ突合の実施、その結果をslackにpostする"""
    # チェックコマンドを拾ったイベントの情報を保持(結果の返し先)
    command_ch = g.msg.channel_id
    command_ts = g.msg.event_ts

    # データ突合
    count, msg = data_comparison()
    logging.notice("count=%s", count)  # type: ignore

    # 突合結果
    after = ExtDt(days=-g.cfg.search.after).format("ymd")
    before = ExtDt().format("ymd")

    ret = f"*【データ突合】* ({after} - {before})\n"
    if count["pending"]:
        ret += f"＊ 保留：{count['pending']}件\n"
        for x in msg["pending"]:
            ret += f"\t\t{ExtDt(float(x)).format("ymdhms")}\n"
    ret += f"＊ 不一致：{count['mismatch']}件\n{msg['mismatch']}"
    ret += f"＊ 取りこぼし：{count['missing']}件\n{msg['missing']}"
    ret += f"＊ 削除漏れ：{count['delete']}件\n{msg['delete']}"
    ret += f"＊ メモ更新：{count['remark_mod']}件\n{msg['remark_mod']}"
    ret += f"＊ メモ削除：{count['remark_del']}件\n{msg['remark_del']}"
    if count["invalid_score"] > 0:
        ret += "\n*【素点合計不一致】*\n"
        ret += msg["invalid_score"]

    g.msg.channel_id = command_ch
    slack_api.post_message(ret, command_ts)


def data_comparison() -> tuple[dict, dict]:
    """データ突合処理

    Returns:
        tuple[dict,dict]:
        - dict: 処理された更新/追加/削除の件数
        - dict: slackに返すメッセージ
    """

    count: dict = {}
    msg: dict = {}

    # slackログからゲーム結果を取得
    slack_score = search.for_slack_score()
    slack_remarks = search.for_slack_remarks()
    for _, val in slack_remarks.items():  # スレッド元のスコアデータを追加
        thread_ts = val.get("thread_ts")
        if thread_ts in slack_score:
            val["score"] = slack_score[thread_ts].get("score", cast(ScoreDataDict, {}))

    if slack_score:
        first_ts = float(min(slack_score))
    else:
        first_ts = float(ExtDt(days=-g.cfg.search.after).format("ts"))

    # データベースからゲーム結果を取得
    db_score = search.for_db_score(first_ts)
    db_remarks = search.for_db_remarks(first_ts)

    # --- スコア突合
    ret_count, ret_msg = check_omission(slack_score, db_score)
    count = dictutil.merge_dicts(count, ret_count)
    msg = dictutil.merge_dicts(msg, ret_msg)

    # --- 素点合計の再チェック(修正可能なslack側のみチェック)
    ret_count, ret_msg = check_total_score(slack_score)
    count = dictutil.merge_dicts(count, ret_count)
    msg = dictutil.merge_dicts(msg, ret_msg)

    # --- メモ突合
    ret_count, ret_msg = check_remarks(slack_remarks, db_remarks)
    count = dictutil.merge_dicts(count, ret_count)
    msg = dictutil.merge_dicts(msg, ret_msg)

    count.update(pending=len(msg["pending"]))

    return (count, msg)


def check_omission(slack_data: SlackSearchDict, db_data: dict) -> tuple[dict, ComparisonDict]:
    """スコア取りこぼしチェック

    Args:
        slack_data (SlackSearchDict): slack検索結果
        db_data (dict): DB登録状況

    Returns:
        tuple[dict, ComparisonDict]: 修正内容(結果)
    """

    now_ts = float(ExtDt().format("ts"))
    count: dict[str, int] = {"mismatch": 0, "missing": 0, "delete": 0}
    msg: ComparisonDict = {"mismatch": "", "missing": "", "delete": "", "pending": []}

    for key, val in slack_data.items():
        # 保留チェック
        if val["edited_ts"]:
            check_ts = float(max(val["edited_ts"])) + g.cfg.search.wait
        else:
            check_ts = float(key) + g.cfg.search.wait

        if check_ts > now_ts:
            msg["pending"].append(str(key))
            logging.info("pending(slack -> DB): %s", ExtDt(float(key)).format("ymdhms"))
            continue

        slack_score = val.get("score", cast(ScoreDataDict, {}))
        g.msg.channel_id = val.get("channel_id", "")
        g.msg.user_id = val.get("user_id", "")
        g.msg.event_ts = key
        g.msg.check_updatable()

        reactions_data = []
        reactions_data.append(val.get("reaction_ok"))
        reactions_data.append(val.get("reaction_ng"))

        if key in db_data:  # slack -> DB チェック
            db_score = db_data[key]
            if not g.cfg.setting.thread_report:  # スレッド内報告が禁止されているパターン
                if val.get("in_thread"):
                    count["delete"] += 1
                    logging.notice("delete: %s, %s (In-thread report)", key, slack_score)  # type: ignore
                    msg["delete"] += f"\t{ExtDt(float(key)).format("ymdhms")} {textformat(slack_score)}\n"
                    modify.db_delete(key)

                    # リアクションの削除
                    if key in val.get("reaction_ok", []):
                        slack_api.call_reactions_remove(g.cfg.setting.reaction_ok, ts=key)
                    if key in val.get("reaction_ng", []):
                        slack_api.call_reactions_remove(g.cfg.setting.reaction_ng, ts=key)
                    continue

            if slack_score == db_score:  # スコア比較
                logging.info("score check pass: %s %s", ExtDt(float(key)).format("ymdhms"), textformat(db_score))
                continue

            # 更新
            if lookup.db.exsist_record(key).get("rule_version") == g.cfg.mahjong.rule_version:
                count["mismatch"] += 1
                logging.notice("mismatch: %s", key)  # type: ignore
                logging.info("  *  slack: %s", textformat(db_score))
                logging.info("  *     db: %s", textformat(slack_score))
                msg["mismatch"] += f"\t{ExtDt(float(key)).format("ymdhms")}\n"
                msg["mismatch"] += f"\t\t修正前：{textformat(db_score)}\n"
                msg["mismatch"] += f"\t\t修正後：{textformat(slack_score)}\n"
                modify.db_update(slack_score, key, reactions_data)
            else:
                logging.info("score check skip: %s %s", ExtDt(float(key)).format("ymdhms"), textformat(db_score))
            continue

        # 追加
        if not g.cfg.setting.thread_report and val.get("in_thread"):
            continue

        count["missing"] += 1
        logging.notice("missing: %s, %s", key, slack_score)  # type: ignore
        msg["missing"] += f"\t{ExtDt(float(key)).format("ymdhms")} {textformat(slack_score)}\n"
        modify.db_insert(slack_score, key, reactions_data)

    for key in db_data:  # DB -> slack チェック
        if float(key) + g.cfg.search.wait > now_ts:
            msg["pending"].append(str(key))
            logging.info("pending(DB -> slack): %s", ExtDt(float(key)).format("ymdhms"))
            continue

        if key in slack_data:
            continue

        # 削除
        count["delete"] += 1
        logging.notice("delete: %s, %s (Only database)", key, db_data[key])  # type: ignore
        msg["delete"] += f"\t{ExtDt(float(key)).format("ymdhms")} {textformat(db_data[key])}\n"
        g.msg.updatable = True
        modify.db_delete(key)

        # メッセージが残っているならリアクションを外す
        if not g.msg.channel_id:
            g.msg.channel_id = lookup.api.get_channel_id()
        for icon in lookup.api.reactions_status(ts=key):
            slack_api.call_reactions_remove(icon, ts=key)

    return (count, msg)


def check_remarks(slack_data: SlackSearchDict, db_data: list) -> tuple[dict, ComparisonDict]:
    """メモの取りこぼしチェック

    Args:
        slack_data (SlackSearchDict): slack検索結果
        db_data (list): DB登録状況

    Returns:
        tuple[dict, ComparisonDict]: 修正内容(結果)
    """

    now_ts = float(ExtDt().format("ts"))
    count: dict[str, int] = {"remark_mod": 0, "remark_del": 0}
    msg: ComparisonDict = {"remark_mod": "", "remark_del": "", "pending": []}

    # 比較用リスト生成
    slack_remarks: list = []
    for val in slack_data.values():
        if val.get("remarks", []):
            for name, matter in val["remarks"]:
                if name in val.get("score", []) and val.get("in_thread"):
                    slack_remarks.append({
                        "thread_ts": val.get("thread_ts", ""),
                        "event_ts": val.get("event_ts", ""),
                        "name": name,
                        "matter": matter,
                    })

    # slack -> DB チェック
    for remark in slack_remarks:
        # 保留チェック
        if float(remark["event_ts"]) + g.cfg.search.wait > now_ts:
            msg["pending"].append(remark["event_ts"])
            logging.info("pending(slack -> DB): %s", ExtDt(float(remark["event_ts"])).format("ymdhms"))
            continue

        if remark in db_data:
            logging.info("remark pass(slack -> DB): %s", remark)
        else:
            count["remark_mod"] += 1
            modify.remarks_delete(remark["event_ts"])
            modify.remarks_append(remark)
            logging.notice("modification(data mismatch): %s", remark)  # type: ignore

    # DB -> slack チェック
    for remark in db_data:
        if remark in slack_remarks:
            logging.info("remark pass(DB -> slack): %s", remark)
        else:
            count["remark_del"] += 1
            modify.remarks_delete_compar(remark)
            logging.notice("delete(missed deletion): %s", remark)  # type: ignore

    return (count, msg)


def check_total_score(slack_data: dict) -> tuple[dict, ComparisonDict]:
    """素点合計の再チェック

    Args:
        slack_data (dict): slack検索結果

    Returns:
        tuple[dict, ComparisonDict]: 修正内容(結果)
    """

    now_ts = float(ExtDt().format("ts"))
    count: dict[str, int] = {"invalid_score": 0}
    msg: ComparisonDict = {"invalid_score": "", "pending": []}

    for key, val in slack_data.items():
        if val["edited_ts"]:
            check_ts = float(max(val["edited_ts"])) + g.cfg.search.wait
        else:
            check_ts = float(key) + g.cfg.search.wait

        if check_ts > now_ts:
            msg["pending"].append(str(key))
            logging.info("pending(slack -> DB): %s", ExtDt(float(key)).format("ymdhms"))
            continue

        if not g.cfg.setting.thread_report and val.get("in_thread"):
            continue
        if lookup.db.exsist_record(key).get("rule_version") != g.cfg.mahjong.rule_version:
            continue

        score_data = score.get_score(val.get("score", cast(ScoreDataDict, {})))
        reaction_ok = val.get("reaction_ok")
        reaction_ng = val.get("reaction_ng")

        if score_data["deposit"] != 0:  # 素点合計と配給原点が不一致
            count["invalid_score"] += 1
            logging.notice("invalid score: %s deposit=%s", key, score_data["deposit"])  # type: ignore
            msg["invalid_score"] += f"\t{ExtDt(float(key)).format("ymdhms")} [供託：{score_data["deposit"]}]{textformat(val.get("score"))}\n"
            if key in reaction_ok:
                slack_api.call_reactions_remove(g.cfg.setting.reaction_ok, ts=key)
            if key not in reaction_ng:
                slack_api.call_reactions_add(g.cfg.setting.reaction_ng, ts=key)
        else:
            if key in reaction_ng:
                slack_api.call_reactions_remove(g.cfg.setting.reaction_ng, ts=key)
            if key not in reaction_ok:
                slack_api.call_reactions_add(g.cfg.setting.reaction_ok, ts=key)

    return (count, msg)


def textformat(text) -> str:
    """メンバーと素点を整形する

    Args:
        text (list): 素点データ

    Returns:
        str: 整形テキスト
    """

    ret = ""
    for i in range(0, 8, 2):
        ret += f"[{text[i]} {str(text[i + 1])}]"

    if text[8]:  # ゲームコメントの有無
        ret += f"[{text[8]}]"
    else:
        ret += "[]"

    return ret
