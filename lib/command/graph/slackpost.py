import global_value as g
from lib import function as f
from lib.command.graph import personal, summary


def main():
    """
    グラフをslackにpostする
    """

    g.opt.initialization("graph", g.msg.argument)
    g.prm.update(g.opt)

    if len(g.prm.player_list) == 1:  # 対象がひとり → 個人成績
        count, ret = personal.plot()
    else:  # 対象が複数 → 比較
        if g.opt.order:
            count, ret = summary.rank_plot()
        else:
            count, ret = summary.point_plot()

    if g.args.testcase:
        f.common.debug_out(ret, None)
    else:
        if count == 0:
            f.slack_api.post_message(ret)
        else:
            f.slack_api.post_fileupload("成績グラフ", ret)
