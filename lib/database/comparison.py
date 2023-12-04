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
                msg = ""
                elements = matches[i]["blocks"][0]["elements"][0]["elements"]

                for x in range(len(elements)):
                    if elements[x]["type"] == "text":
                        tmp_msg += elements[x]["text"]

                # 結果報告フォーマットに一致したポストの処理
                msg = c.search.pattern(tmp_msg)
                if msg:
                    g.logging.info("post data:[{} {} {}][{} {} {}][{} {} {}][{} {} {}]".format(
                        "東家", msg[0], msg[1], "南家", msg[2], msg[3],
                        "西家", msg[4], msg[5], "北家", msg[6], msg[7],
                        )
                    )
                    data[ts] = [msg[x] for x in msg]

    # slackのログに記録が1件もない場合は何もしない
    if len(data) == 0:
        return
    else:
        print(data)

    # ToDo:
    # 見つかったログの最小 ts を起点にDBをselect
    # ログのtsがDBから見つかるかチェック
    # 見つかった→内容比較、update
    # 見つからない→ミリ秒を削って再チェック
    # それでも見つからない→取りこぼし、insert

    # DBのtsとログのtsの比較
    # DB側だけにあるts→ポストが削除された/管理から外された→delete
    # ミリ秒を削るパターンも
