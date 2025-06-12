"""
tests/database/test_registration.py
"""

from contextlib import closing

import pytest

import libs.global_value as g
from libs.registry import member, team
from libs.utils import dbutil
from tests.database import param_data


def test_guest_name():
    """ゲスト登録チェック"""
    with closing(dbutil.get_connection()) as conn:
        cur = conn.execute("select name from member where id = 0;")
        row = dict(cur.fetchone())

    assert row is not None
    assert row.get("name") == g.cfg.member.guest_name


@pytest.mark.parametrize(
    "user_name, ret_meg, registered",
    list(param_data.user_add_case_01.values()),
    ids=list(param_data.user_add_case_01.keys())
)
def test_member_add(user_name, ret_meg, registered):
    """ユーザ登録テスト"""
    ret = member.append(str(user_name).split())
    assert ret_meg in ret

    with closing(dbutil.get_connection()) as conn:
        cur = conn.execute("select name from member;")
        rows = cur.fetchall()
        assert rows is not None

    check_name = str(user_name).split()[0]
    name_list = [dict(row).get("name") for row in rows]
    print(f"in: {check_name} result: {ret}")
    assert (check_name in name_list) == registered


@pytest.mark.parametrize(
    "team_name, ret_meg, registered",
    list(param_data.team_add_case_01.values()),
    ids=list(param_data.team_add_case_01.keys())
)
def test_team_create(team_name, ret_meg, registered):
    """チーム作成テスト"""
    ret = team.create(str(team_name).split())
    assert ret_meg in ret

    with closing(dbutil.get_connection()) as conn:
        cur = conn.execute("select name from team;")
        rows = cur.fetchall()
        assert rows is not None

    check_name = str(team_name).split()[0]
    name_list = [dict(row).get("name") for row in rows]
    print(f"in: {check_name} result: {ret}")
    assert (check_name in name_list) == registered
