import os
import math

import lib.database as d
import lib.function as f
from lib.function import global_value as g


def plot():
    game_info = d.aggregate.game_info()
    if g.opt.stipulated == 0:  # 規定打数が指定されない場合はレートから計算
        g.opt.stipulated = (
            math.ceil(game_info["game_count"] * g.opt.stipulated_rate) + 1
        )
        g.prm.update(g.opt)

    # データ集計
    df = d.aggregate.matrix_table()

    # 表示
    msg = "*【対局対戦マトリックス】*\n"
    msg += f.message.header(game_info, vars(g.prm), "", 1)

    if df.empty:
        return (msg, {})

    # 保存
    file_name = os.path.join(
        g.work_dir,
        f"{g.opt.filename}" if g.opt.filename else "matrix"
    )

    if g.opt.format == "csv":
        file_path = file_name + ".csv"
        df.to_csv(file_path)
    else:
        file_path = file_name + ".txt"
        df.to_markdown(file_path, tablefmt="outline")

    return (msg, {"対局対戦マトリックス表": file_path})
