"""
lib/data/initialization.py
"""

import logging
import os
import sqlite3

import libs.global_value as g
from libs.data.loader import load_query


def initialization_resultdb():
    """DB初期化"""
    resultdb = sqlite3.connect(
        g.cfg.db.database_file,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    resultdb.row_factory = sqlite3.Row

    resultdb.execute(load_query(os.path.join(g.cfg.script_dir, "libs/queries/table/member.sql")))  # メンバー登録テーブル
    resultdb.execute(load_query(os.path.join(g.cfg.script_dir, "libs/queries/table/alias.sql")))  # 別名定義テーブル
    resultdb.execute(load_query(os.path.join(g.cfg.script_dir, "libs/queries/table/team.sql")))  # チーム定義テーブル
    resultdb.execute(load_query(os.path.join(g.cfg.script_dir, "libs/queries/table/result.sql")))  # データ取り込みテーブル
    resultdb.execute(load_query(os.path.join(g.cfg.script_dir, "libs/queries/table/remarks.sql")))  # メモ格納テーブル
    resultdb.execute(load_query(os.path.join(g.cfg.script_dir, "libs/queries/table/words.sql")))  # レギュレーションワード登録テーブル

    # wordsテーブル情報読み込み(regulations)
    if g.cfg.config.has_section("regulations"):
        resultdb.execute("delete from words;")
        for k, v in g.cfg.config.items("regulations"):
            match k:
                case "undefined":
                    continue
                case "type0" | "yakuman":
                    words_list = {x.strip() for x in v.split(",")}
                    for word in words_list:
                        resultdb.execute(
                            "insert into words(word, type, ex_point) values (?, 0, NULL);",
                            (word,)
                        )
                    logging.info("regulations table(type0): %s", words_list)
                case "type2":
                    words_list = {x.strip() for x in v.split(",")}
                    for word in words_list:
                        resultdb.execute(
                            "insert into words(word, type, ex_point) values (?, 2, NULL);",
                            (word,)
                        )
                    logging.info("regulations table(type2): %s", words_list)
                case _:
                    word = k.strip()
                    ex_point = int(v)
                    resultdb.execute(
                        "insert into words(word, type, ex_point) values (?, 1, ?);",
                        (word, ex_point,)
                    )
                    logging.info("regulations table(type1): %s, %s", word, ex_point)

    resultdb.executescript(load_query(os.path.join(g.cfg.script_dir, "libs/queries/view/individual_results.sql")))
    resultdb.executescript(load_query(os.path.join(g.cfg.script_dir, "libs/queries/view/team_results.sql")))
    resultdb.executescript(load_query(os.path.join(g.cfg.script_dir, "libs/queries/view/game_results.sql")))
    resultdb.executescript(load_query(os.path.join(g.cfg.script_dir, "libs/queries/view/game_info.sql")))

    # メモ
    match g.cfg.undefined_word:
        case 0:
            grandslam_where = "words.type is null or words.type == 0"
            regulation_where = "words.type in (1, 2)"
        case 1:
            grandslam_where = "words.type == 0"
            regulation_where = "words.type is null or words.type == 1"
        case 2:
            grandslam_where = "words.type == 0"
            regulation_where = "words.type is null or words.type == 2"
        case _:
            grandslam_where = "words.type == 0"
            regulation_where = "words.type in (1, 2)"

    resultdb.executescript(load_query(os.path.join(g.cfg.script_dir, "libs/queries/view/grandslam.sql")).format(grandslam_where=grandslam_where))
    resultdb.executescript(load_query(os.path.join(g.cfg.script_dir, "libs/queries/view/regulations.sql")).format(regulation_where=regulation_where))

    # ゲスト設定チェック
    ret = resultdb.execute("select * from member where id=0;")
    data = ret.fetchall()

    if len(data) == 0:
        logging.notice("ゲスト設定: %s", g.cfg.member.guest_name)  # type: ignore
        sql = "insert into member (id, name) values (0, ?);"
        resultdb.execute(sql, (g.cfg.member.guest_name,))
    elif data[0][1] != g.cfg.member.guest_name:
        logging.notice("ゲスト修正: %s -> %s", data[0][1], g.cfg.member.guest_name)  # type: ignore
        sql = "update member set name=? where id=0;"
        resultdb.execute(sql, (g.cfg.member.guest_name,))

    resultdb.commit()
    resultdb.close()
