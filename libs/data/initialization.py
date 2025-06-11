"""
lib/data/initialization.py
"""

import json
import logging
import os
from importlib.resources import files

import libs.global_value as g
from cls.types import GradeTableDict
from libs.data import loader
from libs.utils import dbutil


def initialization_resultdb():
    """DB初期化"""
    resultdb = dbutil.get_connection()
    resultdb.execute(loader.load_query("table/member.sql"))  # メンバー登録テーブル
    resultdb.execute(loader.load_query("table/alias.sql"))  # 別名定義テーブル
    resultdb.execute(loader.load_query("table/team.sql"))  # チーム定義テーブル
    resultdb.execute(loader.load_query("table/result.sql"))  # データ取り込みテーブル
    resultdb.execute(loader.load_query("table/remarks.sql"))  # メモ格納テーブル
    resultdb.execute(loader.load_query("table/words.sql"))  # レギュレーションワード登録テーブル

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

    resultdb.executescript(loader.load_query("view/individual_results.sql"))
    resultdb.executescript(loader.load_query("view/team_results.sql"))
    resultdb.executescript(loader.load_query("view/game_results.sql"))
    resultdb.executescript(loader.load_query("view/game_info.sql"))

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

    resultdb.executescript(loader.load_query("view/grandslam.sql").format(grandslam_where=grandslam_where))
    resultdb.executescript(loader.load_query("view/regulations.sql").format(regulation_where=regulation_where))

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


def read_grade_table():
    """段位テーブル読み込み"""

    # テーブル選択
    match table_name := g.cfg.badge.grade.table_name:
        case "":
            return
        case "mahjongsoul" | "雀魂":
            tbl_file = str(files("files.gradetable").joinpath("mahjongsoul.json"))
        case "tenho" | "天鳳":
            tbl_file = str(files("files.gradetable").joinpath("tenho.json"))
        case _:
            tbl_file = os.path.join(g.cfg.config_dir, table_name)
            if not os.path.isfile(tbl_file):
                return

    with open(tbl_file, encoding="utf-8") as f:
        try:
            tbl_data: GradeTableDict = json.load(f)
        except json.JSONDecodeError as err:
            logging.error(err)
            return

    if not isinstance(tbl_list := tbl_data.get("table"), list):
        logging.error("undefined key [table]")
        return

    for x in tbl_list:
        if isinstance(x, dict):
            x["demote"] = x.get("demote", True)
            if {"grade", "point", "acquisition", "demote"} == set(x.keys()):
                if not isinstance(x.get("grade"), str):
                    tbl_data = {}
                    break
                point = x.get("point")
                if not isinstance(point, list) or len(point) != 2:
                    logging.error("point is not match")
                    tbl_data = {}
                    break
                acquisition = x.get("acquisition")
                if not isinstance(acquisition, list) or len(acquisition) != 4:
                    logging.error("acquisition is not match")
                    tbl_data = {}
                    break
            else:
                logging.error("undefined key [grade, point, acquisition]")
                tbl_data = {}
                break
        else:
            tbl_data = {}
            break

    g.cfg.badge.grade.table = tbl_data
