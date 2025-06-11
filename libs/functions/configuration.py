"""
libs/functions/configuration.py
"""

import argparse
import logging
import os
import shutil
import sys
from functools import partial

import libs.global_value as g
from cls.config import Config
from cls.parser import MessageParser
from libs.utils import dbutil


def set_loglevel():
    """ログレベル追加"""

    # DEBUG : 10
    # INFO : 20
    # WARNING : 30
    # ERROR : 40
    # CRITICAL : 50

    # TRACE
    logging.TRACE = 19  # type: ignore
    logging.trace = partial(logging.log, logging.TRACE)  # type: ignore
    logging.addLevelName(logging.TRACE, "TRACE")  # type: ignore

    # NOTICE
    logging.NOTICE = 25  # type: ignore
    logging.notice = partial(logging.log, logging.NOTICE)  # type: ignore
    logging.addLevelName(logging.NOTICE, "NOTICE")  # type: ignore


def arg_parser():
    """コマンドライン解析

    Returns:
        argparse.ArgumentParser: オブジェクト
    """

    p = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=True,
    )

    p.add_argument(
        "--debug",
        action="store_true",
        help="デバッグ情報表示",
    )

    p.add_argument(
        "--verbose",
        action="store_true",
        help="詳細デバッグ情報表示",
    )

    p.add_argument(
        "--moderate",
        action="store_true",
        help="ログレベルがエラー以下のもを非表示",
    )

    p.add_argument(
        "--notime",
        action="store_true",
        help="ログフォーマットから日時を削除",
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

    match os.path.basename(sys.argv[0]):
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
                nargs="?",
                const=1,
                default=None,
                metavar="count",
                help="テスト用サンプルデータ生成(count=生成回数, default: %(const)s)",
            )

        case "test.py":  # 動作テスト用オプション
            p.add_argument(
                "-t", "--testcase",
            )

    return p.parse_args()


def setup() -> None:
    """設定ファイル読み込み"""
    set_loglevel()

    g.args = arg_parser()
    if not hasattr(g.args, "testcase"):
        g.args.testcase = False

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

    g.cfg = Config(g.args.config)
    g.msg = MessageParser()

    logging.notice("database: %s", g.cfg.db.database_file)  # type: ignore
    logging.notice("font: %s", g.cfg.setting.font_file)  # type: ignore
    logging.notice(  # type: ignore
        "rule_version: %s, origin_point: %s, return_point: %s, time_adjust: %sh",
        g.cfg.mahjong.rule_version, g.cfg.mahjong.origin_point, g.cfg.mahjong.return_point, g.cfg.setting.time_adjust
    )

    # 作業用ディレクトリ作成
    try:
        if os.path.isdir(g.cfg.setting.work_dir):
            shutil.rmtree(g.cfg.setting.work_dir)
        os.mkdir(g.cfg.setting.work_dir)
    except Exception as e:
        raise RuntimeError(e) from e


def read_memberslist(log=True):
    """メンバー/チームリスト読み込み

    Args:
        log (bool, optional): 読み込み時に内容をログに出力する. Defaults to True.
    """

    resultdb = dbutil.get_connection()
    rows = resultdb.execute("select name from member where id=0")
    g.cfg.member.guest_name = rows.fetchone()[0]

    rows = resultdb.execute("select name, member from alias")
    g.member_list = dict(rows.fetchall())

    rows = resultdb.execute(
        """
            select
                team.id as id,
                team.name as team,
                group_concat(member.name) as member
            from
                team
            left join member on
                team.id == member.team_id
            group by
                team.id
        """)

    g.team_list = []
    for row in rows.fetchall():
        g.team_list.append(
            dict(zip(["id", "team", "member"], row))
        )

    resultdb.close()

    if log:
        logging.notice(f"guest_name: {g.cfg.member.guest_name}")  # type: ignore
        logging.notice(f"member_list: {set(g.member_list.values())}")  # type: ignore
        logging.notice(f"team_list: {[x['team'] for x in g.team_list]}")  # type: ignore


def graph_setup(plt, fm) -> None:
    """グラフ設定

    Args:
        plt (matplotlib.font_manager): matplotlibオブジェクト
        fm (matplotlib.pyplot): matplotlibオブジェクト
    """

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
