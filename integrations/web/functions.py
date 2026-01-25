"""
integrations/web/functions.py
"""

import re
from typing import TYPE_CHECKING

from flask import make_response, render_template

from integrations.base.interface import FunctionsInterface
from libs.types import StyleOptions
from libs.utils import formatter

if TYPE_CHECKING:
    import pandas as pd
    from flask import Request, Response

    from integrations.base.interface import MessageParserProtocol


class SvcFunctions(FunctionsInterface):
    """WebUI専用関数"""

    def to_styled_html(self, df: "pd.DataFrame", padding: str, index: bool = False) -> str:
        """データフレームをHTML表に変換

        Args:
            df (pd.DataFrame): 変換元データ
            padding (str): パディング
            index (bool): インデックスの表示

        Returns:
            str: HTML表
        """

        df = formatter.df_rename(df, StyleOptions(rename_type=StyleOptions.RenameType.NORMAL))
        df = df.rename(columns={"name": "プレイヤー名", "point": "ポイント", "rank": "順位"}).copy()
        styled = (
            df.style.format(
                {
                    "通算": "{:+.1f}pt",
                    "ポイント": "{:+.1f}pt",
                    "獲得ポイント": "{:+.1f}pt",
                    ("東家", "ポイント"): "{:+.1f}pt",
                    ("南家", "ポイント"): "{:+.1f}pt",
                    ("西家", "ポイント"): "{:+.1f}pt",
                    ("北家", "ポイント"): "{:+.1f}pt",
                    "順位": "{:.0f}位",
                    "平均": "{:+.1f}pt",
                    "順位差": "{:.1f}pt",
                    "トップ差": "{:.1f}pt",
                    "ポイント合計": "{:.1f}pt",
                    "ゲーム参加率": "{}",
                    "通算ポイント": "{}",
                    "平均ポイント": "{}",
                    "最大獲得ポイント": "{}",
                    "平均収支": "{}",
                    "平均素点": "{}",
                    "平均順位": "{}",
                    "1位率": "{}",
                    "連対率": "{}",
                    "ラス回避率": "{}",
                    "トビ率": "{}",
                    "役満和了率": "{}",
                    "レート": "{:.1f}",
                    "順位偏差": "{:.0f}",
                    "得点偏差": "{:.0f}",
                    "経過日数": "{:.0f} 日",
                    "プレイ回数": "{:.0f} ゲーム",
                    # レポート
                    ("ポイント", "通算"): "{:+.1f}pt",
                    ("ポイント", "平均"): "{:+.1f}pt",
                    ("1位", "獲得率"): "{:.2%}",
                    ("2位", "獲得率"): "{:.2%}",
                    ("3位", "獲得率"): "{:.2%}",
                    ("4位", "獲得率"): "{:.2%}",
                    ("トビ", "率"): "{:.2%}",
                    ("役満", "和了率"): "{:.2%}",
                    ("1位", "獲得ポイント"): "{:+.1f}pt",
                    ("2位", "獲得ポイント"): "{:+.1f}pt",
                    ("3位", "獲得ポイント"): "{:+.1f}pt",
                    ("4位", "獲得ポイント"): "{:+.1f}pt",
                    ("5位", "獲得ポイント"): "{:+.1f}pt",
                    # 成績統計
                    "ゲーム数": "{:.0f}",
                    ("", "ゲーム数"): "{:.0f}",
                    ("1位", "獲得数"): "{:.0f}",
                    ("2位", "獲得数"): "{:.0f}",
                    ("3位", "獲得数"): "{:.0f}",
                    ("4位", "獲得数"): "{:.0f}",
                    ("", "平均順位"): "{:.2f}",
                    ("区間成績", "区間ポイント"): "{:+.1f}pt",
                    ("区間成績", "区間平均"): "{:+.1f}pt",
                    ("", "通算ポイント"): "{:+.1f}pt",
                },
                na_rep="-----",
            )
            .set_table_attributes('class="data_table"')
            .set_table_styles(
                [
                    {
                        "selector": "th",
                        "props": [
                            ("color", "#ffffff"),
                            ("background-color", "#000000"),
                            ("text-align", "center"),
                            ("padding", padding),
                        ],
                    },
                    {"selector": "td", "props": [("text-align", "center"), ("padding", padding)]},
                    {"selector": "tr:nth-child(odd)", "props": [("background-color", "#f0f0f0f0")]},
                    {"selector": "tr:nth-child(even)", "props": [("background-color", "#dfdfdfdf")]},
                ]
            )
        )
        if not index:
            styled = styled.hide(axis="index")

        ret = styled.to_html()
        ret = re.sub(r" >-(\d+)</td>", r" >▲\1</td>", ret)  # 素点
        ret = re.sub(r" >-(\d+\.\d)(点?)</td>", r" >▲\1\2</td>", ret)  # 素点(小数点付き)
        ret = re.sub(r" >-(\d+\.\d)pt</td>", r" >▲\1pt</td>", ret)  # ポイント

        return ret

    def to_text_html(self, text: str) -> str:
        """テキストをHTMLに変換

        Args:
            text (str): 変換元

        Returns:
            str: 返還後
        """

        ret: str = "<p>\n"
        for line in text.splitlines():
            ret += f"{line.strip()}<br>\n"
        ret += "</p>\n"

        return ret

    def header_message(self, m: "MessageParserProtocol") -> str:
        """ヘッダ情報取得

        Args:
            m (MessageParserProtocol): メッセージデータ

        Returns:
            str: 取得文字列
        """

        message = ""
        if m.post.headline:
            title, headline = next(iter(m.post.headline.items()))
            if not title.isnumeric() and title:
                message = f"<h1>{title}</h1>\n"
            message += f"<p>\n{headline.replace('\n', '<br>\n')}</p>\n"

        return message

    def set_cookie(self, html: str, req: "Request", data: dict) -> "Response":
        """cookie保存

        Args:
            html (str): テンプレートHTML
            req (Request): Request
            data (dict): データ

        Returns:
            Response: Response
        """

        page = make_response(render_template(html, **data))
        if req.method == "POST":
            if req.form.get("action") == "reset":  # cookie削除
                for k in req.cookies.keys():
                    page.delete_cookie(k, path=req.path)
            else:
                for k, v in req.form.to_dict().items():
                    if k == "action":
                        continue
                    page.set_cookie(k, v, path=req.path)

        return page

    def get_cookie(self, req: "Request") -> dict:
        """cookie取得

        Args:
            req (Request): Request

        Returns:
            dict: cookieデータ
        """

        initial_value: dict = {
            "range": "",
            "guest": "ゲストなし",
            "display": "",
            "result": "",
            "collect": "",
        }

        target_keys: list = [
            "collect",
            "display",
            "guest",
            "player",
            "range",
            "result",
            "text",
        ]

        if req.method == "POST":
            cookie_data = req.form.to_dict()
            if req.form.get("action") == "reset":
                cookie_data = initial_value
            else:
                cookie_data.pop("action")
        else:
            cookie_data = initial_value
            cookie_data.update(req.cookies)

        return {k: v for k, v in cookie_data.items() if k in target_keys}

    def get_conversations(self, m: "MessageParserProtocol") -> dict:
        """abstractmethod dummy"""

        _ = m
        return {}

    def post_processing(self, m: "MessageParserProtocol"):
        """abstractmethod dummy"""

        _ = m
