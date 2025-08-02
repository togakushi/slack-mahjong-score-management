"""
libs/commands/report/matrix.py
"""

import os

import libs.global_value as g
from cls.types import GameInfoDict
from integrations.protocols import MessageParserProtocol
from libs.data import aggregate
from libs.functions import message
from libs.utils import formatter


def plot(m: MessageParserProtocol) -> bool:
    """対局対戦マトリックスの表示

    Args:
        m (MessageParserProtocol): メッセージデータ

    Returns:
        bool: 生成処理結果
        - **True**: レポート生成
        - **False**: 対象データなし
    """

    # データ集計
    game_info: GameInfoDict = aggregate.game_info()
    df = aggregate.matrix_table()
    if g.params.get("anonymous"):
        mapping_dict = formatter.anonymous_mapping(df.index.tolist())
        df = df.rename(columns=mapping_dict, index=mapping_dict)

    # 表示
    msg = "*【対局対戦マトリックス】*\n"
    msg += message.header(game_info, m, "", 1)

    if df.empty:
        m.post.headline = message.random_reply(m, "no_hits", False)
        return False

    # 保存
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

    m.post.headline = msg
    m.post.file_list = [{"対局対戦マトリックス表": file_path}]
    return True
