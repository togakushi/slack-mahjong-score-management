"""
libs/commands/ranking/slackpost.py
"""

import libs.global_value as g
from integrations.slack.functions import conversation
from libs.commands import ranking
from libs.utils import dictutil


def main():
    """ランキングをslackにpostする"""
    g.params = dictutil.placeholder(g.cfg.ranking)

    if g.params.get("rating"):  # レーティング
        msg1, msg2, file_list = ranking.rating.aggregation()
        conversation.slack_post(
            headline=msg1,
            message=msg2,
            summarize=False,
            file_list=file_list,
        )
    else:  # ランキング
        msg1, msg2 = ranking.ranking.aggregation()
        res = conversation.post_message(msg1)
        if msg2:
            conversation.post_multi_message(msg2, res["ts"])
