"""
libs/commands/ranking/slackpost.py
"""

import libs.global_value as g
from integrations import factory
from libs.commands import ranking
from libs.utils import dictutil


def main():
    """ランキングをslackにpostする"""
    api_adapter = factory.select_adapter(g.selected_service)

    g.params = dictutil.placeholder(g.cfg.ranking)

    if g.params.get("rating"):  # レーティング
        msg1, msg2, file_list = ranking.rating.aggregation()
        api_adapter.post(
            headline=msg1,
            message=msg2,
            summarize=False,
            file_list=file_list,
        )
    else:  # ランキング
        msg1, msg2 = ranking.ranking.aggregation()
        res = api_adapter.post_message(msg1)
        if msg2:
            api_adapter.post_multi_message(msg2, res.get("ts"))
