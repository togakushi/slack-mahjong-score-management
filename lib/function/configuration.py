import argparse
import logging
import os
import shutil
import sys
from datetime import datetime
from functools import partial

from dateutil.relativedelta import relativedelta

import global_value as g
from cls.config import Config
from cls.parameter import command_option, parameters
from cls.parser import Message_Parser
from cls.search import SearchRange


def parser():
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
        metavar="config.ini",
        help="設定ファイル",
    )

    # 動作テスト用オプション(非表示)
    p.add_argument(
        "-t", "--testcase",
        help=argparse.SUPPRESS,
    )

    p.add_argument(
        "--classic",
        action="store_true",
        help=argparse.SUPPRESS,
    )

    p.add_argument(
        "--profile",
        help=argparse.SUPPRESS,
    )

    return (p.parse_args())


def setup():
    # 設定ファイル読み込み
    g.args = parser()

    # --- ログレベル追加
    # TRACE
    logging.TRACE = 19  # type: ignore
    logging.trace = partial(logging.log, logging.TRACE)  # type: ignore
    logging.addLevelName(logging.TRACE, "TRACE")  # type: ignore

    # NOTICE
    logging.NOTICE = 25  # type: ignore
    logging.notice = partial(logging.log, logging.NOTICE)  # type: ignore
    logging.addLevelName(logging.NOTICE, "NOTICE")  # type: ignore

    if g.args.notime:
        fmt = "[%(levelname)s][%(name)s:%(module)s:%(funcName)s] %(message)s"
    else:
        fmt = "[%(asctime)s][%(levelname)s][%(name)s:%(module)s:%(funcName)s] %(message)s"

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
    g.search_word = SearchRange()
    g.opt = command_option()
    g.prm = parameters()
    g.msg = Message_Parser()

    # 固定値
    g.wind = ("東家", "南家", "西家", "北家")
    g.member_list = {}
    g.team_list = {}

    g.app_var = {  # ホームタブ用
        "user_id": None,
        "view_id": None,
        "screen": None,
        "sday": (datetime.now() + relativedelta(hours=-12)).strftime("%Y-%m-%d"),
        "eday": (datetime.now() + relativedelta(hours=-12)).strftime("%Y-%m-%d"),
    }

    logging.trace(f"{g.cfg.cw=}")  # type: ignore
    logging.info(f"{g.cfg.setting.slash_command=}")
    logging.info(f"{g.cfg.setting.ignore_userid=}")
    logging.info(f"{g.cfg.db.channel_limitations=}")

    # 作業用ディレクトリ作成
    try:
        if os.path.isdir(g.cfg.setting.work_dir):
            shutil.rmtree(g.cfg.setting.work_dir)
        os.mkdir(g.cfg.setting.work_dir)
    except Exception:
        logging.error("Working directory creation failed !!!")
        sys.exit()
