import logging
import re
import sqlite3
from contextlib import closing
from datetime import datetime

from dateutil.relativedelta import relativedelta

import global_value as g
from lib import command as c
from lib import database as d
from lib import function as f


def main():
    """
    データ突合の実施、その結果をslackにpostする
    """

    # チェックコマンドを拾ったイベントの情報を保持(結果の返し先)
    command_ch = g.msg.channel_id
    command_ts = g.msg.event_ts

    # スコア突合
    count, msg, fts = score_comparison()

    # メモ突合
    if fts:  # slackからスコア記録のログが見つかった場合のみチェック
        count["remark"] = remarks_comparison(fts)

    logging.notice(f"{count=}")

    # 突合結果
    after = (datetime.now() - relativedelta(days=g.cfg.search.after)).strftime("%Y/%m/%d")
    befor = datetime.now().strftime("%Y/%m/%d")
    ret = f"*【データ突合】* ({after} - {befor})\n"
    ret += "＊ 不一致： {}件\n{}".format(count["mismatch"], msg["mismatch"])
    ret += "＊ 取りこぼし：{}件\n{}".format(count["missing"], msg["missing"])
    ret += "＊ 削除漏れ： {}件\n{}".format(count["delete"], msg["delete"])
    ret += "＊ メモ： {}件\n{}".format(count["remark"], msg["remark"])
    if count["invalid_score"] > 0:
        ret += "\n*【素点合計不一致】*\n"
        ret += msg["invalid_score"]

    g.msg.channel_id = command_ch
    f.slack_api.post_message(ret, command_ts)


def score_comparison():
    """
    スコア突合

    Parameters
    ----------
    unnecessary

    Returns
    -------
    count : dict
        処理された更新/追加/削除の件数

    ret_msg : dict
        slackに返すメッセージ

    fts : str or None
        slackのログの先頭の時刻
        見つからない場合は None
    """

    count = {"mismatch": 0, "missing": 0, "delete": 0, "invalid_score": 0, "remark": 0}
    ret_msg = {"mismatch": "", "missing": "", "delete": "", "invalid_score": "", "remark": ""}
    fts = None  # slackのログの先頭の時刻

    # 検索パラメータ
    g.opt.initialization("results")
    g.opt.unregistered_replace = False  # ゲスト無効

    # slackログからデータを取得
    matches = f.search.for_slack(
        g.cfg.search.keyword,
        g.cfg.search.channel,
    )
    slack_data = f.search.game_result(matches)  # ゲーム結果のみ抽出
    if slack_data is None:
        return (count, ret_msg, fts)

    # データベースからデータを取得
    fts = list(slack_data.keys())[0]
    db_data = f.search.for_database(fts)
    if db_data is None:
        return (count, ret_msg, fts)

    # --- 突合処理
    # slackだけにあるパターン
    for key in slack_data.keys():
        g.msg.parser_matches(slack_data[key])
        detection = f.search.pattern(g.msg.text)  # 素点データ抽出
        score_data = f.score.get_score(detection)
        compar_slack = [  # データ構造を合わせる
            score_data["p1_name"], score_data["p1_str"],
            score_data["p2_name"], score_data["p2_str"],
            score_data["p3_name"], score_data["p3_str"],
            score_data["p4_name"], score_data["p4_str"],
            score_data["comment"],
        ]

        if key in db_data.keys():
            if compar_slack == db_data[key]:
                continue
            else:  # 更新
                count["mismatch"] += 1
                logging.notice(f"mismatch: {key}")
                logging.info(f"   * [slack]: {compar_slack}")
                logging.info(f"   * [   db]: {db_data[key]}")
                ret_msg["mismatch"] += "\t{}\n\t\t修正前：{}\n\t\t修正後：{}\n".format(
                    datetime.fromtimestamp(float(key)).strftime('%Y/%m/%d %H:%M:%S'),
                    textformat(db_data[key]), textformat(compar_slack),
                )
                d.common.db_update(compar_slack, g.msg.event_ts)
                continue
        else:  # 追加
            count["missing"] += 1
            logging.notice(f"missing: {key}, {compar_slack}")
            ret_msg["missing"] += "\t{} {}\n".format(
                datetime.fromtimestamp(float(key)).strftime('%Y/%m/%d %H:%M:%S'),
                textformat(compar_slack)
            )
            d.common.db_insert(compar_slack, g.msg.event_ts)

    # DBだけにあるパターン
    for key in db_data.keys():
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

    # 素点合計の再チェック(修正可能なslack側のみチェック)
    for key in slack_data.keys():
        g.msg.parser_matches(slack_data[key])
        detection = f.search.pattern(g.msg.text)  # 素点データ抽出
        score_data = f.score.get_score(detection)

        if score_data["deposit"] != 0:  # 素点合計と配給原点が不一致
            count["invalid_score"] += 1
            ret_msg["invalid_score"] += "\t{} [供託：{}]{}\n".format(
                datetime.fromtimestamp(float(key)).strftime('%Y/%m/%d %H:%M:%S'),
                score_data["deposit"], textformat(detection)
            )
            _ = f.slack_api.reactions_status()

    return (count, ret_msg, fts)


def textformat(text):
    """
    メッセージを整形する
    """

    ret = ""
    for i in range(0, 8, 2):
        ret += f"[{text[i]} {str(text[i + 1])}]"
    ret += f"[{text[8]}]"
    return (ret)


def remarks_comparison(fts):
    """
    メモ突合

    Parameters
    ----------
    fts : datetime
        検索開始時刻

    Returns
    -------
    remark_count : int
        処理された更新/追加/削除の件数
    """

    # 検索パラメータ
    g.opt.initialization("results")
    g.opt.unregistered_replace = False  # ゲスト無効
    g.opt.aggregation_range = ["全部"]  # 検索範囲

    slack_data = {}
    db_data = {}
    remark_count = 0

    # slackログからデータを取得
    matches = f.search.for_slack(
        g.cfg.cw.remarks_word,
        g.cfg.search.channel,
    )

    count = 0
    for i in range(len(matches)):
        event_ts = matches[i]["ts"]
        text = matches[i]["text"]
        permalink = matches[i]["permalink"]
        if permalink.split("?thread_ts=")[1:]:
            thread_ts = permalink.split("?thread_ts=")[1:][0]
        else:
            thread_ts = None

        if re.match(rf"^{g.cfg.cw.remarks_word}", text):
            if thread_ts:
                for name, val in zip(text.split()[1:][0::2], text.split()[1:][1::2]):
                    slack_data[count] = {
                        "thread_ts": thread_ts,
                        "event_ts": event_ts,
                        "name": c.member.NameReplace(name),
                        "matter": val,
                    }
                    logging.trace(f"slack: {slack_data[count]}")
                    count += 1

    slack_ts = set([slack_data[i]["event_ts"] for i in slack_data.keys()])

    # データベースからデータ取得
    with closing(sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)) as cur:
        cur.row_factory = sqlite3.Row
        curs = cur.cursor()

        count = 0
        rows = curs.execute("select * from remarks where thread_ts >= ?", (fts,))
        for row in rows.fetchall():
            db_data[count] = {
                "thread_ts": row["thread_ts"],
                "event_ts": row["event_ts"],
                "name": row["name"],
                "matter": row["matter"],
            }
            logging.trace(f"database: {db_data[count]}")
            count += 1

    db_ts = set([db_data[i]["event_ts"] for i in db_data.keys()])

    # --- 突合処理
    with closing(sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)) as cur:
        cur.row_factory = sqlite3.Row
        curs = cur.cursor()

        for x in slack_ts:
            check_data_src = []
            for i in slack_data.keys():
                if slack_data[i]["event_ts"] == x:
                    check_data_src.append(slack_data[i])

            check_data_dst = []
            for i in db_data.keys():
                if db_data[i]["event_ts"] == x:
                    check_data_dst.append(db_data[i])

            # スレッド元をデータベースから検索
            find_ts = []
            for i in check_data_src:
                rows = curs.execute(
                    "select ts from result where ts=?",
                    (str(i["thread_ts"]),)
                )
                for row in rows.fetchall():
                    find_ts.append(row["ts"])

            if find_ts:  # スレッド元がある
                if check_data_src == check_data_dst:
                    continue
                else:
                    curs.execute(d.sql_remarks_delete_one, (str(x),))
                    for update_data in check_data_src:
                        curs.execute(d.sql_remarks_insert, (
                            update_data["thread_ts"],
                            update_data["event_ts"],
                            c.member.NameReplace(update_data["name"]),
                            update_data["matter"],
                        ))
                        remark_count += 1
                        logging.info(f"update: {update_data}")
            else:  # スレッド元がないデータは不要 → 削除
                curs.execute(d.sql_remarks_delete_one, (str(x),))
                logging.info(f"delete: {x} (No thread origin)")

        for x in db_ts:
            if x not in slack_ts:  # データベースにあってslackにない → 削除
                curs.execute(d.sql_remarks_delete_one, (str(x),))
                logging.info(f"delete: {x} (Only database)")

        cur.commit()

    return (remark_count)
