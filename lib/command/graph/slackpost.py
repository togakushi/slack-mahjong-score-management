import lib.function as f
from lib.function import global_value as g

from lib.command.graph import summary
from lib.command.graph import personal


def main(client, channel, argument):
    """
    ポイント推移グラフをslackにpostする

    Parameters
    ----------
    client : obj

    channel : str
        post先のチャンネルID or ユーザーID

    argument : list
        slackから受け取った引数
        解析対象のプレイヤー、検索範囲などが指定される
    """

    g.opt.initialization("graph", argument)
    g.prm.update(g.opt)

    if len(g.prm.player_list) == 1: # 対象がひとり → 個人成績
        count, ret = personal.plot()
    else: # 対象が複数 → 比較
        if g.opt.order:
            count, ret = summary.rank_plot()
        else:
            count, ret = summary.point_plot()

    if count == 0:
        f.slack_api.post_message(client, channel, ret)
    else:
        f.slack_api.post_fileupload(client, channel, "成績グラフ", ret)
