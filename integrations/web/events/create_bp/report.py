"""
integrations/web/events/report.py
"""

from dataclasses import asdict
from typing import TYPE_CHECKING

import pandas as pd
from flask import Blueprint, abort, request, current_app

import libs.dispatcher
import libs.global_value as g

if TYPE_CHECKING:
    from integrations.web.adapter import ServiceAdapter


def report_bp(adapter: "ServiceAdapter"):
    bp = Blueprint("report", __name__, url_prefix="/report")

    @bp.route("/", methods=["GET", "POST"])
    def report():
        if not adapter.conf.view_report:
            abort(403)

        padding = current_app.config["padding"]

        m = adapter.parser()
        cookie_data = adapter.functions.get_cookie(request)
        text = " ".join(cookie_data.values())
        m.data.text = f"{g.cfg.report.commandword[0]} {text}"
        libs.dispatcher.by_keyword(m)

        message = adapter.functions.header_message(m)
        for k, v in m.post.message.items():
            if not k.isnumeric() and k:
                message += f"<h2>{k}</h2>\n"

            if isinstance(v, pd.DataFrame):
                if "個人成績一覧" in m.post.headline.keys():
                    check_column = v.columns.to_list()
                    multi = [
                        ("", "名前"),
                        ("", "ゲーム数"),
                        ("ポイント", "通算") if {"通算", "平均"}.issubset(check_column) else None,
                        ("ポイント", "平均") if {"通算", "平均"}.issubset(check_column) else None,
                        ("1位", "獲得数") if {"1位数", "1位率"}.issubset(check_column) else None,
                        ("1位", "獲得率") if {"1位数", "1位率"}.issubset(check_column) else None,
                        ("2位", "獲得数") if {"2位数", "2位率"}.issubset(check_column) else None,
                        ("2位", "獲得率") if {"2位数", "2位率"}.issubset(check_column) else None,
                        ("3位", "獲得数") if {"3位数", "3位率"}.issubset(check_column) else None,
                        ("3位", "獲得率") if {"3位数", "3位率"}.issubset(check_column) else None,
                        ("4位", "獲得数") if {"4位数", "4位率"}.issubset(check_column) else None,
                        ("4位", "獲得率") if {"4位数", "4位率"}.issubset(check_column) else None,
                        ("平均順位", "") if {"平均順位", "平順"} & set(check_column) else None,
                        ("トビ", "回数") if {"トビ数", "トビ率"}.issubset(check_column) else None,
                        ("トビ", "率") if {"トビ数", "トビ率"}.issubset(check_column) else None,
                        ("役満", "和了数") if {"役満和了数", "役満和了率"}.issubset(check_column) else None,
                        ("役満", "和了率") if {"役満和了数", "役満和了率"}.issubset(check_column) else None,
                    ]
                    v.columns = pd.MultiIndex.from_tuples([x for x in multi if x is not None])
                message += adapter.functions.to_styled_html(v, padding, m.post.index)
            elif isinstance(v, str):
                message += f"<p>\n{v.replace("\n", "<br>\n")}</p>\n"

        cookie_data.update(body=message, **asdict(adapter.conf))
        page = adapter.functions.set_cookie("report.html", request, cookie_data)

        return page

    return bp
