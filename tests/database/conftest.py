"""
tests/database/conftest.py
"""

from contextlib import closing

import pandas as pd
import pytest

import libs.global_value as g
from cls.config import AppConfig
from libs.data import initialization
from libs.functions import configuration
from libs.utils import dbutil


@pytest.fixture(scope="package")
def database_connection():
    """共有インメモリDBと接続"""
    configuration.set_loglevel()
    g.cfg = AppConfig("tests/testdata/minimal.ini")
    g.cfg.db.database_file = "memdb1?mode=memory&cache=shared"
    conn = dbutil.get_connection()
    yield conn
    conn.close()


@pytest.fixture(scope="package", autouse=True)
def initialize_database(database_connection):  # pylint: disable=redefined-outer-name
    """DB初期化"""
    _ = database_connection  # pylint (W0613: Unused argument)
    initialization.initialization_resultdb()
    with closing(dbutil.get_connection()) as conn:
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
            conn.execute("insert into alias(name, member) values (?, ?);", (name, name,))
        conn.commit()

    configuration.read_memberslist()
