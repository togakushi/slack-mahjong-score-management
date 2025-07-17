"""
libs/commands/ranking/slackpost.py
"""

import copy

import libs.global_value as g
from integrations import factory
from integrations.protocols import MessageParserProtocol
from libs.commands import ranking
from libs.utils import dictutil


def main(m: MessageParserProtocol):
    """ランキングをslackにpostする

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    api_adapter = factory.select_adapter(g.selected_service)

    g.params = dictutil.placeholder(g.cfg.ranking, m)

    if g.params.get("rating"):  # レーティング
        m.post.headline, m.post.message, m.post.file_list = ranking.rating.aggregation(m)
        m.post.summarize = False
        api_adapter.post(m)
    else:  # ランキング
        tmp_m = copy.deepcopy(m)
        tmp_m.post.message, m.post.message = ranking.ranking.aggregation(m)
        res = api_adapter.post_message(tmp_m)
        if m.post.message:
            m.post.ts = str(res.get("ts", "undetermined"))
            api_adapter.post_multi_message(m)
