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
        for k, v in m.post.message.items():
            if not k.isnumeric() and k:
                message += f"<h2>{k}</h2>\n"

            if isinstance(v, pd.DataFrame):
                message += adapter.functions.to_styled_html(v, padding)
            elif isinstance(v, str):
                message += f"<p>\n{v.replace("\n", "<br>\n")}</p>\n"

        cookie_data.update(body=message, **asdict(adapter.conf))
        page = adapter.functions.set_cookie("ranking.html", request, cookie_data)

        return page

    return bp
