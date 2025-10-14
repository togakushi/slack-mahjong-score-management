"""
libs/commands/report/winner.py
"""

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt

import libs.global_value as g
from libs.data import loader
from libs.datamodels import GameInfo
from libs.functions import compose, message
from libs.types import StyleOptions
from libs.utils import formatter, graphutil, textutil

if TYPE_CHECKING:
    from integrations.protocols import MessageParserProtocol


def plot(m: "MessageParserProtocol"):
    """成績上位者を一覧化

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    # --- データ取得
    game_info = GameInfo()
    results_df = loader.read_data("REPORT_WINNER")
    if len(results_df) == 0:
        m.post.headline = {"成績上位": message.random_reply(m, "no_hits")}
        m.status.result = False
        return

    # 匿名化
    if g.params.get("anonymous"):
        name_list: list = []
        for col in [f"name{x}" for x in range(1, 6)]:
            name_list.extend(results_df[col].unique().tolist())
        mapping_dict = formatter.anonymous_mapping(list(set(name_list)))
        for col in [f"name{x}" for x in range(1, 6)]:
            results_df[col] = results_df[col].replace(mapping_dict)

    # --- 集計
    results: dict = {}
    for _, v in results_df.iterrows():
        results[v["collection"]] = {}
        results[v["collection"]]["集計月"] = v["collection"]
        for x in range(1, 6):
            if v.isna()[f"point{x}"]:
                results[v["collection"]][f"{x}位"] = "該当者なし"
            else:
                results[v["collection"]][f"{x}位"] = "{} ({}pt)".format(  # pylint: disable=consider-using-f-string
                    v[f"name{x}"],
                    str("{:+}".format(v[f"point{x}"])).replace("-", "▲")  # pylint: disable=consider-using-f-string
                )

    m.post.headline = {"成績上位者": message.header(game_info, m)}

    # --- グラフ設定
    match g.adapter.conf.plotting_backend:
        case "plotly":
            pass
        case _:
            graphutil.setup()
            report_file_path = textutil.save_file_path("report.png")
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
            for _, val in results.items():
                line_count += 1
                cell_param.append([val[y] for y in column_labels])
                if int(line_count % 2):
                    cell_color.append([line_color1 for i in column_labels])
                else:
                    cell_color.append([line_color2 for i in column_labels])

            fig = plt.figure(
                figsize=(6.5, (len(results) * 0.2) + 0.8),
                dpi=200,
                tight_layout=True
            )
            ax_dummy = fig.add_subplot(111)
            ax_dummy.axis("off")

            plt.title("成績上位者", fontsize=12)

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
                for j in range(len(column_labels)):
                    tb[i, j].set_text_props(ha="center")

            # 追加テキスト
            remark_text = "".join(compose.text_item.remarks(True)) + compose.text_item.search_word(True)
            add_text = "{} {}".format(  # pylint: disable=consider-using-f-string
                f"[検索範囲：{compose.text_item.search_range()}]",
                f"[{remark_text}]" if remark_text else "",
            )

            fig.text(
                0.01, 0.02,  # 表示位置(左下0,0 右下0,1)
                add_text,
                transform=fig.transFigure,
                fontsize=6,
            )

            fig.savefig(report_file_path)

    match g.adapter.interface_type:
        case "slack":
            m.set_data("成績上位者", report_file_path, StyleOptions(use_comment=True, header_hidden=True))
        case "web":
            m.set_data("月別集計結果", formatter.df_rename(results_df))
