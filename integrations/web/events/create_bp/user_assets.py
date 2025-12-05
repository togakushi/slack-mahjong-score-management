"""
integrations/web/events/user_assets.py
"""

import os
from typing import TYPE_CHECKING

from flask import Blueprint, abort, request

import libs.global_value as g

if TYPE_CHECKING:
    from integrations.web.adapter import ServiceAdapter


def user_assets_bp(adapter: "ServiceAdapter") -> Blueprint:
    """ユーザー指定CSS用Blueprint

    Args:
        adapter (ServiceAdapter): web用アダプタ

    Returns:
        Blueprint: Blueprint
    """

    bp = Blueprint(
        "user_assets",
        __name__,
        static_folder=os.path.dirname(os.path.join(g.cfg.config_dir, adapter.conf.custom_css)),
        static_url_path="/user_static",
    )

    @bp.before_request
    def restrict_static():
        if not os.path.basename(request.path) == adapter.conf.custom_css:
            abort(403)

    return bp
