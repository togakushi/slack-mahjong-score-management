"""
libs/utils/dbutil.py
"""

import re
import sqlite3
from importlib.resources import files
from typing import TYPE_CHECKING, Union

import libs.global_value as g

if TYPE_CHECKING:
    from pathlib import Path


def connection(database_path: Union["Path", str]) -> sqlite3.Connection:
    """DB接続共通処理

    Args:
        database_path (Union[Path, str]): データベースファイル

    Returns:
        sqlite3.Connection: オブジェクト
    """

    conn = sqlite3.connect(
        database=f"file:{database_path}",
        # detect_types=sqlite3.PARSE_DECLTYPES,
        uri=True,
    )
    conn.row_factory = sqlite3.Row

    return conn


def query(keyword: str) -> str:
    """SQLクエリを返す

    Args:
        keyword (str): SQL選択キーワード

    Raises:
        ValueError: 未定義のキーワード

    Returns:
        str: SQL文
    """

    sql_tables: dict[str, str] = {
        # テーブル作成
        "CREATE_TABLE_MEMBER": "table/member.sql",
        "CREATE_TABLE_ALIAS": "table/alias.sql",
        "CREATE_TABLE_TEAM": "table/team.sql",
        "CREATE_TABLE_RESULT": "table/result.sql",
        "CREATE_TABLE_REMARKS": "table/remarks.sql",
        "CREATE_TABLE_WORDS": "table/words.sql",
        "CREATE_TABLE_RULE": "table/rule.sql",
        # VIEW作成
        "CREATE_VIEW_INDIVIDUAL_RESULTS": "view/individual_results.sql",
        "CREATE_VIEW_GAME_RESULTS": "view/game_results.sql",
        "CREATE_VIEW_GAME_INFO": "view/game_info.sql",
        "CREATE_VIEW_REGULATIONS": "view/regulations.sql",
        # 情報取得
        "GAME_INFO": "game.info.sql",
        "RESULTS_INFO": "results.info.sql",
        "MEMBER_INFO": "member.info.sql",
        "TEAM_INFO": "team.info.sql",
        "REMARKS_INFO": "remarks.info.sql",
        "SUMMARY_GAMEDATA": "summary/gamedata.sql",
        "SUMMARY_DETAILS": "summary/details.sql",
        "SUMMARY_DETAILS2": "summary/details2.sql",
        "SUMMARY_RESULTS": "summary/results.sql",
        "SUMMARY_TOTAL": "summary/total.sql",
        "SUMMARY_VERSUS_MATRIX": "summary/versus_matrix.sql",
        "RANKING_AGGREGATE": "ranking/aggregate.sql",
        "RANKING_RESULTS": "ranking/results.sql",
        "RANKING_RECORD_COUNT": "ranking/record_count.sql",
        "RANKING_RATINGS": "ranking/ratings.sql",
        "REPORT_PERSONAL_DATA": "report/personal_data.sql",
        "REPORT_COUNT_DATA": "report/count_data.sql",
        "REPORT_MONTHLY": "report/monthly.sql",
        "REPORT_RESULTS_LIST": "report/results_list.sql",
        "REPORT_WINNER": "report/winner.sql",
        "REPORT_MATRIX_TABLE": "report/matrix_table.sql",
        "REPORT_COUNT_MOVING": "report/count_moving.sql",
        #
        "RESULT_INSERT": "general/result_insert.sql",
        "RESULT_UPDATE": "general/result_update.sql",
        "RESULT_DELETE": "general/result_delete.sql",
        #
        "REMARKS_SELECT": "general/remarks_select.sql",
        "REMARKS_INSERT": "general/remarks_insert.sql",
        "REMARKS_DELETE_ALL": "general/remarks_delete_all.sql",
        "REMARKS_DELETE_ONE": "general/remarks_delete_one.sql",
        "REMARKS_DELETE_COMPAR": "general/remarks_delete_compar.sql",
        #
        "SELECT_ALL_RESULTS": "general/select_all_results.sql",
        "SELECT_GAME_RESULTS": "general/select_game_results.sql",
    }

    if query_path := sql_tables.get(keyword):
        with open(str(files("files.queries").joinpath(query_path)), "r", encoding="utf-8") as queryfile:
            return str(queryfile.read()).strip()
    else:
        raise ValueError(f"Unknown keyword: {keyword}")


def query_modification(sql: str) -> str:
    """クエリをオプションの内容で修正する

    Args:
        sql (str): 修正するクエリ

    Returns:
        str: 修正後のクエリ
    """

    if g.params.get("individual"):  # 個人集計
        sql = sql.replace("--[individual] ", "")
        # ゲスト関連フラグ
        if g.params.get("unregistered_replace"):
            sql = sql.replace("--[unregistered_replace] ", "")
            if g.params.get("guest_skip"):
                sql = sql.replace("--[guest_not_skip] ", "")
            else:
                sql = sql.replace("--[guest_skip] ", "")
        else:
            sql = sql.replace("--[unregistered_not_replace] ", "")
    else:  # チーム集計
        g.params.update({"unregistered_replace": False})
        g.params.update({"guest_skip": True})
        sql = sql.replace("--[team] ", "")
        if not g.params.get("friendly_fire"):
            sql = sql.replace("--[friendly_fire] ", "")

    # 集約集計
    match g.params.get("collection"):
        case "daily":
            sql = sql.replace("--[collection_daily] ", "")
            sql = sql.replace("--[collection] ", "")
        case "weekly":
            sql = sql.replace("--[collection_weekly] ", "")
            sql = sql.replace("--[collection] ", "")
        case "monthly":
            sql = sql.replace("--[collection_monthly] ", "")
            sql = sql.replace("--[collection] ", "")
        case "yearly":
            sql = sql.replace("--[collection_yearly] ", "")
            sql = sql.replace("--[collection] ", "")
        case "all":
            sql = sql.replace("--[collection_all] ", "")
            sql = sql.replace("--[collection] ", "")
        case _:
            sql = sql.replace("--[not_collection] ", "")

    # 集計対象ルール
    rule_list: list = []
    g.params["mode"] = g.params.get("mode", 4)
    if target_mode := g.params.get("target_mode"):
        g.params["mode"] = target_mode
        rule_list.extend(g.cfg.rule.get_version(g.params["mode"], True))
    if g.params.get("mixed"):
        rule_list.extend(g.cfg.rule.get_version(g.params["mode"], False))
    if (rule_version := g.params.get("rule_version")) and g.cfg.rule.to_dict(rule_version):
        if g.params["mode"] == g.cfg.rule.get_mode(rule_version):
            rule_list.append(rule_version)
    if not rule_list:
        rule_list = list(g.cfg.rule.keyword_mapping.values())
    g.params["rule_set"] = {f"rule_{idx}": name for idx, name in enumerate(set(rule_list))}
    sql = sql.replace("<<rule_list>>", ":" + ", :".join(g.params["rule_set"]))

    # 集計モード
    match g.params.get("mode"):
        case 3:
            sql = sql.replace("--[mode3] ", "")
        case 4:
            sql = sql.replace("--[mode4] ", "")

    # スコア入力元識別子別集計
    if g.params.get("separate"):
        sql = sql.replace("--[separate] ", "")

    # コメント検索
    if g.params.get("search_word") or g.params.get("group_length"):
        sql = sql.replace("--[group_by] ", "")
    else:
        sql = sql.replace("--[not_group_by] ", "")

    if g.params.get("search_word"):
        sql = sql.replace("--[search_word] ", "")
    else:
        sql = sql.replace("--[not_search_word] ", "")

    if g.params.get("group_length"):
        sql = sql.replace("--[group_length] ", "")
    else:
        sql = sql.replace("--[not_group_length] ", "")
        if g.params.get("search_word"):
            sql = sql.replace("--[comment] ", "")
        else:
            sql = sql.replace("--[not_comment] ", "")

    # 直近N検索用（全範囲取得してから絞る）
    if g.params.get("target_count") != 0:
        sql = sql.replace("and my.playtime between", "-- and my.playtime between")

    # プレイヤーリスト
    if g.params.get("player_name"):
        sql = sql.replace("--[player_name] ", "")
        sql = sql.replace("<<player_list>>", ":" + ", :".join(g.params["player_list"]))
    sql = sql.replace("<<guest_mark>>", g.cfg.setting.guest_mark)

    # フラグの処理
    match g.cfg.aggregate_unit:
        case "M":
            sql = sql.replace("<<collection>>", "substr(collection_daily, 1, 7) as 集計")
            sql = sql.replace("<<group by>>", "group by 集計")
        case "Y":
            sql = sql.replace("<<collection>>", "substr(collection_daily, 1, 4) as 集計")
            sql = sql.replace("<<group by>>", "group by 集計")
        case "A":
            sql = sql.replace("<<collection>>", "'合計' as 集計")
            sql = sql.replace("<<group by>>", "")

    if g.params.get("interval") is not None:
        if g.params.get("interval") == 0:
            sql = sql.replace("<<Calculation Formula>>", ":interval")
        else:
            sql = sql.replace("<<Calculation Formula>>", "(row_number() over (order by total_count desc) - 1) / :interval")
    if g.params.get("kind") is not None:
        if g.params.get("kind") == "yakuman":
            if g.cfg.undefined_word == 0:
                sql = sql.replace("<<where_string>>", "and (words.type is null or words.type = 0)")
            else:
                sql = sql.replace("<<where_string>>", "and words.type = 0")
        else:
            match g.cfg.undefined_word:
                case 1:
                    sql = sql.replace("<<where_string>>", "and (words.type is null or words.type = 1)")
                case 2:
                    sql = sql.replace("<<where_string>>", "and (words.type is null or words.type = 2)")
                case _:
                    sql = sql.replace("<<where_string>>", "and (words.type = 1 or words.type = 2)")

    # SQLコメント削除
    sql = re.sub(r"^ *--\[.*$", "", sql, flags=re.MULTILINE)
    sql = re.sub(r"\n+", "\n", sql, flags=re.MULTILINE)

    return sql


def table_info(conn: sqlite3.Connection, table_name: str) -> dict:
    """テーブルのスキーマを取得して辞書で返す

    Args:
        conn (sqlite3.Connection): オブジェクト
        table_name (str): テーブル名

    Returns:
        dict: スキーマ
    """

    rows = conn.execute(f"pragma table_info('{table_name}');")
    schema = {row["name"]: dict(row) for row in rows.fetchall()}

    return schema
