"""
integrations/web/events/detail.py
"""

from dataclasses import asdict
from typing import TYPE_CHECKING

import pandas as pd
from flask import Blueprint, abort, current_app, request

import libs.dispatcher
import libs.global_value as g

if TYPE_CHECKING:
    from integrations.web.adapter import ServiceAdapter


def detail_bp(adapter: "ServiceAdapter") -> Blueprint:
    """個人成績詳細ページ用Blueprint

    Args:
        adapter (ServiceAdapter): web用アダプタ

    Returns:
        Blueprint: Blueprint
    """

    bp = Blueprint("detail", __name__, url_prefix="/detail")

    @bp.route("/", methods=["GET", "POST"])
    def detail():
        if not adapter.conf.view_summary:
            abort(403)

        padding = current_app.config["padding"]
        players = g.cfg.member.lists

        m = adapter.parser()
        cookie_data = adapter.functions.get_cookie(request)
        text = " ".join(cookie_data.values())
        m.data.text = f"{g.cfg.results.commandword[0]} {text}"
        libs.dispatcher.by_keyword(m)

        message = adapter.functions.header_message(m)

        for data, options in m.post.message:
            if not options.title.isnumeric() and options.title:
                message += f"<h2>{options.title}</h2>\n"

            if isinstance(data, pd.DataFrame):
                show_index = options.show_index
                if options.title == "戦績" and g.params.get("verbose"):
                    padding = "0.25em 0.75em"
                    data = _conv_verbose(data)
                message += adapter.functions.to_styled_html(data, padding, show_index)
                message = message.replace(f">{g.params['player_name']}<", f"><div class='player_name'>{g.params['player_name']}</div><")

            if isinstance(data, str):
                message += adapter.functions.to_text_html(data)

        cookie_data.update(body=message, players=players, **asdict(adapter.conf))
        page = adapter.functions.set_cookie("detail.html", request, cookie_data)

        return page

    return bp


def _conv_verbose(df: pd.DataFrame) -> pd.DataFrame:
    """戦績(詳細)はマルチカラムで表示

    Args:
        df (pd.DataFrame): _description_

    Returns:
        pd.DataFrame: _description_
    """

    if not isinstance(df.columns, pd.MultiIndex):
        new_columns = [tuple(col.split("_")) if len(col.split("_")) != 1 else ("", col) for col in df.columns]
        df.columns = pd.MultiIndex.from_tuples(new_columns, names=["座席", "項目"])

    return df
