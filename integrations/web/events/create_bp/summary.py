"""
integrations/web/events/summary.py
"""

from dataclasses import asdict
from typing import TYPE_CHECKING

import pandas as pd
from flask import Blueprint, abort, request, current_app

import libs.dispatcher
import libs.global_value as g

if TYPE_CHECKING:
    from integrations.web.adapter import ServiceAdapter


def summary_bp(adapter: "ServiceAdapter") -> Blueprint:
    """成績サマリページ用Blueprint

    Args:
        adapter (ServiceAdapter): web用アダプタ

    Returns:
        Blueprint: Blueprint
    """

    bp = Blueprint("summary", __name__, url_prefix="/summary")

    @bp.route("/", methods=["GET", "POST"])
    def summary():
        if not adapter.conf.view_summary:
            abort(403)

        padding = current_app.config["padding"]

        m = adapter.parser()
        cookie_data = adapter.functions.get_cookie(request)
        text = " ".join(cookie_data.values())
        m.data.text = f"{g.cfg.results.commandword[0]} {text}"
        libs.dispatcher.by_keyword(m)

        message = adapter.functions.header_message(m)

        for data in m.post.message:
            for k, v in data.items():
                msg = v.get("data")

                if not k.isnumeric() and k:
                    message += f"<h2>{k}</h2>\n"

                if isinstance(msg, pd.DataFrame):
                    show_index = v["options"].show_index
                    if k == "戦績" and g.params.get("verbose"):
                        padding = "0.25em 0.75em"
                        msg = _conv_verbose(msg)

                    message += adapter.functions.to_styled_html(msg, padding, show_index)

                if isinstance(msg, str):
                    message += adapter.functions.to_text_html(msg)

        cookie_data.update(body=message, **asdict(adapter.conf))
        page = adapter.functions.set_cookie("summary.html", request, cookie_data)

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
        if not g.params.get("individual", True):  # チーム戦
            df.rename(columns={
                "東家 名前": "東家 チーム",
                "南家 名前": "南家 チーム",
                "西家 名前": "西家 チーム",
                "北家 名前": "北家 チーム",
            }, inplace=True)
        new_columns = [tuple(col.split(" ")) if " " in col else ("", col) for col in df.columns]
        df.columns = pd.MultiIndex.from_tuples(new_columns, names=["座席", "項目"])

    return df
