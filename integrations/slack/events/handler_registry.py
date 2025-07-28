"""
integrations/slack/events/handler_registry.py
"""

from typing import Callable

_registry: list[Callable] = []


def register(fn: Callable):
    """登録関数をグローバルレジストリに追加"""
    _registry.append(fn)


def register_all(app):
    """すべての登録関数を呼び出す"""
    for fn in _registry:
        fn(app)
