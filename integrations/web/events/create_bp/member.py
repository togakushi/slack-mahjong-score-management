"""
integrations/web/events/member.py
"""

from dataclasses import asdict
from typing import TYPE_CHECKING

from flask import Blueprint, abort, current_app, render_template, request

from libs.configuration import read_memberslist
from libs.data import loader
from libs.registry import member, team

if TYPE_CHECKING:
    from integrations.web.adapter import ServiceAdapter


def member_bp(adapter: "ServiceAdapter") -> Blueprint:
    """メンバー管理ページ用Blueprint

    Args:
        adapter (ServiceAdapter): web用アダプタ

    Returns:
        Blueprint: Blueprint
    """

    bp = Blueprint("member", __name__, url_prefix="/member")

    @bp.route("/", methods=["GET", "POST"])
    def mgt_member():
        if not adapter.conf.management_member:
            abort(403)

        padding = current_app.config["padding"]
        data: dict = asdict(adapter.conf)

        if request.method == "POST":
            match request.form.get("action"):
                case "add_member":
                    if name := request.form.get("member", "").strip():
                        ret = member.append(name.split()[0:2])
                        data.update(result_msg=ret)
                case "del_member":
                    if name := request.form.get("member", "").strip():
                        ret = member.remove(name.split()[0:2])
                        data.update(result_msg=ret)
                case "add_team":
                    if team_name := request.form.get("team", "").strip():
                        ret = team.append(team_name.split()[0:2])
                        data.update(result_msg=ret)
                case "del_team":
                    if team_name := request.form.get("team", "").strip():
                        ret = team.remove(team_name.split()[0:2])
                        data.update(result_msg=ret)
                case "delete_all_team":
                    ret = team.clear()
                    data.update(result_msg=ret)

            read_memberslist(log=False)

        member_df = loader.read_data("MEMBER_INFO")
        if member_df.empty:
            data.update(member_table="<p>登録済みメンバーはいません。</p>")
        else:
            data.update(member_table=adapter.functions.to_styled_html(member_df, padding))

        team_df = loader.read_data("TEAM_INFO")
        if team_df.empty:
            data.update(team_table="<p>登録済みチームはありません。</p>")
        else:
            data.update(team_table=adapter.functions.to_styled_html(team_df, padding))

        return render_template("registry.html", **data)

    return bp
