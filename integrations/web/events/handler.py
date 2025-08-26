"""
integrations/web/events/handler.py
"""

import re

import pandas as pd
from flask import Flask, request

import libs.event_dispatcher
import libs.global_value as g
from integrations import factory


def main():
    """メイン処理"""

    m = factory.select_parser(g.selected_service, **g.cfg.setting.to_dict())
    app = Flask(__name__, static_folder="../../../files/html", static_url_path="")

    padding = "0.25em 1.5em"

    @app.route("/")
    def index():
        return app.send_static_file("index.html")

    @app.route("/results")
    def results(padding=padding):
        message = ""
        m.data.status = "message_append"
        m.data.text = f"{g.cfg.cw.results} " + request.args.get("text", "")

        libs.event_dispatcher.dispatch_by_keyword(m)

        title, headline = next(iter(m.post.headline.items()))
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

                styled = (
                    v.style
                    .hide(axis="index")
                    .format(
                        {
                            "通算": "{:+.1f} pt",
                            "ポイント": "{:+.1f} pt",
                            ("東家", "ポイント"): "{:+.1f} pt",
                            ("南家", "ポイント"): "{:+.1f} pt",
                            ("西家", "ポイント"): "{:+.1f} pt",
                            ("北家", "ポイント"): "{:+.1f} pt",
                            "平均": "{:+.1f} pt",
                            "順位差": "{:.1f} pt",
                            "トップ差": "{:.1f} pt",
                        },
                        na_rep="-----",
                    )
                    .set_table_styles([
                        {"selector": "th", "props": [("color", "#ffffff"), ("background-color", "#000000"), ("text-align", "center"), ("padding", padding)]},
                        {"selector": "td", "props": [("text-align", "center"), ("padding", padding)]},
                        {"selector": "tr:nth-child(even)", "props": [("background-color", "#dddddd")]},
                    ])
                )
                message += styled.to_html()
                message = re.sub(r" >-(\d+)</td>", r" >▲\1</td>", message)  # 素点
                message = re.sub(r" >-(\d+\.\d) pt</td>", r" >▲\1 pt</td>", message)  # ポイント
            else:
                message += v.replace("\n", "<br>")

        return message

    @app.route("/graph")
    def graph():
        m.data.status = "message_append"
        m.data.text = f"{g.cfg.cw.graph} " + request.args.get("text", "")

        libs.event_dispatcher.dispatch_by_keyword(m)

        for file_list in m.post.file_list:
            _, file_path = next(iter(file_list.items()))
            if file_path:
                with open(file_path, encoding="utf-8") as f:
                    return f.read()
        return app.send_static_file("index.html")

    @app.route("/ranking")
    def ranking():
        message = ""
        m.data.status = "message_append"
        m.data.text = f"{g.cfg.cw.ranking} " + request.args.get("text", "")

        libs.event_dispatcher.dispatch_by_keyword(m)

        title, headline = next(iter(m.post.headline.items()))
        message = f"<h1>{title}</h1>"
        message += headline.replace("\n", "<br>")
        for k, v in m.post.message.items():
            if not k.isnumeric() and k:
                message += f"<h2>{k}</h2>"

            if isinstance(v, pd.DataFrame):
                styled = (
                    v.style
                    .hide(axis="index")
                    .format(
                        {
                            "ゲーム参加率": "{:.2%}",
                            "通算ポイント": "{:+.1f} pt",
                            "平均ポイント": "{:+.1f} pt",
                            "最大獲得ポイント": "{:.1f} pt",
                            "平均収支": "{:+.1f}",
                            "平均素点": "{:.1f}",
                            "平均順位": "{:.2f}",
                            "1位率": "{:.2%}",
                            "連対率": "{:.2%}",
                            "ラス回避率": "{:.2%}",
                            "トビ率": "{:.2%}",
                            "役満和了率": "{:.2%}",
                            "レート": "{:.1f}",
                            "順位偏差": "{:.0f}",
                            "得点偏差": "{:.0f}",
                        },
                        na_rep="-----",
                    )
                    .set_table_styles([
                        {"selector": "th", "props": [("color", "#ffffff"), ("background-color", "#000000"), ("text-align", "center"), ("padding", padding)]},
                        {"selector": "td", "props": [("text-align", "center"), ("padding", padding)]},
                        {"selector": "tr:nth-child(even)", "props": [("background-color", "#dddddd")]},
                    ])
                )
                message = re.sub(r" >-(\d+)</td>", r" >▲\1</td>", message)  # 素点
                message = re.sub(r" >-(\d+\.\d)</td>", r" >▲\1</td>", message)  # 素点(小数点付き)
                message = re.sub(r" >-(\d+\.\d) pt</td>", r" >▲\1 pt</td>", message)  # ポイント
                message += styled.to_html()
            elif isinstance(v, str):
                message += v.replace("\n", "<br>")

        return message

    app.run(port=8000)
