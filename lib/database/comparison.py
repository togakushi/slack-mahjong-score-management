import re
import sqlite3
from datetime import datetime

import lib.command as c
import lib.function as f
from lib.function import global_value as g

def slack_search(command_option):
    """
    過去ログからスコアを検索して返す

    Parameters
    ----------
    command_option : dict
        コマンドオプション

    Returns
    -------
    data : dict
        検索した結果
    """

    keyword = g.config["search"].get("keyword", "終局")
    channel = g.config["search"].get("channel", "#麻雀部")
    command_option = f.configure.command_option_initialization("results")
    command_option["unregistered_replace"] = False # ゲスト無効
    g.logging.info(f"[serach] query:'{keyword} in:{channel}' {command_option}")

    ### データ取得 ###
    response = g.webclient.search_messages(
        query = f"{keyword} in:{channel}",
        sort = "timestamp",
        sort_dir = "asc",
        count = 100
    )
    matches = response["messages"]["matches"] # 1ページ目

    for p in range(2, response["messages"]["paging"]["pages"] + 1):
        response = g.webclient.search_messages(
            query = f"{keyword} in:{channel}",
            sort = "timestamp",
            sort_dir = "asc",
            count = 100,
            page = p
        )
        matches += response["messages"]["matches"] # 2ページ目以降

    data = {}
    for i in range(len(matches)):
        if "blocks" in matches[i]:
            ts = matches[i]["ts"]
            if "elements" in matches[i]["blocks"][0]:
                tmp_msg = ""
                elements = matches[i]["blocks"][0]["elements"][0]["elements"]

                for x in range(len(elements)):
                    if elements[x]["type"] == "text":
                        tmp_msg += elements[x]["text"]

                # 結果報告フォーマットに一致したポストの処理
                msg = c.search.pattern(tmp_msg)
                if msg:
                    p1_name = c.NameReplace(msg[0], command_option, add_mark = False)
                    p2_name = c.NameReplace(msg[2], command_option, add_mark = False)
                    p3_name = c.NameReplace(msg[4], command_option, add_mark = False)
                    p4_name = c.NameReplace(msg[6], command_option, add_mark = False)
                    g.logging.info("post data:[{} {} {}][{} {} {}][{} {} {}][{} {} {}]".format(
                        "東家", p1_name, msg[1], "南家", p2_name, msg[3],
                        "西家", p3_name, msg[5], "北家", p4_name, msg[7],
                        )
                    )
                    data[ts] = [p1_name, msg[1], p2_name, msg[3], p3_name, msg[5], p4_name, msg[7]]

    # slackのログに記録が1件もない場合は何もしない
    if len(data) == 0:
        return(None)
    else:
        return(data)

    # ToDo:
    # 見つかったログの最小 ts を起点にDBをselect
    # ログのtsがDBから見つかるかチェック
    # 見つかった→内容比較、update
    # 見つからない→ミリ秒を削って再チェック
    # それでも見つからない→取りこぼし、insert

    # DBのtsとログのtsの比較
    # DB側だけにあるts→ポストが削除された/管理から外された→delete
    # ミリ秒を削るパターンも
