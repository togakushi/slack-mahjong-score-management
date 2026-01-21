"""
libs/data/initialization.py
"""

import json
import logging
import os
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING, Union, cast

import libs.global_value as g
from libs.utils import dbutil

if TYPE_CHECKING:
    from configparser import ConfigParser

    from libs.types import GradeTableDict


def initialization_resultdb(database_file: Union[str, Path]) -> None:
    """DB初期化 & マイグレーション

    Args:
        database_file (Union[str, Path]): データベース接続パス
    """

    if isinstance(database_file, Path):
        logging.info(database_file.absolute())
    else:
        logging.info(database_file)

    resultdb = dbutil.connection(database_file)
    memdb = dbutil.connection(":memory:")

    table_list = {
        "member": "CREATE_TABLE_MEMBER",  # メンバー登録テーブル
        "alias": "CREATE_TABLE_ALIAS",  # 別名定義テーブル
        "team": "CREATE_TABLE_TEAM",  # チーム定義テーブル
        "result": "CREATE_TABLE_RESULT",  # データ取り込みテーブル
        "remarks": "CREATE_TABLE_REMARKS",  # メモ格納テーブル
        "words": "CREATE_TABLE_WORDS",  # レギュレーションワード登録テーブル
        "rule": "CREATE_TABLE_RULE",  # ルールセット登録テーブル
    }
    for table_name, keyword in table_list.items():
        # テーブル作成
        resultdb.execute(dbutil.query(keyword))
        memdb.execute(dbutil.query(keyword))

        # スキーマ比較
        actual_cols = dbutil.table_info(resultdb, table_name)
        expected_cols = dbutil.table_info(memdb, table_name)
        for col_name, col_data in expected_cols.items():
            if col_name not in actual_cols:
                # NOT NULL かつ DEFAULT 未指定だと追加できないので回避
                if col_data["notnull"] and col_data["dflt_value"] is None:
                    logging.warning(
                        "migration skip: table=%s, column=%s, reason='NOT NULL' and 'DEFAULT' unspecified",
                        table_name,
                        col_name,
                    )
                    continue
                col_type = col_data["type"]
                notnull = "NOT NULL" if col_data["notnull"] else ""
                dflt = f"DEFAULT {col_data['dflt_value']}" if col_data["dflt_value"] is not None else ""
                resultdb.execute(f"alter table {table_name} add column {col_name} {col_type} {notnull} {dflt};")
                logging.info("migration: table=%s, column=%s", table_name, col_name)

    # 追加カラムデータ更新
    resultdb.execute("update result set mode = 4 where mode isnull and p4_name != '' and p4_str != '';")

    # regulationsテーブル情報読み込み
    if cast("ConfigParser", getattr(g.cfg, "_parser")).has_section("regulations"):
        resultdb.execute("delete from words;")
        for k, v in cast("ConfigParser", getattr(g.cfg, "_parser")).items("regulations"):
            match k:
                case "undefined":
                    g.cfg.undefined_word = int(v)
                case "yakuman_list":
                    words_list = {x.strip() for x in v.split(",")}
                    for word in words_list:
                        resultdb.execute("insert into words(word, type, ex_point) values (?, 0, NULL);", (word,))
                    logging.debug("regulations table(type0): %s", words_list)
                case "word_list":
                    words_list = {x.strip() for x in v.split(",")}
                    for word in words_list:
                        resultdb.execute("insert into words(word, type, ex_point) values (?, 1, NULL);", (word,))
                    logging.debug("regulations table(type1): %s", words_list)
                case _:
                    word = k.strip()
                    ex_point = int(v)
                    resultdb.execute(
                        "insert into words(word, type, ex_point) values (?, 2, ?);",
                        (
                            word,
                            ex_point,
                        ),
                    )
                    logging.debug("regulations table(type2): %s, %s", word, ex_point)

    if cast("ConfigParser", getattr(g.cfg, "_parser")).has_section("regulations"):
        for k, v in cast("ConfigParser", getattr(g.cfg, "_parser")).items("regulations_them"):
            resultdb.execute(
                "insert into words(word, type, ex_point) values (?, 3, ?);",
                (
                    k.strip(),
                    int(v),
                ),
            )
            logging.debug("regulations table(type3): %s, %s", k.strip(), int(v))

    # VIEW
    rows = resultdb.execute("select name from sqlite_master where type = 'view';")
    for row in rows.fetchall():
        resultdb.execute(f"drop view if exists '{row['name']}';")
    resultdb.execute(dbutil.query("CREATE_VIEW_INDIVIDUAL_RESULTS").replace("<time_adjust>", str(g.cfg.setting.time_adjust)))
    resultdb.execute(dbutil.query("CREATE_VIEW_GAME_RESULTS").replace("<time_adjust>", str(g.cfg.setting.time_adjust)))
    resultdb.execute(dbutil.query("CREATE_VIEW_GAME_INFO"))
    resultdb.execute(dbutil.query("CREATE_VIEW_REGULATIONS").format(undefined_word=g.cfg.undefined_word))

    # INDEX
    resultdb.execute(dbutil.query("CREATE_INDEX"))

    # ゲスト設定チェック
    ret = resultdb.execute("select * from member where id=0;")
    data = ret.fetchall()

    if len(data) == 0:
        logging.info("ゲスト設定: %s", g.cfg.member.guest_name)
        sql = "insert into member (id, name) values (0, ?);"
        resultdb.execute(sql, (g.cfg.member.guest_name,))
    elif data[0][1] != g.cfg.member.guest_name:
        logging.warning("ゲスト修正: %s -> %s", data[0][1], g.cfg.member.guest_name)
        sql = "update member set name=? where id=0;"
        resultdb.execute(sql, (g.cfg.member.guest_name,))

    resultdb.commit()
    resultdb.close()
    memdb.close()
    read_grade_table()


def read_grade_table() -> None:
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
            tbl_data: "GradeTableDict" = json.load(f)
        except json.JSONDecodeError as err:
            logging.warning("JSONDecodeError: %s", err)
            return

    if not isinstance(tbl_list := tbl_data.get("table"), list):
        logging.warning("undefined key [table]")
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
                    logging.warning("point is not match")
                    tbl_data = {}
                    break
                acquisition = x.get("acquisition")
                if not isinstance(acquisition, list) or len(acquisition) != 4:
                    logging.warning("acquisition is not match")
                    tbl_data = {}
                    break
            else:
                logging.warning("undefined key [grade, point, acquisition]")
                tbl_data = {}
                break
        else:
            tbl_data = {}
            break

    g.cfg.badge.grade.table = tbl_data
