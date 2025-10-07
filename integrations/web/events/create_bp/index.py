"""
integrations/web/events/index.py
"""

from dataclasses import asdict
from typing import TYPE_CHECKING

from flask import Blueprint, render_template

if TYPE_CHECKING:
    from integrations.web.adapter import ServiceAdapter


def index_bp(adapter: "ServiceAdapter"):
    bp = Blueprint("index", __name__, url_prefix="/")

    @bp.route("/", methods=["GET", "POST"])
    def index():
        return render_template("index.html", **asdict(adapter.conf))

    return bp
