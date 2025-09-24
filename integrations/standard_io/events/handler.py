"""
integrations/standard_io/events/handler.py
"""

import libs.event_dispatcher
import libs.global_value as g
from integrations.standard_io.adapter import AdapterInterface


def main(adapter: AdapterInterface):
    """メイン処理"""

    m = adapter.parser()
    m.parser({"event": {"text": g.args.text}})

    # キーワード処理
    libs.event_dispatcher.dispatch_by_keyword(m)
