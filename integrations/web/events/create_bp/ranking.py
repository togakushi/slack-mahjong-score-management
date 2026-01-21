"""
integrations/web/events/ranking.py
"""

from dataclasses import asdict
from typing import TYPE_CHECKING

import pandas as pd
from flask import Blueprint, abort, current_app, request

import libs.dispatcher
import libs.global_value as g
from libs.types import StyleOptions
from libs.utils import formatter

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

        for data, options in m.post.message:
            if not options.title.isnumeric() and options.title:
                message += f"<h2>{options.title}</h2>\n"

            if isinstance(data, pd.DataFrame):
                show_index = options.show_index
                message += adapter.functions.to_styled_html(
                    formatter.df_rename2(data, StyleOptions(rename_type=StyleOptions.RenameType.NORMAL)), padding, show_index
                )

            if isinstance(data, str):
                message += adapter.functions.to_text_html(data)

        cookie_data.update(body=message, **asdict(adapter.conf))
        page = adapter.functions.set_cookie("ranking.html", request, cookie_data)

        return page

    return bp
