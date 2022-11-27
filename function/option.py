import argparse

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
        "-m", "--member",
        required = True,
        metavar = "member.ini",
        help = "メンバー情報ファイル",
    )
    return(p.parse_args())