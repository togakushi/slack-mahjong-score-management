"""
lib/command/report/matrix.py
"""

import os

import lib.global_value as g
from lib import database as d
from lib import function as f


def plot():
    """対局対戦マトリックスの表示

    Returns:
        Tuple[str, dict]:
            - str: ヘッダ情報
            - dict: 生成ファイル情報
    """

    game_info = d.aggregate.game_info()
    g.prm.stipulated_update(g.opt, game_info["game_count"])

    # データ集計
    df = d.aggregate.matrix_table()

    # 表示
    msg = "*【対局対戦マトリックス】*\n"
    msg += f.message.header(game_info, "", 1)

    if df.empty:
        return (msg, {})

    # 保存
    file_name = os.path.join(
        g.cfg.setting.work_dir,
        f"{g.opt.filename}" if g.opt.filename else "matrix"
    )

    if g.opt.format == "csv":
        file_path = file_name + ".csv"
        df.to_csv(file_path)
    else:
        file_path = file_name + ".txt"
        df.to_markdown(file_path, tablefmt="outline")

    return (msg, {"対局対戦マトリックス表": file_path})
