"""
libs/commands/report/monthly.py
"""

import os

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

import libs.global_value as g
from integrations.protocols import MessageParserProtocol
from libs.data import loader
from libs.functions import compose, configuration, message


def plot(m: MessageParserProtocol) -> bool:
    """月別ゲーム統計表の生成

    Args:
        m (MessageParserProtocol): メッセージデータ

    Returns:
        bool: 生成処理結果
        - **True**: レポート生成
        - **False**: 対象データなし
    """

    plt.close()
    # --- データ収集
    df = loader.read_data("report/monthly.sql")
    results = df.transpose().to_dict()

    if len(results) == 0:
        m.post.headline = message.random_reply(m, "no_hits", False)
        return False

    # --- グラフフォント設定
    configuration.graph_setup(plt, fm)
    plt.rcParams["font.size"] = 6

    # 色彩設定
    match (plt.rcParams["text.color"], plt.rcParams["figure.facecolor"]):
        case text_color, bg_color if text_color == "black" and bg_color == "white":
            line_color1 = "#ffffff"
            line_color2 = "#dddddd"
        case text_color, bg_color if text_color == "white" and bg_color == "black":
            line_color1 = "#000000"
            line_color2 = "#111111"
        case _:
            line_color1 = plt.rcParams["figure.facecolor"]
            line_color2 = plt.rcParams["figure.facecolor"]

    column_labels = list(results[list(results.keys())[0]].keys())
    column_color = ["#000080" for i in column_labels]

    cell_param = []
    cell_color = []
    line_count = 0
    for x in results.keys():
        line_count += 1
        cell_param.append([results[x][y] for y in column_labels])
        if int(line_count % 2):
            cell_color.append([line_color1 for i in column_labels])
        else:
            cell_color.append([line_color2 for i in column_labels])

    report_file_path = os.path.join(
        g.cfg.setting.work_dir,
        f"{g.params["filename"]}.png" if g.params.get("filename") else "report.png",
    )

    fig = plt.figure(
        figsize=(6, (len(results) * 0.2) + 0.8),
        dpi=200,
        tight_layout=True
    )
    ax_dummy = fig.add_subplot(111)
    ax_dummy.axis("off")

    plt.title("月別ゲーム統計", fontsize=12)
    tb = plt.table(
        colLabels=column_labels,
        colColours=column_color,
        cellText=cell_param,
        cellColours=cell_color,
        loc="center",
    )

    tb.auto_set_font_size(False)
    for i in range(len(column_labels)):
        tb[0, i].set_text_props(color="#FFFFFF", weight="bold")
    for i in range(len(results.keys()) + 1):
        tb[i, 0].set_text_props(ha="center")

    # 追加テキスト
    fig.text(
        0.01, 0.02,  # 表示位置(左下0,0 右下0,1)
        f"[検索範囲：{compose.text_item.search_range()}] [特記：すべてのゲーム結果を含む]",
        transform=fig.transFigure,
        fontsize=6,
    )

    fig.savefig(report_file_path)
    plt.close()

    m.post.file_list = [{"月別ゲーム統計": report_file_path}]
    return True
