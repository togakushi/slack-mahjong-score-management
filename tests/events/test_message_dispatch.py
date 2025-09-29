"""
tests/events/test_message_dispatch.py
"""

import sys
from typing import cast
from unittest.mock import patch

import pytest

import libs.dispatcher
import libs.global_value as g
from integrations import factory
from libs.functions import configuration
from tests.events import param_data


@pytest.mark.parametrize(
    "config, keyword",
    list(param_data.message_help.values()),
    ids=list(param_data.message_help.keys()),
)
def test_help_event(config, keyword, monkeypatch):
    """キーワード呼び出しテスト(help)"""
    monkeypatch.setattr(sys, "argv", ["progname", "--service=std", f"--config=tests/testdata/{config}"])

    with (
        patch("libs.functions.configuration.compose.msg_help.event_message") as mock_help_event,
    ):
        configuration.setup()
        adapter = factory.select_adapter("standard_io", g.cfg)

        m = adapter.parser()
        m.data.text = keyword
        m.data.status = "message_append"
        m.set_command_flag(False)

        libs.dispatcher.by_keyword(m)
        mock_help_event.assert_called_once()


@pytest.mark.parametrize(
    "module, config, keyword",
    list(param_data.message_event.values()),
    ids=list(param_data.message_event.keys()),
)
def test_keyword_event(module, config, keyword, monkeypatch):
    """キーワード呼び出しテスト(サブコマンド)"""
    monkeypatch.setattr(sys, "argv", ["progname", "--service=std", f"--config=tests/testdata/{config}"])

    with (
        patch(f"libs.functions.configuration.libs.commands.{module}.entry.main") as mock_keyword_event,
    ):
        configuration.setup()
        adapter = factory.select_adapter("standard_io", g.cfg)

        m = adapter.parser()
        m.data.status = "message_append"
        m.set_command_flag(False)
        m.data.text = keyword

        libs.dispatcher.by_keyword(m)
        mock_keyword_event.assert_called_once()
