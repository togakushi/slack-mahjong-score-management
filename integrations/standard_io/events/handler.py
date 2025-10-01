"""
integrations/standard_io/events/handler.py
"""

import libs.dispatcher
import libs.global_value as g


def main(adapter: g.std_adapter):
    """メイン処理"""

    m = adapter.parser()
    m.parser({"event": {"text": g.args.text}})

    # キーワード処理
    libs.dispatcher.by_keyword(m)
