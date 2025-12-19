"""
libs/configuration.py
"""

import argparse
import logging
import os
import sys
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, cast

import libs.commands.graph.entry
import libs.commands.ranking.entry
import libs.commands.report.entry
import libs.commands.results.entry
import libs.global_value as g
from cls.config import AppConfig
from integrations import factory
from libs.data import initialization, lookup
from libs.functions import compose
from libs.registry import member, team
from libs.types import Args, StyleOptions

if TYPE_CHECKING:
    from cls.config import SubCommand
    from integrations.protocols import MessageParserProtocol


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


def arg_parser() -> Args:
    """コマンドライン解析

    Returns:
        Args : ArgumentParserオブジェクト
    """

    p = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=True,
    )

    p.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("config.ini"),
        help="設定ファイル(default: %(default)s)",
    )
    p.add_argument(
        "--profile",
        help=argparse.SUPPRESS,
    )
    p.add_argument(
        "-s",
        "--service",
        choices=[
            "slack",
            "discord",
            "standard_io",
            "std",
            "web",
            "flask",
        ],
        type=str,
        default="slack",
        help="連携先サービス",
    )

    logging_group = p.add_argument_group("logging options")
    logging_group.add_argument(
        "-d",
        "--debug",
        action="count",
        default=0,
        help="デバッグレベル(-d, -dd)",
    )
    logging_group.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="動作ログ出力レベル(-v, -vv)",
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
            required = p.add_argument_group("Required options(amutually exclusive)")
            exclusive = required.add_mutually_exclusive_group()
            exclusive.add_argument(
                "--compar",
                action="store_true",
                help="データ突合",
            )
            exclusive.add_argument(
                "--unification",
                type=Path,
                nargs="?",
                const="rename.ini",
                help="ファイルの内容に従って記録済みのメンバー名を修正する(default: %(const)s)",
            )
            exclusive.add_argument(
                "--recalculation",
                action="store_true",
                help="ポイント再計算",
            )
            exclusive.add_argument(
                "--export",
                dest="export_data",
                type=str,
                nargs="?",
                const="export",
                metavar="PREFIX",
                help="メンバー設定情報をエクスポート(default prefix: %(const)s)",
            )
            exclusive.add_argument(
                "--import",
                dest="import_data",
                type=str,
                nargs="?",
                const="export",
                metavar="PREFIX",
                help="メンバー設定情報をインポート(default prefix: %(const)s)",
            )
            exclusive.add_argument(
                "--vacuum",
                action="store_true",
                help="database vacuum",
            )
            exclusive.add_argument(
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
                "-t",
                "--testcase",
                dest="testcase",
                type=bool,
            )

    return cast(Args, p.parse_args(namespace=Args))


def setup():
    """設定ファイル読み込み"""

    set_loglevel()

    g.args = arg_parser()

    # 連携サービス
    match g.args.service:
        case "slack":
            g.selected_service = "slack"
        case "discord":
            g.selected_service = "discord"
        case "standard_io" | "std":
            g.selected_service = "standard_io"
        case "web" | "flask":
            g.selected_service = "web"
        case _:
            sys.exit()

    if not hasattr(g.args, "testcase"):
        g.args.testcase = None
    else:
        g.selected_service = "standard_io"

    # ログフォーマット
    if g.args.notime:
        fmt = ""
    else:
        fmt = "[%(asctime)s]"

    # デバッグレベル
    match g.args.debug:
        case 1:
            fmt += "[%(levelname)s][%(module)s:%(funcName)s] %(message)s"
            logging.basicConfig(level=logging.DEBUG, format=fmt)
            logging.info("DEBUG MODE")
        case 2:
            fmt += "[%(levelname)s][%(module)s:%(funcName)s] %(message)s"
            logging.basicConfig(level=logging.TRACE, format=fmt)  # type: ignore
            logging.info("DEBUG MODE(verbose)")
        case _:
            fmt += "[%(levelname)s][%(module)s:%(funcName)s] %(message)s"
            if g.args.moderate:
                logging.basicConfig(level=logging.WARNING, format=fmt)
            else:
                logging.basicConfig(level=logging.INFO, format=fmt)

    g.cfg = AppConfig(g.args.config)
    g.adapter = factory.select_adapter(g.selected_service, g.cfg)
    register()

    # DB初期化
    initialization.initialization_resultdb(g.cfg.setting.database_file)
    for section in g.cfg.main_parser.sections():
        if str(section).startswith(f"{g.adapter.interface_type}_"):
            if channel_config := g.cfg.main_parser[section].get("channel_config"):
                others_db = lookup.internal.get_config_value(
                    config_file=Path(channel_config),
                    section="setting",
                    name="database_file",
                    val_type=str,
                    fallback="",
                )

                if others_db:
                    initialization.initialization_resultdb(Path(others_db).absolute())

    # 設定内容のロギング
    logging.info("config: %s", g.cfg.config_file.absolute())
    logging.info(
        "service: %s, graph_library: %s, time_adjust: %sh",
        g.selected_service,
        g.adapter.conf.plotting_backend,
        g.cfg.setting.time_adjust,
    )
    for keyword, config in g.cfg.keyword.rule.items():
        g.cfg.overwrite(config, "mahjong")
        logging.info(
            "keyword: %s, origin_point: %s, return_point: %s, rank_point: %s, draw_split: %s, rule_version: %s",
            keyword,
            g.cfg.mahjong.origin_point,
            g.cfg.mahjong.return_point,
            g.cfg.mahjong.rank_point,
            g.cfg.mahjong.draw_split,
            g.cfg.mahjong.rule_version,
        )


def read_memberslist(log=True):
    """メンバー/チームリスト読み込み

    Args:
        log (bool, optional): 読み込み時に内容をログに出力する. Defaults to True.
    """

    g.cfg.member.guest_name = lookup.db.get_guest()
    g.cfg.member.list = lookup.db.get_member_list()
    g.cfg.team.list = lookup.db.get_team_list()

    if log:
        logging.info("guest_name: %s", g.cfg.member.guest_name)
        logging.info("member_list: %s", sorted(set(g.cfg.member.list.values())))
        logging.info("team_list: %s", [x["team"] for x in g.cfg.team.list])


def register():
    """ディスパッチテーブル登録"""

    def _switching(m: "MessageParserProtocol"):
        g.cfg.initialization()
        if g.cfg.main_parser.has_section(m.status.source):
            if channel_config := g.cfg.main_parser[m.status.source].get("channel_config"):
                logging.debug("Channel override settings: %s", Path(channel_config).absolute())
                g.cfg.overwrite(Path(channel_config), "setting")
        read_memberslist(log=False)

    def dispatch_help(m: "MessageParserProtocol"):
        _switching(m)
        m.set_data("ヘルプ", compose.msg_help.event_message(), StyleOptions())
        m.post.ts = m.data.event_ts

    def dispatch_download(m: "MessageParserProtocol"):
        _switching(m)
        m.set_data("成績記録DB", g.cfg.setting.database_file, StyleOptions())

    def dispatch_members_list(m: "MessageParserProtocol"):
        _switching(m)
        m.set_data("登録済みメンバー", lookup.textdata.get_members_list(), StyleOptions(codeblock=True))
        m.post.ts = m.data.event_ts

    def dispatch_team_list(m: "MessageParserProtocol"):
        _switching(m)
        m.set_data("登録済みチーム", lookup.textdata.get_team_list(), StyleOptions(codeblock=True))
        m.post.ts = m.data.event_ts

    def dispatch_member_append(m: "MessageParserProtocol"):
        _switching(m)
        m.set_data("メンバー追加", member.append(m.argument), StyleOptions(key_title=False))

    def dispatch_member_remove(m: "MessageParserProtocol"):
        _switching(m)
        m.set_data("メンバー削除", member.remove(m.argument), StyleOptions(key_title=False))

    def dispatch_team_create(m: "MessageParserProtocol"):
        _switching(m)
        m.set_data("チーム作成", team.create(m.argument), StyleOptions(key_title=False))

    def dispatch_team_delete(m: "MessageParserProtocol"):
        _switching(m)
        m.set_data("チーム削除", team.delete(m.argument), StyleOptions(key_title=False))

    def dispatch_team_append(m: "MessageParserProtocol"):
        _switching(m)
        m.set_data("チーム所属", team.append(m.argument), StyleOptions(key_title=False))

    def dispatch_team_remove(m: "MessageParserProtocol"):
        _switching(m)
        m.set_data("チーム脱退", team.remove(m.argument), StyleOptions(key_title=False))

    def dispatch_team_clear(m: "MessageParserProtocol"):
        _switching(m)
        m.set_data("全チーム削除", team.clear(), StyleOptions(key_title=False))

    dispatch_table: dict = {
        "results": libs.commands.results.entry.main,
        "graph": libs.commands.graph.entry.main,
        "ranking": libs.commands.ranking.entry.main,
        "report": libs.commands.report.entry.main,
        "member": dispatch_members_list,
        "team": dispatch_team_list,
        "team_list": dispatch_team_list,
        "download": dispatch_download,
        "add": dispatch_member_append,
        "delete": dispatch_member_remove,
        "team_create": dispatch_team_create,
        "team_del": dispatch_team_delete,
        "team_add": dispatch_team_append,
        "team_remove": dispatch_team_remove,
        "team_clear": dispatch_team_clear,
    }

    # ヘルプ
    g.keyword_dispatcher.update({g.cfg.setting.help: dispatch_help})

    for command, ep in dispatch_table.items():
        # 呼び出しキーワード登録
        if hasattr(g.cfg, command):
            sub_command = cast("SubCommand", getattr(g.cfg, command))
            for alias in sub_command.commandword:
                g.keyword_dispatcher.update({alias: ep})
        # スラッシュコマンド登録
        if hasattr(g.cfg.alias, command):
            for alias in cast(list, getattr(g.cfg.alias, command)):
                g.command_dispatcher.update({alias: ep})

    # サービス別コマンド登録
    g.command_dispatcher.update(g.adapter.conf.command_dispatcher)
    g.keyword_dispatcher.update(g.adapter.conf.keyword_dispatcher)

    logging.debug("keyword_dispatcher:\n%s", "\n".join([f"\t{k}: {v}" for k, v in g.keyword_dispatcher.items()]))
    logging.debug("command_dispatcher:\n%s", "\n".join([f"\t{k}: {v}" for k, v in g.command_dispatcher.items()]))
