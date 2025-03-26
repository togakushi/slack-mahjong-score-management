import logging
from datetime import datetime
from typing import Tuple, TypedDict

from dateutil.relativedelta import relativedelta

import lib.global_value as g
from lib import database as d
from lib import function as f


class MsgDict(TypedDict, total=False):
    mismatch: str
    missing: str
    delete: str
    remark: str
    invalid_score: str
    pending: list[str]


def main():
    """データ突合の実施、その結果をslackにpostする
    """

    # チェックコマンドを拾ったイベントの情報を保持(結果の返し先)
    command_ch = g.msg.channel_id
    command_ts = g.msg.event_ts

    # データ突合
    count, msg = data_comparison()
    logging.notice("count=%s", count)  # type: ignore

    # 突合結果
    after = (datetime.now() - relativedelta(days=g.cfg.search.after)).strftime("%Y/%m/%d")
    before = datetime.now().strftime("%Y/%m/%d")

    ret = f"*【データ突合】* ({after} - {before})\n"
    if count["pending"]:
        ret += f"＊ 保留：{count['pending']}件\n"
        for x in msg["pending"]:
            ret += f"\t\t{f.common.ts_conv(float(x))}\n"
    ret += f"＊ 不一致：{count['mismatch']}件\n{msg['mismatch']}"
    ret += f"＊ 取りこぼし：{count['missing']}件\n{msg['missing']}"
    ret += f"＊ 削除漏れ：{count['delete']}件\n{msg['delete']}"
    ret += f"＊ メモ：{count['remark']}件\n{msg['remark']}"
    if count["invalid_score"] > 0:
        ret += "\n*【素点合計不一致】*\n"
        ret += msg["invalid_score"]

    g.msg.channel_id = command_ch
    f.slack_api.post_message(ret, command_ts)


def data_comparison() -> Tuple[dict, dict]:
    """データ突合処理

    Returns:
        Tuple[dict, dict]:
            - dict: 処理された更新/追加/削除の件数
            - dict: slackに返すメッセージ
    """

    count: dict = {}
    msg: dict = {}

    # slackログからゲーム結果を取得
    slack_data = f.search.for_slack()
    first_ts = (datetime.now() - relativedelta(days=g.cfg.search.after)).timestamp()

    # データベースからゲーム結果を取得
    db_data = f.search.for_database(first_ts)
    db_remarks = f.search.for_db_remarks(first_ts)

    logging.trace("thread_report: %s", g.cfg.setting.thread_report)  # type: ignore
    logging.trace("slack_data=%s", slack_data)  # type: ignore
    logging.trace("db_data=%s", db_data)  # type: ignore
    logging.trace("db_remarks=%s", db_remarks)  # type: ignore

    # --- スコア突合
    ret_count, ret_msg = check_omission(slack_data, db_data)
    count = f.common.merge_dicts(count, ret_count)
    msg = f.common.merge_dicts(msg, ret_msg)

    # --- 素点合計の再チェック(修正可能なslack側のみチェック)
    ret_count, ret_msg = check_total_score(slack_data)
    count = f.common.merge_dicts(count, ret_count)
    msg = f.common.merge_dicts(msg, ret_msg)

    # --- メモ突合
    ret_count, ret_msg = check_remarks(slack_data, db_remarks)
    count = f.common.merge_dicts(count, ret_count)
    msg = f.common.merge_dicts(msg, ret_msg)

    count.update(pending=len(msg["pending"]))

    return (count, msg)


def check_omission(slack_data: dict, db_data: dict) -> Tuple[dict, MsgDict]:
    """スコア取りこぼしチェック

    Args:
        slack_data (dict): slack検索結果
        db_data (dict): DB登録状況

    Returns:
        Tuple[dict, MsgDict]: 修正内容(結果)
    """

    now_ts = datetime.now().timestamp()
    count: dict[str, int] = {"mismatch": 0, "missing": 0, "delete": 0}
    msg: MsgDict = {"mismatch": "", "missing": "", "delete": "", "pending": []}

    for key, val in slack_data.items():
        if val["edited_ts"]:
            check_ts = float(max(val["edited_ts"])) + g.cfg.search.wait
        else:
            check_ts = float(key) + g.cfg.search.wait

        if check_ts > now_ts:
            msg["pending"].append(str(key))
            logging.info("pending(slack -> DB): %s", f.common.ts_conv(float(key)))
            continue

        slack_score = val.get("score")
        g.msg.channel_id = val.get("channel_id")
        g.msg.user_id = val.get("user_id")
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
                    msg["delete"] += f"\t{f.common.ts_conv(float(key))} {textformat(slack_score)}\n"
                    d.common.db_delete(key)

                    # リアクションの削除
                    if key in val.get("reaction_ok"):
                        f.slack_api.call_reactions_remove(g.cfg.setting.reaction_ok, ts=key)
                    if key in val.get("reaction_ng"):
                        f.slack_api.call_reactions_remove(g.cfg.setting.reaction_ng, ts=key)
                    continue

            if slack_score == db_score:  # スコア比較
                logging.info("score check pass: %s %s", f.common.ts_conv(float(key)), textformat(db_score))
                continue

            # 更新
            if d.common.exsist_record(key).get("rule_version") == g.prm.rule_version:
                count["mismatch"] += 1
                logging.notice("mismatch: %s", key)  # type: ignore
                logging.info("  *  slack: %s", textformat(db_score))
                logging.info("  *     db: %s", textformat(slack_score))
                msg["mismatch"] += f"\t{f.common.ts_conv(float(key))}\n"
                msg["mismatch"] += f"\t\t修正前：{textformat(db_score)}\n"
                msg["mismatch"] += f"\t\t修正後：{textformat(slack_score)}\n"
                d.common.db_update(slack_score, key, reactions_data)
            else:
                logging.info("score check skip: %s %s", f.common.ts_conv(float(key)), textformat(db_score))
            continue

        # 追加
        if not g.cfg.setting.thread_report and val.get("in_thread"):
            continue

        count["missing"] += 1
        logging.notice("missing: %s, %s", key, slack_score)  # type: ignore
        msg["missing"] += f"\t{f.common.ts_conv(float(key))} {textformat(slack_score)}\n"
        d.common.db_insert(slack_score, key, reactions_data)

    for key in db_data:  # DB -> slack チェック
        if float(key) + g.cfg.search.wait > now_ts:
            msg["pending"].append(str(key))
            logging.info("pending(DB -> slack): %s", f.common.ts_conv(float(key)))
            continue

        if key in slack_data:
            continue

        # 削除
        count["delete"] += 1
        logging.notice("delete: %s, %s (Only database)", key, db_data[key])  # type: ignore
        msg["delete"] += f"\t{f.common.ts_conv(float(key))} {textformat(db_data[key])}\n"
        g.msg.updatable = True
        d.common.db_delete(key)

        # メッセージが残っているならリアクションを外す
        if not g.msg.channel_id:
            g.msg.channel_id = f.slack_api.get_channel_id()
        for icon in f.slack_api.reactions_status(ts=key):
            f.slack_api.call_reactions_remove(icon, ts=key)

    return (count, msg)


def check_remarks(slack_data: dict, db_remarks: dict) -> Tuple[dict, MsgDict]:
    """メモの取りこぼしチェック

    Args:
        slack_data (dict): slack検索結果
        db_remarks (dict): DB登録状況

    Returns:
        Tuple[dict, MsgDict]: 修正内容(結果)
    """

    now_ts = datetime.now().timestamp()
    count: dict[str, int] = {"remark": 0}
    msg: MsgDict = {"remark": "", "pending": []}

    slack_remarks: list = []
    for key, val in slack_data.items():
        if val.get("edited_ts"):
            check_ts = float(max(val["edited_ts"])) + g.cfg.search.wait
        else:
            check_ts = float(key) + g.cfg.search.wait

        if check_ts > now_ts:
            msg["pending"].append(str(key))
            logging.info("pending(slack -> DB): %s", f.common.ts_conv(float(key)))
            continue

        remarks = val.get("remarks")
        event_ts = val.get("event_ts")
        for idx, (name, matter) in enumerate(remarks):
            in_name = name in val.get("score")
            chk = {
                "thread_ts": key,
                "event_ts": event_ts[idx],
                "name": name,
                "matter": matter,
            }
            slack_remarks.append(chk)

            if chk in db_remarks:  # slack -> DB チェック
                if in_name:
                    logging.info("remark pass: %s, %s", chk, in_name)
                else:
                    count["remark"] += 1
                    d.common.remarks_delete_compar(chk)
                    logging.notice("delete(name mismatch): %s", chk)  # type: ignore
            else:
                if in_name:
                    count["remark"] += 1
                    d.common.remarks_append((chk,))
                    logging.notice("insert(data missing): %s", chk)  # type: ignore

    for key in db_remarks:  # DB -> slack チェック
        event_ts = float(key.get("event_ts"))
        if event_ts + g.cfg.search.wait > now_ts:
            msg["pending"].append(str(event_ts))
            logging.info("pending(DB -> slack): %s", f.common.ts_conv(float(event_ts)))
            continue

        if key.get("thread_ts") in msg.get("pending", {}):  # スレッド元が保留中ならチェックしない
            msg["pending"].append(str(event_ts))
            logging.info("pending(thread): %s", f.common.ts_conv(float(event_ts)))
            continue

        if key in slack_remarks:
            continue

        count["remark"] += 1
        d.common.remarks_delete_compar(key)
        logging.notice("delete(missed deletion): %s", f.common.ts_conv(float(event_ts)))  # type: ignore

    return (count, msg)


def check_total_score(slack_data: dict) -> Tuple[dict, MsgDict]:
    """素点合計の再チェック

    Args:
        slack_data (dict): slack検索結果

    Returns:
        Tuple[dict, MsgDict]: 修正内容(結果)
    """

    now_ts = datetime.now().timestamp()
    count: dict[str, int] = {"invalid_score": 0}
    msg: MsgDict = {"invalid_score": "", "pending": []}

    for key, val in slack_data.items():
        if val["edited_ts"]:
            check_ts = float(max(val["edited_ts"])) + g.cfg.search.wait
        else:
            check_ts = float(key) + g.cfg.search.wait

        if check_ts > now_ts:
            msg["pending"].append(str(key))
            logging.info("pending(slack -> DB): %s", f.common.ts_conv(float(key)))
            continue

        if not g.cfg.setting.thread_report and val.get("in_thread"):
            continue
        if d.common.exsist_record(key).get("rule_version") != g.prm.rule_version:
            continue

        score_data = f.score.get_score(val.get("score"))
        reaction_ok = val.get("reaction_ok")
        reaction_ng = val.get("reaction_ng")

        if score_data["deposit"] != 0:  # 素点合計と配給原点が不一致
            count["invalid_score"] += 1
            logging.notice("invalid score: %s deposit=%s", key, score_data["deposit"])  # type: ignore
            msg["invalid_score"] += f"\t{f.common.ts_conv(float(key))} [供託：{score_data["deposit"]}]{textformat(val.get("score"))}\n"
            if key in reaction_ok:
                f.slack_api.call_reactions_remove(g.cfg.setting.reaction_ok, ts=key)
            if key not in reaction_ng:
                f.slack_api.call_reactions_add(g.cfg.setting.reaction_ng, ts=key)
        else:
            if key in reaction_ng:
                f.slack_api.call_reactions_remove(g.cfg.setting.reaction_ng, ts=key)
            if key not in reaction_ok:
                f.slack_api.call_reactions_add(g.cfg.setting.reaction_ok, ts=key)

    return (count, msg)


def textformat(text):
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

    return (ret)
