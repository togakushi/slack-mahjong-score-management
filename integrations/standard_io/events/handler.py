"""
integrations/standard_io/events/handler.py
"""

from typing import TYPE_CHECKING

import libs.dispatcher
import libs.global_value as g

if TYPE_CHECKING:
    from integrations.standard_io.adapter import ServiceAdapter


def main(adapter: "ServiceAdapter"):
    """メイン処理"""

    m = adapter.parser()
    m.parser({"event": {"text": g.args.text}})

    # キーワード処理
    libs.dispatcher.by_keyword(m)
