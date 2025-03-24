import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta

import lib.global_value as g
from lib import database as d
from lib import function as f


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
    ret += f"＊ 不一致：{count['mismatch']}件\n{msg['mismatch']}"
    ret += f"＊ 取りこぼし：{count['missing']}件\n{msg['missing']}"
    ret += f"＊ 削除漏れ：{count['delete']}件\n{msg['delete']}"
    ret += f"＊ メモ：{count['remark']}件\n{msg['remark']}"
    if count["invalid_score"] > 0:
        ret += "\n*【素点合計不一致】*\n"
        ret += msg["invalid_score"]

    g.msg.channel_id = command_ch
    f.slack_api.post_message(ret, command_ts)


def data_comparison():
    """データ突合処理

    Returns:
        Tuple[dict, dict]:
            - dict: 処理された更新/追加/削除の件数
            - dict: slackに返すメッセージ
    """

    count = {"mismatch": 0, "missing": 0, "delete": 0, "invalid_score": 0, "remark": 0}
    ret_msg = {"mismatch": "", "missing": "", "delete": "", "invalid_score": "", "remark": ""}

    # slackログからゲーム結果を取得
    slack_data = f.search.for_slack()
    if slack_data:
        first_ts = min(slack_data)
    else:
        first_ts = (datetime.now() - relativedelta(days=g.cfg.search.after)).timestamp()

    # データベースからゲーム結果を取得
    db_data = f.search.for_database(first_ts)
    db_remarks = f.search.for_db_remarks(first_ts)

    logging.trace("thread_report: %s", g.cfg.setting.thread_report)  # type: ignore
    logging.trace("slack_data=%s", slack_data)  # type: ignore
    logging.trace("db_data=%s", db_data)  # type: ignore
    logging.trace("db_remarks=%s", db_remarks)  # type: ignore

    # --- スコア突合
    for key, val in slack_data.items():
        slack_score = val.get("score")
        g.msg.channel_id = val.get("channel_id")
        g.msg.user_id = val.get("user_id")
        g.msg.event_ts = key

        reactions_data = []
        reactions_data.append(val.get("reaction_ok"))
        reactions_data.append(val.get("reaction_ng"))

        if key in db_data:  # slack -> DB チェック
            db_score = db_data[key]
            if not g.cfg.setting.thread_report:  # スレッド内報告が禁止されているパターン
                if val.get("in_thread"):
                    count["delete"] += 1
                    logging.notice("delete: %s, %s (In-thread report)", key, slack_score)  # type: ignore
                    ret_msg["delete"] += "\t{} {}\n".format(  # pylint: disable=consider-using-f-string
                        datetime.fromtimestamp(float(key)).strftime('%Y/%m/%d %H:%M:%S'),
                        textformat(slack_score)
                    )
                    d.common.db_delete(key)

                    # リアクションの削除
                    if key in val.get("reaction_ok"):
                        f.slack_api.call_reactions_remove(g.cfg.setting.reaction_ok, ts=key)
                    if key in val.get("reaction_ng"):
                        f.slack_api.call_reactions_remove(g.cfg.setting.reaction_ng, ts=key)
                    continue

            if slack_score == db_score:  # スコア比較
                logging.info("score check pass: %s %s", key, textformat(db_score))
                continue

            # 更新
            if d.common.exsist_record(key).get("rule_version") == g.prm.rule_version:
                count["mismatch"] += 1
                logging.notice("mismatch: %s", key)  # type: ignore
                logging.info("  *  slack: %s", textformat(db_score))
                logging.info("  *     db: %s", textformat(slack_score))
                ret_msg["mismatch"] += "\t{}\n\t\t修正前：{}\n\t\t修正後：{}\n".format(  # pylint: disable=consider-using-f-string
                    datetime.fromtimestamp(float(key)).strftime('%Y/%m/%d %H:%M:%S'),
                    textformat(db_score), textformat(slack_score),
                )
                d.common.db_update(slack_score, key, reactions_data)
            else:
                logging.info("score check skip: %s %s", key, textformat(db_score))
            continue

        # 追加
        if not g.cfg.setting.thread_report and val.get("in_thread"):
            continue

        count["missing"] += 1
        logging.notice("missing: %s, %s", key, slack_score)  # type: ignore
        ret_msg["missing"] += "\t{} {}\n".format(  # pylint: disable=consider-using-f-string
            datetime.fromtimestamp(float(key)).strftime('%Y/%m/%d %H:%M:%S'),
            textformat(slack_score)
        )
        d.common.db_insert(slack_score, key, reactions_data)

    for key in db_data:  # DB -> slack チェック
        if key in slack_data:
            continue

        # 削除
        count["delete"] += 1
        logging.notice("delete: %s, %s (Only database)", key, db_data[key])  # type: ignore
        ret_msg["delete"] += "\t{} {}\n".format(  # pylint: disable=consider-using-f-string
            datetime.fromtimestamp(float(key)).strftime('%Y/%m/%d %H:%M:%S'),
            textformat(db_data[key])
        )
        d.common.db_delete(key)
        # メッセージが残っているならリアクションを外す
        for icon in f.slack_api.reactions_status(ts=key):
            f.slack_api.call_reactions_remove(icon)

    # 素点合計の再チェック(修正可能なslack側のみチェック)
    for key, val in slack_data.items():
        ret = check_total_score(key, val)
        if ret:
            count["invalid_score"] += 1
            ret_msg["invalid_score"] += ret

    # --- メモ突合
    slack_remarks = []
    for key, val in slack_data.items():
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
                    logging.notice("remark delete(name mismatch): %s", chk)  # type: ignore
            else:
                if in_name:
                    count["remark"] += 1
                    d.common.remarks_append((chk,))
                    logging.notice("remark insert(data missing): %s", chk)  # type: ignore

    for key in db_remarks:
        if key in slack_remarks:  # DB -> slack チェック
            continue

        count["remark"] += 1
        d.common.remarks_delete_compar(key)
        logging.notice("remark delete(missed deletion): %s", key)  # type: ignore

    return (count, ret_msg)


def check_total_score(key, val) -> str:
    """素点合計の再チェック

    Args:
        key (_type_): _description_
        val (_type_): _description_

    Returns:
        str: _description_
    """

    ret_msg = ""

    if not g.cfg.setting.thread_report and val.get("in_thread"):
        return (ret_msg)
    if d.common.exsist_record(key).get("rule_version") != g.prm.rule_version:
        return (ret_msg)

    score_data = f.score.get_score(val.get("score"))
    reaction_ok = val.get("reaction_ok")
    reaction_ng = val.get("reaction_ng")

    if score_data["deposit"] != 0:  # 素点合計と配給原点が不一致
        logging.notice("invalid score: %s deposit=%s", key, score_data["deposit"])  # type: ignore
        ret_msg = "\t{} [供託：{}]{}\n".format(  # pylint: disable=consider-using-f-string
            datetime.fromtimestamp(float(key)).strftime('%Y/%m/%d %H:%M:%S'),
            score_data["deposit"], textformat(val.get("score"))
        )
        if key in reaction_ok:
            f.slack_api.call_reactions_remove(g.cfg.setting.reaction_ok, ts=key)
        if key not in reaction_ng:
            f.slack_api.call_reactions_add(g.cfg.setting.reaction_ng, ts=key)
    else:
        if key in reaction_ng:
            f.slack_api.call_reactions_remove(g.cfg.setting.reaction_ng, ts=key)
        if key not in reaction_ok:
            f.slack_api.call_reactions_add(g.cfg.setting.reaction_ok, ts=key)

    return (ret_msg)


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
