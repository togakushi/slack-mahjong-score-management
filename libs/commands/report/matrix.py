"""
libs/commands/report/matrix.py
"""

from typing import TYPE_CHECKING

import libs.global_value as g
from libs.data import aggregate
from libs.datamodels import GameInfo
from libs.functions import message
from libs.types import StyleOptions
from libs.utils import formatter, textutil

if TYPE_CHECKING:
    from integrations.protocols import MessageParserProtocol


def plot(m: "MessageParserProtocol"):
    """対局対戦マトリックスの表示

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    # データ集計
    title: str = "対局対戦マトリックス"
    game_info = GameInfo()
    df = aggregate.matrix_table()
    if g.params.get("anonymous"):
        mapping_dict = formatter.anonymous_mapping(df.index.tolist())
        df = df.rename(columns=mapping_dict, index=mapping_dict)

    if df.empty:
        m.post.headline = {title: message.random_reply(m, "no_target")}
        m.status.result = False
        return

    if str(g.params.get("format", "default")).lower() == "csv":
        file_path = textutil.save_file_path("matrix.csv", True)
        df.to_csv(file_path)
    else:
        file_path = textutil.save_file_path("matrix.txt", True)
        df.to_markdown(file_path, tablefmt="outline")

    m.post.headline = {title: message.header(game_info, m, "", 1)}
    match g.adapter.interface_type:
        case "slack":
            m.set_data(title, file_path, StyleOptions(use_comment=True, header_hidden=True))
        case "web":
            m.set_data("", df, StyleOptions(show_index=True))
