"""
integrations/web/events/handler.py
"""

import pandas as pd
from flask import Flask, render_template, request

import libs.event_dispatcher
import libs.global_value as g
from integrations import factory
from integrations.web import functions
from libs.data import lookup
from libs.utils import dbutil


def main():
    """メイン処理"""

    m = factory.select_parser(g.selected_service, **g.cfg.setting.to_dict())
    app = Flask(__name__, static_folder="../../../files/html", template_folder="../../../files/html")

    padding = "0.25em 1.5em"

    @app.route("/")
    def index():
        return app.send_static_file("index.html")

    @app.route("/summary", methods=["GET", "POST"])
    def summary(padding=padding):
        m.data.status = "message_append"
        m.post.message = {}

        cookie_data = functions.get_cookie(request)

        text = " ".join(cookie_data.values())
        m.data.text = f"{g.cfg.cw.results} {text}"
        libs.event_dispatcher.dispatch_by_keyword(m)

        message = ""
        title, headline = next(iter(m.post.headline.items()))
        if not title.isnumeric() and title:
            message = f"<h1>{title}</h1>"
        message += headline.replace("\n", "<br>")

        for k, v in m.post.message.items():
            if not k.isnumeric() and k:
                message += f"<h2>{k}</h2>"

            if isinstance(v, pd.DataFrame):
                # 戦績(詳細)はマルチカラムで表示
                if k == "戦績" and g.params.get("verbose"):
                    padding = "0.25em 0.75em"
                    if not isinstance(v.columns, pd.MultiIndex):
                        new_columns = [tuple(col.split(" ")) if " " in col else ("", col) for col in v.columns]
                        v.columns = pd.MultiIndex.from_tuples(new_columns, names=["座席", "項目"])

                message += functions.to_styled_html(v, padding)
            else:
                message += v.replace("\n", "<br>")

        cookie_data.update(body=message)
        page = functions.set_cookie("summary.html", request, cookie_data)

        return page

    @app.route("/graph", methods=["GET", "POST"])
    def graph():
        m.data.status = "message_append"
        m.post.message = {}
        cookie_data = functions.get_cookie(request)

        text = " ".join(cookie_data.values())
        m.data.text = f"{g.cfg.cw.graph} {text}"
        libs.event_dispatcher.dispatch_by_keyword(m)

        message = ""
        title, headline = next(iter(m.post.headline.items()))
        if not title.isnumeric() and title:
            message = f"<h1>{title}</h1>"

        for file_list in m.post.file_list:
            _, file_path = next(iter(file_list.items()))
            if file_path:
                with open(file_path, encoding="utf-8") as f:
                    message += f.read()
            else:
                message += headline.replace("\n", "<br>")

        cookie_data.update(body=message)
        page = functions.set_cookie("graph.html", request, cookie_data)

        return page

    @app.route("/ranking", methods=["GET", "POST"])
    def ranking():
        m.data.status = "message_append"
        m.post.message = {}
        cookie_data = functions.get_cookie(request)

        text = " ".join(cookie_data.values())
        m.data.text = f"{g.cfg.cw.ranking} {text}"
        libs.event_dispatcher.dispatch_by_keyword(m)

        message = ""
        title, headline = next(iter(m.post.headline.items()))
        if not title.isnumeric() and title:
            message = f"<h1>{title}</h1>"
        message += headline.replace("\n", "<br>")

        for k, v in m.post.message.items():
            if not k.isnumeric() and k:
                message += f"<h2>{k}</h2>"

            if isinstance(v, pd.DataFrame):
                message += functions.to_styled_html(v, padding)
            elif isinstance(v, str):
                message += v.replace("\n", "<br>")

        cookie_data.update(body=message)
        page = functions.set_cookie("ranking.html", request, cookie_data)

        return page

    @app.route("/detail", methods=["GET", "POST"])
    def detail(padding=padding):
        m.data.status = "message_append"
        m.post.message = {}
        cookie_data = functions.get_cookie(request)

        text = " ".join(cookie_data.values())
        m.data.text = f"{g.cfg.cw.results} {text}"
        libs.event_dispatcher.dispatch_by_keyword(m)

        players = lookup.internal.get_member()
        message = ""

        title, headline = next(iter(m.post.headline.items()))
        if not title.isnumeric() and title:
            message = f"<h1>{title}</h1>"
        message += headline.replace("\n", "<br>")

        for k, v in m.post.message.items():
            if not k.isnumeric() and k:
                message += f"<h2>{k}</h2>"
            if isinstance(v, pd.DataFrame):
                # 戦績(詳細)はマルチカラムで表示
                if k == "戦績" and g.params.get("verbose"):
                    padding = "0.25em 0.75em"
                    if not isinstance(v.columns, pd.MultiIndex):
                        new_columns = [tuple(col.split(" ")) if " " in col else ("", col) for col in v.columns]
                        v.columns = pd.MultiIndex.from_tuples(new_columns, names=["座席", "項目"])
                message += functions.to_styled_html(v, padding)
            else:
                message += v.replace("\n", "<br>")

        cookie_data.update(body=message, players=players)
        page = functions.set_cookie("detail.html", request, cookie_data)

        return page

    @app.route("/management")
    def management():
        df = pd.read_sql(
            sql="select member.name, team.name as team from member left join team on member.team_id == team.id where member.id != 0;",
            con=dbutil.get_connection(),
            params=g.params,
        )
        message = functions.to_styled_html(df, padding)
        return render_template("page.html", body=message)

    app.run(host=g.args.host, port=g.args.port)
