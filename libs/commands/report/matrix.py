"""
libs/commands/report/matrix.py
"""

import os
from typing import TYPE_CHECKING

import libs.global_value as g
from cls.types import GameInfoDict
from libs.data import aggregate
from libs.functions import message
from libs.utils import formatter

if TYPE_CHECKING:
    from integrations.protocols import MessageParserProtocol


def plot(m: "MessageParserProtocol"):
    """対局対戦マトリックスの表示

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    # データ集計
    title: str = "対局対戦マトリックス"
    game_info: "GameInfoDict" = aggregate.game_info()
    df = aggregate.matrix_table()
    if g.params.get("anonymous"):
        mapping_dict = formatter.anonymous_mapping(df.index.tolist())
        df = df.rename(columns=mapping_dict, index=mapping_dict)

    if df.empty:
        m.post.headline = {title: message.random_reply(m, "no_hits", False)}
        m.status.result = False

    file_name = os.path.join(
        g.cfg.setting.work_dir,
        f"{g.params["filename"]}" if g.params.get("filename") else "matrix",
    )

    if str(g.params.get("format", "default")).lower() == "csv":
        file_path = file_name + ".csv"
        df.to_csv(file_path)
    else:
        file_path = file_name + ".txt"
        df.to_markdown(file_path, tablefmt="outline")

    m.post.headline = {title: message.header(game_info, m, "", 1)}
    m.post.message = {"": df}
    m.post.index = True
    m.post.file_list = [{title: file_path}]
