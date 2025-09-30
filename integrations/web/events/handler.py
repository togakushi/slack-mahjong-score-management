"""
integrations/web/events/handler.py
"""

import os
from dataclasses import asdict

import pandas as pd
from flask import Blueprint, Flask, abort, render_template, request
from flask_httpauth import HTTPBasicAuth  # type: ignore

import libs.dispatcher
import libs.global_value as g
from cls.score import GameResult
from cls.timekit import ExtendedDatetime as ExtDT
from integrations.web.adapter import ServiceAdapter
from libs.data import loader, lookup, modify
from libs.registry import member, team
from libs.utils import dbutil, formatter


def main(adapter: ServiceAdapter):
    """メイン処理"""

    app = Flask(
        __name__,
        static_folder=os.path.join(g.cfg.script_dir, "files/html/static"),
        template_folder=os.path.join(g.cfg.script_dir, "files/html/template"),
    )
    user_assets_bp = Blueprint(
        "user_assets",
        __name__,
        static_folder=os.path.dirname(os.path.join(g.cfg.config_dir, adapter.conf.custom_css)),
        static_url_path="/user_static"
    )
    auth = HTTPBasicAuth()

    m = adapter.parser()

    padding = "0.25em 1.5em"
    players = lookup.internal.get_member()

    @user_assets_bp.before_request
    def restrict_static():
        if not os.path.basename(request.path) == adapter.conf.custom_css:
            abort(403)

    @auth.verify_password
    def verify_password(username, password):
        if username == adapter.conf.username and password == adapter.conf.password:
            return True
        return False

    @app.before_request
    def require_auth():
        if adapter.conf.require_auth:
            return auth.login_required(lambda: None)()
        return None

    @app.route("/")
    def index():
        m.post.reset()
        return render_template("index.html", **asdict(adapter.conf))

    @app.route("/summary", methods=["GET", "POST"])
    def summary(padding=padding):
        if not adapter.conf.view_summary:
            abort(403)

        m.post.reset()
        cookie_data = adapter.functions.get_cookie(request)
        text = " ".join(cookie_data.values())
        m.data.text = f"{g.cfg.results.commandword[0]} {text}"
        libs.dispatcher.by_keyword(m)

        message = ""
        title, headline = next(iter(m.post.headline.items()))
        if not title.isnumeric() and title:
            message = f"<h1>{title}</h1>\n"
        message += f"<p>\n{headline.replace("\n", "<br>\n")}</p>\n"

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

        cookie_data.update(body=message, **asdict(adapter.conf))
        page = adapter.functions.set_cookie("summary.html", request, cookie_data)

        return page

    @app.route("/graph", methods=["GET", "POST"])
    def graph():
        if not adapter.conf.view_graph:
            abort(403)

        m.post.message = {}
        cookie_data = adapter.functions.get_cookie(request)
        text = " ".join(cookie_data.values())
        m.data.text = f"{g.cfg.graph.commandword[0]} {text}"
        libs.dispatcher.by_keyword(m)

        message = ""
        try:
            _, headline = next(iter(m.post.headline.items()))
            for file_list in m.post.file_list:
                _, file_path = next(iter(file_list.items()))
                if os.path.exists(file_path):
                    with open(file_path, encoding="utf-8") as f:
                        message += f.read()
                else:
                    message += f"<p>{headline.replace("\n", "<br>")}</p>"
        except StopIteration:
            pass

        cookie_data.update(body=message, **asdict(adapter.conf))
        page = adapter.functions.set_cookie("graph.html", request, cookie_data)

        return page

    @app.route("/ranking", methods=["GET", "POST"])
    def ranking():
        if not adapter.conf.view_ranking:
            abort(403)

        m.post.reset()
        cookie_data = adapter.functions.get_cookie(request)
        text = " ".join(cookie_data.values())
        m.data.text = f"{g.cfg.ranking.commandword[0]} {text}"
        libs.dispatcher.by_keyword(m)

        message = ""
        title, headline = next(iter(m.post.headline.items()))
        if not title.isnumeric() and title:
            message = f"<h1>{title}</h1>\n"
        message += f"<p>\n{headline.replace("\n", "<br>\n")}</p>\n"

        for k, v in m.post.message.items():
            if not k.isnumeric() and k:
                message += f"<h2>{k}</h2>\n"

            if isinstance(v, pd.DataFrame):
                message += adapter.functions.to_styled_html(v, padding)
            elif isinstance(v, str):
                message += f"<p>\n{v.replace("\n", "<br>\n")}</p>\n"

        cookie_data.update(body=message, **asdict(adapter.conf))
        page = adapter.functions.set_cookie("ranking.html", request, cookie_data)

        return page

    @app.route("/detail", methods=["GET", "POST"])
    def detail(padding=padding):
        if not adapter.conf.view_summary:
            abort(403)

        m.post.reset()
        cookie_data = adapter.functions.get_cookie(request)
        text = " ".join(cookie_data.values())
        m.data.text = f"{g.cfg.results.commandword[0]} {text}"
        libs.dispatcher.by_keyword(m)

        message = ""
        title, headline = next(iter(m.post.headline.items()))
        if not title.isnumeric() and title:
            message = f"<h1>{title}</h1>\n"
        message += f"<p>\n{headline.replace("\n", "<br>\n")}</p>\n"

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

    @app.route("/member", methods=["GET", "POST"])
    def mgt_member():
        if not adapter.conf.management_member:
            abort(403)

        data: dict = asdict(adapter.conf)

        if request.method == "POST":
            match request.form.get("action"):
                case "add_member":
                    if (name := request.form.get("member", "").strip()):
                        ret = member.append(name.split()[0:2])
                        data.update(result_msg=next(iter(ret.values())))
                case "del_member":
                    if (name := request.form.get("member", "").strip()):
                        ret = member.remove(name.split()[0:2])
                        data.update(result_msg=next(iter(ret.values())))
                case "add_team":
                    if (team_name := request.form.get("team", "").strip()):
                        ret = team.append(team_name.split()[0:2])
                        data.update(result_msg=next(iter(ret.values())))
                case "del_team":
                    if (team_name := request.form.get("team", "").strip()):
                        ret = team.remove(team_name.split()[0:2])
                        data.update(result_msg=next(iter(ret.values())))
                case "delete_all_team":
                    ret = team.clear()
                    data.update(result_msg=next(iter(ret.values())))

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

    @app.route("/score", methods=["GET", "POST"])
    def mgt_score():
        if not adapter.conf.management_score:
            abort(403)

        def score_table() -> str:
            df = formatter.df_rename(pd.read_sql(
                sql="""
                select
                    '<input type="radio" name="ts" value="' || ts || '">' as '#',
                    playtime,
                    p1_name, p1_str,
                    p2_name, p2_str,
                    p3_name, p3_str,
                    p4_name, p4_str,
                    comment
                from
                    result
                order by
                    ts desc
                limit 0, 10
                ;
                """,
                con=dbutil.connection(g.cfg.setting.database_file)
            ))

            if not isinstance(df.columns, pd.MultiIndex):
                new_columns = [tuple(col.split(" ")) if " " in col else ("", col) for col in df.columns]
                df.columns = pd.MultiIndex.from_tuples(new_columns, names=["座席", "項目"])

            return adapter.functions.to_styled_html(df, padding)

        data: dict = asdict(adapter.conf)
        data.update(players=players)

        if request.method == "POST":
            data.update(request.form.to_dict())
            data.update(mode="update")
            data.update(origin_point=g.cfg.mahjong.origin_point)

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
                        g.params.update(unregistered_replace=False)
                        data.update(request.form.to_dict(), players=players)
                        if (p1_name := request.form.get("p1_other")):
                            data.update(p1_name=formatter.name_replace(p1_name))
                        if (p2_name := request.form.get("p2_other")):
                            data.update(p2_name=formatter.name_replace(p2_name))
                        if (p3_name := request.form.get("p3_other")):
                            data.update(p3_name=formatter.name_replace(p3_name))
                        if (p4_name := request.form.get("p4_other")):
                            data.update(p4_name=formatter.name_replace(p4_name))
                        if not request.form.get("comment"):
                            data.update(comment=None)

                        detection = GameResult(**data, **g.cfg.mahjong.to_dict())
                        if data.get("mode") == "insert":
                            modify.db_insert(detection, m)
                        else:
                            modify.db_update(detection, m)

                        data.update(table=score_table())
                        return render_template("score_list.html", **data)
            elif request.form.get("action") == "modify":  # 新規登録
                playtime = ExtDT()
                data.update(mode="insert", playtime=playtime.format(fmt="sql"), ts=playtime.format(fmt="ts"))
                return render_template("score_input.html", **data)

        data.update(table=score_table())
        return render_template("score_list.html", **data)

    app.register_blueprint(user_assets_bp)

    if adapter.conf.use_ssl:
        if os.path.exists(adapter.conf.certificate) and os.path.exists(adapter.conf.private_key):
            app.run(host=adapter.conf.host, port=adapter.conf.port, ssl_context=(adapter.conf.certificate, adapter.conf.private_key))
        raise FileNotFoundError("certificate or private key not found")
    app.run(host=adapter.conf.host, port=adapter.conf.port)
