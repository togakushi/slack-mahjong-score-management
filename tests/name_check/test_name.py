"""
tests/name_check/test_name.py
"""

import sys

import pytest

from libs import configuration
from libs.data import lookup
from libs.utils import validator
from tests.name_check import param_data

TEST_ARGS = ["progname", "--config=tests/test_data/saki.ini"]


@pytest.mark.parametrize(
    "input_args, expected_flags",
    list(param_data.flag_name_pattern_01.values()),
    ids=list(param_data.flag_name_pattern_01.keys()),
)
def test_name_permit(input_args, expected_flags, monkeypatch):
    """メンバー登録テスト(OK)"""
    monkeypatch.setattr(sys, "argv", TEST_ARGS)
    configuration.setup(init_db=False)
    lookup.db.read_memberslist()

    flg, reason = validator.check_namepattern(input_args, "member")
    print(" -->", flg, reason)
    assert flg == expected_flags


@pytest.mark.parametrize(
    "input_args, expected_flags",
    list(param_data.flag_name_pattern_02.values()),
    ids=list(param_data.flag_name_pattern_02.keys()),
)
def test_name_refusal(input_args, expected_flags, monkeypatch):
    """メンバー登録テスト(NG)"""
    monkeypatch.setattr(sys, "argv", TEST_ARGS)
    configuration.setup(init_db=False)
    lookup.db.read_memberslist()

    flg, _ = validator.check_namepattern(input_args, "member")
    assert flg == expected_flags
