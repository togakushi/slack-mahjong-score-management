"""
integrations/slack/events/handler_registry.py
"""

import logging
from typing import Callable

from integrations.slack.adapter import AdapterInterface

_registry: list[Callable] = []


def register(fn: Callable):
    """登録関数をグローバルレジストリに追加"""
    _registry.append(fn)


def register_all(app, adapter: AdapterInterface):
    """すべての登録関数を呼び出す"""
    for fn in _registry:
        logging.trace("Calling: %s", fn.__name__)  # type: ignore
        fn(app, adapter)
