"""
integrations/web/events/detail.py
"""

from dataclasses import asdict
from typing import TYPE_CHECKING

import pandas as pd
from flask import Blueprint, abort, request, current_app

import libs.dispatcher
import libs.global_value as g

if TYPE_CHECKING:
    from integrations.web.adapter import ServiceAdapter


def detail_bp(adapter: "ServiceAdapter"):
    bp = Blueprint("detail", __name__, url_prefix="/detail")

    @bp.route("/", methods=["GET", "POST"])
    def detail():
        if not adapter.conf.view_summary:
            abort(403)

        padding = current_app.config["padding"]
        players = current_app.config["players"]

        m = adapter.parser()
        cookie_data = adapter.functions.get_cookie(request)
        text = " ".join(cookie_data.values())
        m.data.text = f"{g.cfg.results.commandword[0]} {text}"
        libs.dispatcher.by_keyword(m)

        message = adapter.functions.header_message(m)
        for k, v in m.post.message.items():
            if not k.isnumeric() and k:
                message += f"<h2>{k}</h2>\n"
            if isinstance(v, pd.DataFrame):
                # 戦績(詳細)はマルチカラムで表示
                if k == "戦績" and g.params.get("verbose"):
                    padding = "0.25em 0.75em"
                    if not isinstance(v.columns, pd.MultiIndex):
                        new_columns = [tuple(col.split(" ")) if " " in col else ("", col) for col in v.columns]
                        v.columns = pd.MultiIndex.from_tuples(new_columns, names=["座席", "項目"])
                message += adapter.functions.to_styled_html(v, padding)
            else:
                message += f"<p>\n{v.replace("\n", "<br>\n")}</p>\n"

        cookie_data.update(body=message, players=players, **asdict(adapter.conf))
        page = adapter.functions.set_cookie("detail.html", request, cookie_data)

        return page

    return bp
