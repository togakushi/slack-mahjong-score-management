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
    logging.notice(f"{count=}")

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

    logging.trace(f"thread_report: {g.cfg.setting.thread_report}")
    logging.trace(f"{slack_data=}")
    logging.trace(f"{db_data=}")
    logging.trace(f"{db_remarks=}")

    # --- スコア突合
    for key in slack_data.keys():
        slack_score = slack_data[key].get("score")
        g.msg.channel_id = slack_data[key].get("channel_id")
        g.msg.user_id = slack_data[key].get("user_id")
        g.msg.event_ts = key

        reactions_data = []
        reactions_data.append(slack_data[key].get("reaction_ok"))
        reactions_data.append(slack_data[key].get("reaction_ng"))

        if key in db_data.keys():  # slack -> DB チェック
            db_score = db_data[key]
            if not g.cfg.setting.thread_report:  # スレッド内報告が禁止されているパターン
                if slack_data[key].get("in_thread"):
                    count["delete"] += 1
                    logging.notice(f"delete: {key}, {slack_score} (In-thread report)")
                    ret_msg["delete"] += "\t{} {}\n".format(  # pylint: disable=consider-using-f-string
                        datetime.fromtimestamp(float(key)).strftime('%Y/%m/%d %H:%M:%S'),
                        textformat(slack_score)
                    )
                    d.common.db_delete(key)

                    # リアクションの削除
                    if key in slack_data[key].get("reaction_ok"):
                        f.slack_api.call_reactions_remove(g.cfg.setting.reaction_ok, ts=key)
                    if key in slack_data[key].get("reaction_ng"):
                        f.slack_api.call_reactions_remove(g.cfg.setting.reaction_ng, ts=key)
                    continue

            if slack_score == db_score:  # スコア比較
                logging.info(f"score check pass: {key} {textformat(db_score)}")
                continue
            else:  # 更新
                if d.common.exsist_record(key).get("rule_version") == g.prm.rule_version:
                    count["mismatch"] += 1
                    logging.notice(f"mismatch: {key}")
                    logging.info(f"  *  slack: {textformat(db_score)}")
                    logging.info(f"  *     db: {textformat(slack_score)}")
                    ret_msg["mismatch"] += "\t{}\n\t\t修正前：{}\n\t\t修正後：{}\n".format(  # pylint: disable=consider-using-f-string
                        datetime.fromtimestamp(float(key)).strftime('%Y/%m/%d %H:%M:%S'),
                        textformat(db_score), textformat(slack_score),
                    )
                    d.common.db_update(slack_score, key, reactions_data)
                else:
                    logging.info(f"score check skip: {key} {textformat(db_score)}")
                continue
        else:  # 追加
            if not g.cfg.setting.thread_report and slack_data[key].get("in_thread"):
                continue
            else:
                count["missing"] += 1
                logging.notice(f"missing: {key}, {slack_score}")
                ret_msg["missing"] += "\t{} {}\n".format(
                    datetime.fromtimestamp(float(key)).strftime('%Y/%m/%d %H:%M:%S'),
                    textformat(slack_score)
                )
                d.common.db_insert(slack_score, key, reactions_data)

    for key in db_data.keys():  # DB -> slack チェック
        if key in slack_data.keys():
            continue
        else:  # 削除
            count["delete"] += 1
            logging.notice(f"delete: {key}, {db_data[key]} (Only database)")
            ret_msg["delete"] += "\t{} {}\n".format(  # pylint: disable=consider-using-f-string
                datetime.fromtimestamp(float(key)).strftime('%Y/%m/%d %H:%M:%S'),
                textformat(db_data[key])
            )
            d.common.db_delete(key)
            # メッセージが残っているならリアクションを外す
            for icon in f.slack_api.reactions_status(ts=key):
                f.slack_api.call_reactions_remove(icon)

    # 素点合計の再チェック(修正可能なslack側のみチェック)
    for key in slack_data.keys():
        if not g.cfg.setting.thread_report and slack_data[key].get("in_thread"):
            continue
        if d.common.exsist_record(key).get("rule_version") != g.prm.rule_version:
            continue

        score_data = f.score.get_score(slack_data[key].get("score"))
        reaction_ok = slack_data[key].get("reaction_ok")
        reaction_ng = slack_data[key].get("reaction_ng")

        if score_data["deposit"] != 0:  # 素点合計と配給原点が不一致
            count["invalid_score"] += 1
            logging.notice(f"invalid score: {key} deposit={score_data['deposit']}")
            ret_msg["invalid_score"] += "\t{} [供託：{}]{}\n".format(  # pylint: disable=consider-using-f-string
                datetime.fromtimestamp(float(key)).strftime('%Y/%m/%d %H:%M:%S'),
                score_data["deposit"], textformat(slack_data[key].get("score"))
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

    # --- メモ突合
    slack_remarks = []
    for key in slack_data.keys():
        remarks = slack_data[key].get("remarks")
        event_ts = slack_data[key].get("event_ts")
        for idx, (name, matter) in enumerate(remarks):
            in_name = True if name in slack_data[key].get("score") else False
            chk = {
                "thread_ts": key,
                "event_ts": event_ts[idx],
                "name": name,
                "matter": matter,
            }
            slack_remarks.append(chk)

            if chk in db_remarks:  # slack -> DB チェック
                if in_name:
                    logging.info(f"remark pass: {chk}, {in_name=}")
                else:
                    count["remark"] += 1
                    d.common.remarks_delete_compar(chk)
                    logging.notice(f"remark delete(name mismatch): {chk}")
            else:
                if in_name:
                    count["remark"] += 1
                    d.common.remarks_append((chk,))
                    logging.notice(f"remark insert(data missing): {chk}")

    for key in db_remarks:
        if key in slack_remarks:  # DB -> slack チェック
            continue
        else:
            count["remark"] += 1
            d.common.remarks_delete_compar(key)
            logging.notice(f"remark delete(missed deletion): {key}")

    return (count, ret_msg)


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
