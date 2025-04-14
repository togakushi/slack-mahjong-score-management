"""
lib/command/report/matrix.py
"""

import os

import lib.global_value as g
from cls.types import GameInfoDict
from lib import database as d
from lib import function as f
from lib.command.member import anonymous_mapping


def plot():
    """対局対戦マトリックスの表示

    Returns:
        Tuple[str,dict]:
            - str: ヘッダ情報
            - dict: 生成ファイル情報
    """

    # データ集計
    game_info: GameInfoDict = d.aggregate.game_info()
    df = d.aggregate.matrix_table()
    if g.params.get("anonymous"):
        mapping_dict = anonymous_mapping(df.index.tolist())
        df = df.rename(columns=mapping_dict, index=mapping_dict)

    # 表示
    msg = "*【対局対戦マトリックス】*\n"
    msg += f.message.header(game_info, "", 1)

    if df.empty:
        return (msg, {})

    # 保存
    file_name = os.path.join(
        g.cfg.setting.work_dir,
        f"{g.params["filename"]}" if g.params.get("filename") else "matrix",
    )

    if g.params.get("format", "default").lower() == "csv":
        file_path = file_name + ".csv"
        df.to_csv(file_path)
    else:
        file_path = file_name + ".txt"
        df.to_markdown(file_path, tablefmt="outline")

    return (msg, {"対局対戦マトリックス表": file_path})
