"""
libs/functions/configuration.py
"""

import argparse
import logging
import os
import shutil
import sys
from configparser import ConfigParser
from functools import partial
from typing import cast

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import use

import libs.global_value as g
from cls.config import AppConfig
from integrations import factory
from libs.data import lookup


def set_loglevel():
    """ログレベル追加"""

    # DEBUG : 10
    # INFO : 20
    # WARNING : 30
    # ERROR : 40
    # CRITICAL : 50

    # TRACE
    logging.TRACE = 5  # type: ignore
    logging.trace = partial(logging.log, logging.TRACE)  # type: ignore
    logging.addLevelName(logging.TRACE, "TRACE")  # type: ignore

    # NOTICE
    logging.NOTICE = 25  # type: ignore
    logging.notice = partial(logging.log, logging.NOTICE)  # type: ignore
    logging.addLevelName(logging.NOTICE, "NOTICE")  # type: ignore


def arg_parser() -> argparse.Namespace:
    """コマンドライン解析

    Returns:
        argparse.ArgumentParser: オブジェクト
    """

    p = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=True,
    )

    p.add_argument(
        "-c", "--config",
        default="config.ini",
        help="設定ファイル(default: %(default)s)",
    )
    p.add_argument(
        "--profile",
        help=argparse.SUPPRESS,
    )
    p.add_argument(
        "--service",
        choices=[
            "slack",
            "standard_io", "std",
            "web", "flask",
        ],
        default="slack",
        help="連携先サービス",
    )

    logging_group = p.add_argument_group("logging options")
    logging_group.add_argument(
        "--debug",
        action="store_true",
        help="デバッグ情報表示",
    )
    logging_group.add_argument(
        "--verbose", "--trace",
        dest="verbose",
        action="store_true",
        help="詳細デバッグ情報表示",
    )
    logging_group.add_argument(
        "--moderate",
        action="store_true",
        help="ログレベルがエラー以下のもを非表示",
    )
    logging_group.add_argument(
        "--notime",
        action="store_true",
        help="ログフォーマットから日時を削除",
    )

    match os.path.basename(sys.argv[0]):
        case "app.py":
            service_stdio = p.add_argument_group("Only allowed when --service=standard_io")
            service_stdio.add_argument(
                "--text",
                type=str,
                help="input text strings",
            )
            service_web = p.add_argument_group("Only allowed when --service=web")
            service_web.add_argument(
                "--host",
                type=str,
                default="127.0.0.1",
                help="listen  address(default: %(default)s)",
            )
            service_web.add_argument(
                "--port",
                type=int,
                default=8000,
                help="bind port(default: %(default)s)",
            )
        case "dbtools.py":  # dbtools専用オプション
            group = p.add_mutually_exclusive_group()
            group.add_argument(
                "--compar",
                action="store_true",
                help="データ突合",
            )
            group.add_argument(
                "--unification",
                nargs="?",
                const="rename.ini",
                help="ファイルの内容に従って記録済みのメンバー名を修正する(default: %(const)s)",
            )
            group.add_argument(
                "--recalculation",
                action="store_true",
                help="ポイント再計算",
            )
            group.add_argument(
                "--export",
                dest="export_data",
                nargs="?",
                const="export",
                metavar="PREFIX",
                help="メンバー設定情報をエクスポート(default prefix: %(const)s)",
            )
            group.add_argument(
                "--import",
                nargs="?",
                dest="import_data",
                const="export",
                metavar="PREFIX",
                help="メンバー設定情報をインポート(default prefix: %(const)s)",
            )
            group.add_argument(
                "--vacuum",
                action="store_true",
                help="database vacuum",
            )
            group.add_argument(
                "--gen-test-data",
                type=int,
                dest="gen_test_data",
                nargs="?",
                const=1,
                default=None,
                metavar="count",
                help="テスト用サンプルデータ生成(count=生成回数, default: %(const)s)",
            )
        case "test.py":  # 動作テスト用オプション
            p.add_argument(
                "-t", "--testcase",
                dest="testcase",
            )

    return p.parse_args()


def setup() -> None:
    """設定ファイル読み込み"""
    set_loglevel()

    g.args = arg_parser()

    # 連携サービス
    match g.args.service:
        case "slack":
            g.selected_service = "slack"
        case "standard_io" | "std":
            g.selected_service = "standard_io"
        case "web" | "flask":
            g.selected_service = "web"
        case _:
            sys.exit()

    if not hasattr(g.args, "testcase"):
        g.args.testcase = False
    else:
        g.selected_service = "standard_io"

    if g.args.notime:
        fmt = "[%(levelname)s][%(module)s:%(funcName)s] %(message)s"
    else:
        fmt = "[%(asctime)s][%(levelname)s][%(module)s:%(funcName)s] %(message)s"

    if g.args.debug:
        if g.args.verbose:
            print("DEBUG MODE(verbose)")
            logging.basicConfig(level=logging.TRACE, format=fmt)  # type: ignore
        else:
            print("DEBUG MODE")
            logging.basicConfig(level=logging.INFO, format=fmt)
    else:
        if g.args.moderate:
            logging.basicConfig(level=logging.WARNING, format=fmt)
        else:
            logging.basicConfig(level=logging.NOTICE, format=fmt)  # type: ignore

    g.cfg = AppConfig(g.args.config)
    g.app_config = factory.load_config(str(g.selected_service), cast(ConfigParser, getattr(g.cfg, "_parser")))
    os.path.realpath

    # 作業用ディレクトリ作成
    try:
        if os.path.isdir(g.cfg.setting.work_dir):
            shutil.rmtree(g.cfg.setting.work_dir)
        os.mkdir(g.cfg.setting.work_dir)
    except Exception as err:
        raise RuntimeError(err) from err

    # 設定内容のロギング
    logging.notice("conf: %s", os.path.join(g.cfg.config_dir, g.args.config))  # type: ignore
    logging.notice("font: %s", g.cfg.setting.font_file)  # type: ignore
    logging.notice("database: %s", g.cfg.setting.database_file)  # type: ignore
    logging.notice("graph_library: %s", g.app_config.plotting_backend)  # type: ignore
    logging.notice(  # type: ignore
        "rule_version: %s, origin_point: %s, return_point: %s, time_adjust: %sh",
        g.cfg.mahjong.rule_version, g.cfg.mahjong.origin_point, g.cfg.mahjong.return_point, g.cfg.setting.time_adjust
    )


def read_memberslist(log=True):
    """メンバー/チームリスト読み込み

    Args:
        log (bool, optional): 読み込み時に内容をログに出力する. Defaults to True.
    """

    g.cfg.member.guest_name = lookup.db.get_guest()
    g.member_list = lookup.db.get_member_list()
    g.team_list = lookup.db.get_team_list()

    if log:
        logging.notice(f"guest_name: {g.cfg.member.guest_name}")  # type: ignore
        logging.notice(f"member_list: {sorted(set(g.member_list.values()))}")  # type: ignore
        logging.notice(f"team_list: {[x["team"] for x in g.team_list]}")  # type: ignore


def graph_setup() -> None:
    """グラフ設定初期化"""

    pd.options.plotting.backend = g.app_config.plotting_backend
    match g.app_config.plotting_backend:
        case "plotly":
            return

    plt.close()
    use(backend="agg")
    mlogger = logging.getLogger("matplotlib")
    mlogger.setLevel(logging.WARNING)

    # スタイルの適応
    if (style := g.cfg.setting.graph_style) not in plt.style.available:
        style = "ggplot"
    plt.style.use(style)

    # フォント再設定
    for x in ("family", "serif", "sans-serif", "cursive", "fantasy", "monospace"):
        if f"font.{x}" in plt.rcParams:
            plt.rcParams[f"font.{x}"] = ""

    fm.fontManager.addfont(g.cfg.setting.font_file)
    font_prop = fm.FontProperties(fname=g.cfg.setting.font_file)
    plt.rcParams["font.family"] = font_prop.get_name()

    # グリッド線
    if not plt.rcParams["axes.grid"]:
        plt.rcParams["axes.grid"] = True
        plt.rcParams["grid.alpha"] = 0.3
        plt.rcParams["grid.linestyle"] = "--"
    plt.rcParams["axes.axisbelow"] = True
