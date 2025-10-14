"""
integrations/web/events/ranking.py
"""

from dataclasses import asdict
from typing import TYPE_CHECKING

import pandas as pd
from flask import Blueprint, abort, request, current_app

import libs.dispatcher
import libs.global_value as g

if TYPE_CHECKING:
    from integrations.web.adapter import ServiceAdapter


def ranking_bp(adapter: "ServiceAdapter") -> Blueprint:
    """ランキングページ用Blueprint

    Args:
        adapter (ServiceAdapter): web用アダプタ

    Returns:
        Blueprint: Blueprint
    """

    bp = Blueprint("ranking", __name__, url_prefix="/ranking")

    @bp.route("/", methods=["GET", "POST"])
    def ranking():
        if not adapter.conf.view_ranking:
            abort(403)

        padding = current_app.config["padding"]

        m = adapter.parser()
        cookie_data = adapter.functions.get_cookie(request)
        text = " ".join(cookie_data.values())
        m.data.text = f"{g.cfg.ranking.commandword[0]} {text}"
        libs.dispatcher.by_keyword(m)

        message = adapter.functions.header_message(m)

        for data in m.post.order:
            for k, v in data.items():
                msg = v.get("data")

                if not k.isnumeric() and k:
                    message += f"<h2>{k}</h2>\n"

                if isinstance(msg, pd.DataFrame):
                    disp = v.get("show_index", False)
                    message += adapter.functions.to_styled_html(msg, padding, disp)

                if isinstance(msg, str):
                    message += adapter.functions.to_text_html(msg)

        cookie_data.update(body=message, **asdict(adapter.conf))
        page = adapter.functions.set_cookie("ranking.html", request, cookie_data)

        return page

    return bp
