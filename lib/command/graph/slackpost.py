import global_value as g
from lib import function as f
from lib.command.graph import personal, rating, summary


def main():
    """
    グラフをslackにpostする
    """

    g.opt.initialization("graph", g.msg.argument)
    g.prm.update(g.opt)

    if len(g.prm.player_list) == 1:  # 対象がひとり
        title = "個人成績"
        if g.opt.statistics:
            count, ret = personal.statistics_plot()
        else:
            count, ret = personal.plot()
    else:  # 対象が複数
        if g.opt.rating:  # レーティング
            title = "レーティング推移"
            count, ret = rating.plot()
        else:
            if g.opt.order:
                title = "順位変動"
                count, ret = summary.rank_plot()
            else:
                title = "ポイント推移"
                count, ret = summary.point_plot()

    if count == 0:
        f.slack_api.post_message(ret)
    else:
        f.slack_api.post_fileupload(title, ret)
