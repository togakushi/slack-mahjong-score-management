"""
tests/database/conftest.py

テスト共通前処理
"""

from contextlib import closing
from pathlib import Path

import pandas as pd
import pytest

import libs.global_value as g
from cls.config import AppConfig
from libs import configuration
from libs.data import initialization
from libs.utils import dbutil


@pytest.fixture(scope="package")
def database_connection():
    """共有インメモリDBと接続"""
    configuration.set_loglevel()
    g.cfg = AppConfig(Path("tests/testdata/minimal.ini"))
    g.cfg.setting.database_file = "memdb1?mode=memory&cache=shared"
    conn = dbutil.connection(g.cfg.setting.database_file)
    yield conn
    conn.close()


@pytest.fixture(scope="package", autouse=True)
def initialize_database(database_connection):
    """DB初期化"""
    _ = database_connection  # pylint (W0613: Unused argument)
    initialization.initialization_resultdb(g.cfg.setting.database_file)
    with closing(dbutil.connection(g.cfg.setting.database_file)) as conn:
        pd.read_csv("tests/test_data/saki_member.csv").to_sql(
            name="member",
            con=conn,
            if_exists="append",
            index=False,
        )
        pd.read_csv("tests/test_data/saki_team.csv").to_sql(
            name="team",
            con=conn,
            if_exists="append",
            index=False,
        )
        cur = conn.execute("select name from member where id != 0;")
        rows = cur.fetchall()
        for name in [dict(row).get("name") for row in rows]:
            conn.execute(
                "insert into alias(name, member) values (?, ?);",
                (
                    name,
                    name,
                ),
            )
        conn.commit()

    configuration.read_memberslist()
