"""
integrations/web/functions.py
"""

import re
from configparser import ConfigParser
from dataclasses import dataclass, field, fields
from typing import cast

import pandas as pd
from flask import Request, Response, make_response, render_template

import libs.global_value as g


@dataclass
class Config:
    """設定値"""
    host: str = field(default="")
    port: int = field(default="")

    require_auth: bool = field(default=False)
    username: str = field(default="")
    password: str = field(default="")

    use_ssl: bool = field(default=False)
    certificate: str = field(default="")
    private_key: str = field(default="")

    view_summary: bool = field(default=True)
    view_graph: bool = field(default=True)
    view_ranking: bool = field(default=True)
    management_member: bool = field(default=False)
    management_score: bool = field(default=False)


def load_config() -> Config:
    """設定ファイル読み込み"""

    cfg = Config()
    section = "web"
    parser = cast(ConfigParser, getattr(g.cfg, "_parser"))

    if parser.has_section(section):
        for f in fields(Config):
            if parser.has_option(section, f.name):
                if f.type is int:
                    value = parser.getint(section, f.name)
                elif f.type is bool:
                    value = parser.getboolean(section, f.name)
                elif f.type is str:
                    value = parser.get(section, f.name)
                else:
                    raise TypeError(f"Unsupported type: {f.type}")
                setattr(cfg, f.name, value)

    if not cfg.host:
        cfg.host = g.args.host

    if not cfg.port:
        cfg.port = g.args.port

    if not all([cfg.username, cfg.password]):
        cfg.require_auth = False

    if not all([cfg.private_key, cfg.certificate]):
        cfg.use_ssl = False

    return cfg


def to_styled_html(df: pd.DataFrame, padding: str) -> str:
    """データフレームをHTML表に変換

    Args:
        df (pd.DataFrame): 変換元データ
        padding (str): パディング

    Returns:
        str: HTML表
    """

    styled = (
        df.style
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
                "ポイント合計": "{:.1f} pt",
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
                "経過日数": "{:.0f} 日",
                "プレイ回数": "{:.0f} ゲーム"
            },
            na_rep="-----",
        )
        .set_table_styles([
            {"selector": "th", "props": [("color", "#ffffff"), ("background-color", "#000000"), ("text-align", "center"), ("padding", padding)]},
            {"selector": "td", "props": [("text-align", "center"), ("padding", padding)]},
            {"selector": "tr:nth-child(odd)", "props": [("background-color", "#f0f0f0f0")]},
            {"selector": "tr:nth-child(even)", "props": [("background-color", "#dfdfdfdf")]},
        ])
    )

    ret = styled.to_html()
    ret = re.sub(r" >-(\d+)</td>", r" >▲\1</td>", ret)  # 素点
    ret = re.sub(r" >-(\d+\.\d)</td>", r" >▲\1</td>", ret)  # 素点(小数点付き)
    ret = re.sub(r" >-(\d+\.\d) pt</td>", r" >▲\1 pt</td>", ret)  # ポイント

    return ret


def set_cookie(html: str, req: Request, data: dict) -> Response:
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


def get_cookie(req: Request) -> dict:
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

    if req.method == "POST":
        cookie_data = req.form.to_dict()
        if req.form.get("action") == "reset":
            cookie_data = initial_value
        else:
            cookie_data.pop("action")
    else:
        cookie_data = initial_value
        cookie_data.update(req.cookies)

    return cookie_data
