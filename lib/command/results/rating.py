import math

import global_value as g
from lib import command as c
from lib import database as d
from lib import function as f


def aggregation():
    """
    レーティングを集計して返す
    """

    # ゲスト強制除外
    g.opt.guest_skip = True

    # データ収集
    game_info = d.aggregate.game_info()
    df_ratings = d.aggregate.calculation_rating()

    # 最終的なレーティング
    final = df_ratings.ffill().tail(1).transpose()
    final["count"] = df_ratings.count()
    final.columns = ["rate", "count"]
    final = final.sort_values(by="rate", ascending=False)

    if g.opt.stipulated == 0:  # 規定打数が指定されない場合はレートから計算
        g.opt.stipulated = (
            math.ceil(game_info["game_count"] * g.opt.stipulated_rate) + 1
        )
        g.prm.update(g.opt)

    # 足切り
    final = final.query("count >= @g.opt.stipulated")

    # ゲスト置換
    if g.opt.unregistered_replace:
        for player in final.index:
            if player not in g.member_list:
                final = final.copy().drop(player)
    final["name"] = final.copy().index
    final["名前"] = final["name"].copy().apply(
        lambda x: c.member.NameReplace(x, add_mark=True)
    )

    # 表示
    # --- 情報ヘッダ
    add_text = ""
    headline = "*【レーティング】*\n"
    headline += f.message.header(game_info, add_text, 1)

    final.rename(columns={
        "rate": "レート",
        "count": "ゲーム数",
    }, inplace=True)
    final = final.filter(items=["名前", "レート", "ゲーム数"])
    msg = final.to_markdown(
        index=False,
        tablefmt="simple",
        numalign="right",
        maxheadercolwidths=8,
        floatfmt=("", ".1f", ".0f")
    )
    msg = f"```\n{msg}\n```\n"

    return (headline, msg)
