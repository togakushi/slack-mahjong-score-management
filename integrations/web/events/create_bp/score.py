"""
integrations/web/events/score.py
"""

from dataclasses import asdict
from typing import TYPE_CHECKING

import pandas as pd
from flask import Blueprint, abort, current_app, render_template, request

import libs.global_value as g
from cls.score import GameResult
from cls.timekit import ExtendedDatetime as ExtDt
from cls.timekit import Format
from libs.data import modify
from libs.types import StyleOptions
from libs.utils import dbutil, formatter

if TYPE_CHECKING:
    from integrations.web.adapter import ServiceAdapter


def score_bp(adapter: "ServiceAdapter") -> Blueprint:
    """スコア管理ページ用Blueprint

    Args:
        adapter (ServiceAdapter): web用アダプタ

    Returns:
        Blueprint: Blueprint
    """

    bp = Blueprint("score", __name__, url_prefix="/score")

    @bp.route("/", methods=["GET", "POST"])
    def mgt_score():
        if not adapter.conf.management_score:
            abort(403)

        padding = current_app.config["padding"]
        players = g.cfg.member.lists
        m = adapter.parser()

        def score_table() -> str:
            df = formatter.df_rename2(
                pd.read_sql(
                    sql="""
                select
                    '<input type="radio" name="ts" value="' || ts || '">' as '#',
                    playtime,
                    p1_name, p1_str,
                    p2_name, p2_str,
                    p3_name, p3_str,
                    p4_name, p4_str,
                    comment, source
                from
                    result
                order by
                    ts desc
                limit 0, 10
                ;
                """,
                    con=dbutil.connection(g.cfg.setting.database_file),
                ),
                options=StyleOptions(),
            )

            if not isinstance(df.columns, pd.MultiIndex):
                new_columns = [tuple(col.split(" ")) if " " in col else ("", col) for col in df.columns]
                df.columns = pd.MultiIndex.from_tuples(new_columns, names=["座席", "項目"])

            return adapter.functions.to_styled_html(df, padding)

        data: dict = asdict(adapter.conf)
        data.update(players=players)

        if request.method == "POST":
            data.update(request.form.to_dict())
            data.update(mode="update")
            data.update(g.cfg.mahjong.to_dict())

            if "ts" in data:
                match request.form.get("action"):
                    case "modify":
                        sql = "select * from result where ts = :ts;"
                        df = pd.read_sql(sql=sql, con=dbutil.connection(g.cfg.setting.database_file), params=data)
                        data.update(next(iter(df.T.to_dict().values())))
                        return render_template("score_input.html", **data)
                    case "delete":
                        m.data.event_ts = request.form.get("ts", "")
                        modify.db_delete(m)
                        data.update(table=score_table())
                        return render_template("score_list.html", **data)
                    case "update":
                        g.params.update({"unregistered_replace": False})
                        data.update(request.form.to_dict(), players=players)
                        if p1_name := request.form.get("p1_other"):
                            data.update(p1_name=formatter.name_replace(p1_name))
                        if p2_name := request.form.get("p2_other"):
                            data.update(p2_name=formatter.name_replace(p2_name))
                        if p3_name := request.form.get("p3_other"):
                            data.update(p3_name=formatter.name_replace(p3_name))
                        if p4_name := request.form.get("p4_other"):
                            data.update(p4_name=formatter.name_replace(p4_name))
                        if not request.form.get("comment"):
                            data.update(comment=None)

                        detection = GameResult(**data)
                        detection.source = "web"
                        m.status.source = "web"

                        if data.get("mode") == "insert":
                            modify.db_insert(detection, m)
                        else:
                            modify.db_update(detection, m)

                        data.update(table=score_table())
                        return render_template("score_list.html", **data)
            elif request.form.get("action") == "modify":  # 新規登録
                playtime = ExtDt()
                data.update(mode="insert", playtime=playtime.format(Format.SQL), ts=playtime.format(Format.TS))
                return render_template("score_input.html", **data)

        data.update(table=score_table())
        return render_template("score_list.html", **data)

    return bp
