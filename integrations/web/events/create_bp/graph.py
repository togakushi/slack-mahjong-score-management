"""
integrations/web/events/graph.py
"""

import os
from dataclasses import asdict
from typing import TYPE_CHECKING

from flask import Blueprint, abort, request

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

        m = adapter.parser()
        cookie_data = adapter.functions.get_cookie(request)
        text = " ".join(cookie_data.values())
        m.data.text = f"{g.cfg.graph.commandword[0]} {text}"
        libs.dispatcher.by_keyword(m)

        message = adapter.functions.header_message(m)

        try:
            _, headline = next(iter(m.post.headline.items()))
            for file_list in m.post.file_list:
                _, file_path = next(iter(file_list.items()))
                if os.path.exists(file_path):
                    with open(file_path, encoding="utf-8") as f:
                        message += f"<p>\n{f.read()}\n</p>\n"
                else:
                    message += f"<p>\n{headline.replace("\n", "<br>")}</p>\n"
        except StopIteration:
            pass

        cookie_data.update(body=message, **asdict(adapter.conf))
        page = adapter.functions.set_cookie("graph.html", request, cookie_data)

        return page

    return bp
