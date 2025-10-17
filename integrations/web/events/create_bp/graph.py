"""
integrations/web/events/graph.py
"""

from dataclasses import asdict
from pathlib import PosixPath
from typing import TYPE_CHECKING

import pandas as pd
from flask import Blueprint, abort, current_app, request

import libs.dispatcher
import libs.global_value as g

if TYPE_CHECKING:
    from integrations.web.adapter import ServiceAdapter


def graph_bp(adapter: "ServiceAdapter") -> Blueprint:
    """グラフ表示ページ用Blueprint

    Args:
        adapter (ServiceAdapter): web用アダプタ

    Returns:
        Blueprint: Blueprint
    """

    bp = Blueprint("graph", __name__, url_prefix="/graph")

    @bp.route("/", methods=["GET", "POST"])
    def graph():
        if not adapter.conf.view_graph:
            abort(403)

        padding = current_app.config["padding"]

        m = adapter.parser()
        cookie_data = adapter.functions.get_cookie(request)
        text = " ".join(cookie_data.values())
        m.data.text = f"{g.cfg.graph.commandword[0]} {text}"
        libs.dispatcher.by_keyword(m)

        message = adapter.functions.header_message(m)

        for data in m.post.message:
            for k, v in data.items():
                msg = v.get("data")

                if isinstance(msg, PosixPath) and msg.exists():
                    message += f"<p>\n{msg.read_text(encoding="utf-8")}\n</p>\n"

                if isinstance(msg, pd.DataFrame) and k == "素点情報":
                    show_index = v["options"].show_index
                    msg["ゲーム数"] = msg["ゲーム数"].astype("float")
                    msg.rename(columns={"平均値(x)": "平均値", "中央値(|)": "中央値"}, inplace=True)
                    message += f"<h2>{k}</h2>\n"
                    message += adapter.functions.to_styled_html(msg, padding, show_index)

                if isinstance(msg, pd.DataFrame) and k == "順位/ポイント情報":
                    show_index = v["options"].show_index
                    msg["ゲーム数"] = msg["ゲーム数"].astype("float")
                    multi = [
                        ("", "ゲーム数"),
                        ("1位", "獲得数"),
                        ("1位", "獲得率"),
                        ("2位", "獲得数"),
                        ("2位", "獲得率"),
                        ("3位", "獲得数"),
                        ("3位", "獲得率"),
                        ("4位", "獲得数"),
                        ("4位", "獲得率"),
                        ("", "平均順位"),
                        ("区間成績", "区間ポイント"),
                        ("区間成績", "区間平均"),
                        ("", "通算ポイント"),
                    ]
                    msg.columns = pd.MultiIndex.from_tuples(multi)
                    message += f"<h2>{k}</h2>\n"
                    message += adapter.functions.to_styled_html(msg, padding, show_index)

        cookie_data.update(body=message, **asdict(adapter.conf))
        page = adapter.functions.set_cookie("graph.html", request, cookie_data)

        return page

    return bp
