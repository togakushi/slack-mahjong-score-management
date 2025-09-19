"""
libs/utils/dbutil.py
"""

import sqlite3
from importlib.resources import files


def connection(database_path: str) -> sqlite3.Connection:
    """DB接続共通処理

    Args:
        database_path (str): path

    Returns:
        sqlite3.Connection: オブジェクト
    """

    conn = sqlite3.connect(
        database=f"file:{database_path}",
        detect_types=sqlite3.PARSE_DECLTYPES,
        uri=True
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

        # VIEW作成
        "CREATE_VIEW_INDIVIDUAL_RESULTS": "view/individual_results.sql",
        "CREATE_VIEW_GAME_RESULTS": "view/game_results.sql",
        "CREATE_VIEW_GAME_INFO": "view/game_info.sql",
        "CREATE_VIEW_REGULATIONS": "view/regulations.sql",

        # 情報取得
        "GAME_INFO": "game.info.sql",
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
        "REMARKS_INSERT": "general/remarks_insert.sql",
        "REMARKS_DELETE_ALL": "general/remarks_delete_all.sql",
        "REMARKS_DELETE_ONE": "general/remarks_delete_one.sql",
        "REMARKS_DELETE_COMPAR": "general/remarks_delete_compar.sql",

        #
        "SELECT_ALL_RESULTS": "general/select_all_results.sql",
        "SELECT_GAME_RESULTS": "general/select_game_results.sql",
    }

    if (query_path := sql_tables.get(keyword)):
        with open(str(files("files.queries").joinpath(query_path)), "r", encoding="utf-8") as queryfile:
            return str(queryfile.read()).strip()
    else:
        raise ValueError(f"Unknown keyword: {keyword}")
