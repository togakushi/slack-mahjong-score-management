import argparse
import configparser

from function import global_value as g

def parser():
    p = argparse.ArgumentParser(
        formatter_class = argparse.RawTextHelpFormatter,
        add_help = True,
    )

    p.add_argument(
        "--debug",
        action = "store_true",
        help = "デバッグ情報表示",
    )

    p.add_argument(
        "-c", "--config",
        required = True,
        metavar = "config.ini",
        help = "設定ファイル",
    )

    p.add_argument(
        "-m", "--member",
        required = True,
        metavar = "member.ini",
        help = "メンバー情報ファイル",
    )

    return(p.parse_args())


def configload(configfile):
    config = configparser.ConfigParser()

    try:
        config.read(configfile, encoding="utf-8")
    except:
        sys.exit()

    g.logging.info(f"configload: {configfile} -> {config.sections()}")
    return(config)


def configsave(config, configfile):
    with open(configfile, "w") as f:
        config.write(f)
