"""
integrations/standard_io/events/handler.py
"""

import libs.event_dispatcher
import libs.global_value as g
from integrations import factory


def main():
    """メイン処理"""

    adapter = factory.select_adapter("standard_io")
    m = adapter.parser()
    m.parser({"event": {"text": g.args.text}})

    # キーワード処理
    libs.event_dispatcher.dispatch_by_keyword(m)
