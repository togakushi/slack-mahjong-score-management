import re
import sqlite3
from datetime import datetime

import lib.command as c
import lib.function as f
import lib.database as d
from lib.function import global_value as g


def main(client, channel, event_ts):
    """
    データ突合の実施、その結果をslackにpostする

    Parameters
    ----------
    client : obj

    channel : str
        post先のチャンネルID or ユーザーID

    event_ts: text
        スレッドに返す場合の返し先
    """

    # スコア突合
    count, msg, fts = score_comparison()

    # メモ突合
    if fts:  # slackからスコア記録のログが見つかった場合のみチェック
        remarks_comparison(fts)

    g.logging.notice(f"{count=}")  # type: ignore

    ret = "*【データ突合】*\n"
    ret += "＊ 不一致： {}件\n{}".format(count["mismatch"], msg["mismatch"])
    ret += "＊ 取りこぼし：{}件\n{}".format(count["missing"], msg["missing"])
    ret += "＊ 削除漏れ： {}件\n{}".format(count["delete"], msg["delete"])
    if count["invalid_score"] > 0:
        ret += "\n*【素点合計不一致】*\n"
        ret += msg["invalid_score"]

    f.slack_api.post_message(client, channel, ret, event_ts)


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

    count = {"mismatch": 0, "missing": 0, "delete": 0, "invalid_score": 0}
    ret_msg = {"mismatch": "", "missing": "", "delete": "", "invalid_score": ""}
    fts = None  # slackのログの先頭の時刻

    # 検索パラメータ
    g.opt.initialization("results")
    g.opt.unregistered_replace = False  # ゲスト無効

    # slackログからデータを取得
    matches = f.search.for_slack(
        g.config["search"].get("keyword", "終局"),
        g.config["search"].get("channel", "#麻雀部"),
    )
    slack_data = f.search.game_result(matches)
    if slack_data == None:
        return (count, ret_msg, fts)

    # データベースからデータを取得
    fts = list(slack_data.keys())[0]
    resultdb = sqlite3.connect(
        g.database_file,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    resultdb.row_factory = sqlite3.Row
    cur = resultdb.cursor()
    db_data = f.search.for_database(cur, fts)
    if db_data == None:
        return (count, ret_msg, fts)

    # --- 突合処理
    # slackだけにあるパターン
    for key in slack_data.keys():
        if key in db_data.keys():
            if slack_data[key] == db_data[key]:
                continue
            else:  # 更新
                count["mismatch"] += 1
                g.logging.notice(f"mismatch: {key}")  # type: ignore
                g.logging.info(f"   * [slack]: {slack_data[key]}")
                g.logging.info(f"   * [   db]: {db_data[key]}")
                ret_msg["mismatch"] += "\t{}\n\t\t修正前：{}\n\t\t修正後：{}\n".format(
                    datetime.fromtimestamp(float(key)).strftime('%Y/%m/%d %H:%M:%S'),
                    textformat(db_data[key]), textformat(slack_data[key]),
                )
                db_update(cur, key, slack_data[key])
                continue
        else:  # 追加
            count["missing"] += 1
            g.logging.notice(f"missing: {key}, {slack_data[key]}")  # type: ignore
            ret_msg["missing"] += "\t{} {}\n".format(
                datetime.fromtimestamp(float(key)).strftime('%Y/%m/%d %H:%M:%S'),
                textformat(slack_data[key])
            )
            db_insert(cur, key, slack_data[key])

    # DBだけにあるパターン
    for key in db_data.keys():
        if key in slack_data.keys():
            continue
        else:  # 削除
            count["delete"] += 1
            g.logging.notice(f"delete: {key}, {db_data[key]} (Only database)")  # type: ignore
            ret_msg["delete"] += "\t{} {}\n".format(
                datetime.fromtimestamp(float(key)).strftime('%Y/%m/%d %H:%M:%S'),
                textformat(db_data[key])
            )
            db_delete(cur, key)

    # 素点合計の再チェック(修正可能なslack側のみチェック)
    for i in slack_data.keys():
        rpoint_data = [
            eval(slack_data[i][1]), eval(slack_data[i][3]),
            eval(slack_data[i][5]), eval(slack_data[i][7]),
        ]
        deposit = g.config["mahjong"].getint("point", 250) * 4 - sum(rpoint_data)
        if not deposit == 0:
            count["invalid_score"] += 1
            ret_msg["invalid_score"] += "\t{} [供託：{}]{}\n".format(
                datetime.fromtimestamp(float(i)).strftime('%Y/%m/%d %H:%M:%S'),
                deposit, textformat(slack_data[i])
            )

    resultdb.commit()
    resultdb.close()

    return (count, ret_msg, fts)


def db_update(cur, ts, msg):  # 突合処理専用
    param = {
        "ts": ts,
        "playtime": datetime.fromtimestamp(float(ts)),
        "rule_version": g.rule_version,
    }
    param.update(f.score.get_score(msg))

    cur.execute(d.sql_result_update, param)
    g.logging.notice(f"{param=}")  # type: ignore


def db_insert(cur, ts, msg):  # 突合処理専用
    param = {
        "ts": ts,
        "playtime": datetime.fromtimestamp(float(ts)),
        "rule_version": g.rule_version,
    }
    param.update(f.score.get_score(msg))

    resultdb = sqlite3.connect(
        g.database_file,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    cur.execute(d.sql_result_insert, param)

    resultdb.commit()
    resultdb.close()
    g.logging.notice(f"{param=}")  # type: ignore


def db_delete(cur, ts):  # 突合処理専用
    cur.execute(d.sql_result_delete, (ts,))


def textformat(text):
    """
    メッセージを整形する
    """

    ret = ""
    for i in range(0, len(text), 2):
        if text[i] == None:
            continue
        ret += f"[{text[i]} {str(text[i + 1])}]"

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
    なし
    """

    # 検索パラメータ
    g.opt.initialization("results")
    g.opt.unregistered_replace = False  # ゲスト無効
    g.opt.aggregation_range = ["全部"]  # 検索範囲

    slack_data = {}
    db_data = {}

    # slackログからデータを取得
    matches = f.search.for_slack(
        g.commandword["remarks_word"],
        g.config["search"].get("channel", "#麻雀部"),
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

        if re.match(rf"^{g.commandword['remarks_word']}", text):
            if thread_ts:
                for name, val in zip(text.split()[1:][0::2], text.split()[1:][1::2]):
                    slack_data[count] = {
                        "thread_ts": thread_ts,
                        "event_ts": event_ts,
                        "name": c.member.NameReplace(name),
                        "matter": val,
                    }
                    g.logging.trace(f"slack: {slack_data[count]}")  # type: ignore
                    count += 1

    slack_ts = set([slack_data[i]["event_ts"] for i in slack_data.keys()])

    # データベースからデータ取得
    resultdb = sqlite3.connect(
        g.database_file,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    resultdb.row_factory = sqlite3.Row
    cur = resultdb.cursor()

    count = 0
    rows = cur.execute("select * from remarks where thread_ts >= ?", (fts,))
    for row in rows.fetchall():
        db_data[count] = {
            "thread_ts": row["thread_ts"],
            "event_ts": row["event_ts"],
            "name": row["name"],
            "matter": row["matter"],
        }
        g.logging.trace(f"database: {db_data[count]}")  # type: ignore
        count += 1

    db_ts = set([db_data[i]["event_ts"] for i in db_data.keys()])

    # --- 突合処理
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
            rows = cur.execute(
                "select ts from result where ts=?",
                (str(i["thread_ts"]),)
            )
            for row in rows.fetchall():
                find_ts.append(row["ts"])

        if find_ts:  # スレッド元がある
            if check_data_src == check_data_dst:
                continue
            else:
                cur.execute(d.sql_remarks_delete_one, (str(x),))
                for update_data in check_data_src:
                    cur.execute(d.sql_remarks_insert, (
                        update_data["thread_ts"],
                        update_data["event_ts"],
                        c.member.NameReplace(update_data["name"]),
                        update_data["matter"],
                    ))
                    g.logging.info(f"update: {update_data}")
        else:  # スレッド元がないデータは不要
            cur.execute(d.sql_remarks_delete_one, (str(x),))
            g.logging.info(f"delete: {x} (No thread origin)")

    for x in db_ts:
        if x not in slack_ts:  # データベースにあってslackにない → 削除
            cur.execute(d.sql_remarks_delete_one, (str(x),))
            g.logging.info(f"delete: {x} (Only database)")

    resultdb.commit()
    resultdb.close()
