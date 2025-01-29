import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta

import global_value as g
from lib import database as d
from lib import function as f


def main():
    """
    データ突合の実施、その結果をslackにpostする
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
    ret += "＊ 不一致： {}件\n{}".format(count["mismatch"], msg["mismatch"])
    ret += "＊ 取りこぼし：{}件\n{}".format(count["missing"], msg["missing"])
    ret += "＊ 削除漏れ： {}件\n{}".format(count["delete"], msg["delete"])
    ret += "＊ メモ： {}件\n{}".format(count["remark"], msg["remark"])
    if count["invalid_score"] > 0:
        ret += "\n*【素点合計不一致】*\n"
        ret += msg["invalid_score"]

    g.msg.channel_id = command_ch
    f.slack_api.post_message(ret, command_ts)


def data_comparison():
    """
    データ突合

    Parameters
    ----------
    unnecessary

    Returns
    -------
    count : dict
        処理された更新/追加/削除の件数

    ret_msg : dict
        slackに返すメッセージ
    """

    count = {"mismatch": 0, "missing": 0, "delete": 0, "invalid_score": 0, "remark": 0}
    ret_msg = {"mismatch": "", "missing": "", "delete": "", "invalid_score": "", "remark": ""}

    # slackログからゲーム結果を取得
    slack_data = f.search.for_slack()
    if slack_data:
        # データベースからゲーム結果を取得
        db_data = f.search.for_database(min(slack_data))
        if db_data is None:
            return (count, ret_msg)
        else:
            db_remarks = f.search.for_db_remarks(min(slack_data))
    else:
        return (count, ret_msg)

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
                    ret_msg["delete"] += "\t{} {}\n".format(
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
                continue
            else:  # 更新
                count["mismatch"] += 1
                logging.notice(f"mismatch: {key}")
                logging.info(f"   * [slack]: {slack_score}")
                logging.info(f"   * [   db]: {db_score}")
                ret_msg["mismatch"] += "\t{}\n\t\t修正前：{}\n\t\t修正後：{}\n".format(
                    datetime.fromtimestamp(float(key)).strftime('%Y/%m/%d %H:%M:%S'),
                    textformat(db_score), textformat(slack_score),
                )
                d.common.db_update(slack_score, key, reactions_data)
                continue
        else:  # 追加
            if not g.cfg.setting.thread_report and slack_data[key].get("in_thread"):
                pass
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
            ret_msg["delete"] += "\t{} {}\n".format(
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

        score_data = f.score.get_score(slack_data[key].get("score"))
        reaction_ok = slack_data[key].get("reaction_ok")
        reaction_ng = slack_data[key].get("reaction_ng")

        if score_data["deposit"] != 0:  # 素点合計と配給原点が不一致
            count["invalid_score"] += 1
            ret_msg["invalid_score"] += "\t{} [供託：{}]{}\n".format(
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
        if remarks:
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

                if chk in db_remarks:
                    logging.info(f"[pass] {chk}, {in_name=}")
                else:
                    logging.info(f"[missing] {chk}, {in_name=}")
                    if in_name:
                        count["remark"] += 1
                        d.common.remarks_append((chk,))
                        logging.info(f"insert: {chk}")

    if db_remarks:
        for x in db_remarks:
            if x in slack_remarks:
                pass
            else:
                count["remark"] += 1
                d.common.remarks_delete_compar(x)
                logging.info(f"delete: {x}")

    return (count, ret_msg)


def textformat(text):
    """
    メッセージを整形する
    """

    ret = ""
    for i in range(0, 8, 2):
        ret += f"[{text[i]} {str(text[i + 1])}]"
    ret += f"[{text[8]}]"
    return (ret)
