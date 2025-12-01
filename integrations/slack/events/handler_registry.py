"""
integrations/slack/events/handler_registry.py
"""

import logging
from typing import TYPE_CHECKING, Callable

from integrations.slack.adapter import ServiceAdapter

if TYPE_CHECKING:
    from slack_bolt import App

_registry: list[Callable] = []


def register(fn: Callable):
    """登録関数をグローバルレジストリに追加"""
    _registry.append(fn)


def register_all(app: "App", adapter: ServiceAdapter):
    """すべての登録関数を呼び出す"""
    for fn in _registry:
        logging.trace("Calling: %s", fn.__name__)  # type: ignore
        fn(app, adapter)
