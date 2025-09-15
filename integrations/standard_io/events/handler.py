"""
integrations/standard_io/events/handler.py
"""

import libs.event_dispatcher
import libs.global_value as g
from integrations import factory


def main():
    """メイン処理"""

    m = factory.select_parser(g.selected_service)
    m.parser({"event": {"text": g.args.text}})

    # キーワード処理
    libs.event_dispatcher.dispatch_by_keyword(m)
