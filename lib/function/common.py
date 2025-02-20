import os
import unicodedata

import lib.global_value as g


def len_count(text):
    """文字数をカウント(全角文字は2)

    Args:
        text (str): 判定文字列

    Returns:
        int: 文字数
    """

    count = 0
    for c in text:
        if unicodedata.east_asian_width(c) in "FWA":
            count += 2
        else:
            count += 1

    return (count)


def han_to_zen(text):
    """半角文字を全角文字に変換(数字のみ)

    Args:
        text (str): 変換対象文字列

    Returns:
        str: 変換後の文字列
    """

    zen = "".join(chr(0xff10 + i) for i in range(10))
    han = "".join(chr(0x30 + i) for i in range(10))
    trans_table = str.maketrans(han, zen)
    return (text.translate(trans_table))


def zen_to_han(text):
    """全角文字を半角文字に変換(数字のみ)

    Args:
        text (str): 変換対象文字列

    Returns:
        str: 変換後の文字列
    """

    zen = "".join(chr(0xff10 + i) for i in range(10))
    han = "".join(chr(0x30 + i) for i in range(10))
    trans_table = str.maketrans(zen, han)
    return (text.translate(trans_table))


def hira_to_kana(text):
    """ひらがなをカタカナに変換

    Args:
        text (str): 変換対象文字列

    Returns:
        str: 変換後の文字列
    """

    hira = "".join(chr(0x3041 + i) for i in range(86))
    kana = "".join(chr(0x30a1 + i) for i in range(86))
    trans_table = str.maketrans(hira, kana)
    return (text.translate(trans_table))


def kata_to_hira(text):
    """カタカナをひらがなに変換

    Args:
        text (str): 変換対象文字列

    Returns:
        str: 変換後の文字列
    """

    hira = "".join(chr(0x3041 + i) for i in range(86))
    kana = "".join(chr(0x30a1 + i) for i in range(86))
    trans_table = str.maketrans(kana, hira)
    return (text.translate(trans_table))


def badge_degree(game_count=0):
    """プレイしたゲーム数に対して表示される称号を返す

    Args:
        game_count (int, optional): ゲーム数. Defaults to 0.

    Returns:
        str: 表示する称号
    """

    badge_degree = ""

    if "degree" in g.cfg.config.sections():
        if g.cfg.config["degree"].getboolean("display", False):
            degree_badge = g.cfg.config.get("degree", "badge").split(",")
            degree_counter = [
                x for x in map(int, g.cfg.config.get("degree", "counter").split(","))
            ]
            for i in range(len(degree_counter)):
                if game_count >= degree_counter[i]:
                    badge_degree = degree_badge[i]

    return (badge_degree)


def badge_status(game_count=0, win=0):
    """勝率に対して付く調子バッジを返す

    Args:
        game_count (int, optional): ゲーム数. Defaults to 0.
        win (int, optional): 勝ち数. Defaults to 0.

    Returns:
        str: 表示する称号
    """

    badge_status = ""

    if "status" in g.cfg.config.sections():
        if g.cfg.config["status"].getboolean("display", False):
            status_badge = g.cfg.config.get("status", "badge").split(",")
            status_step = g.cfg.config.getfloat("status", "step")
            if game_count == 0:
                index = 0
            else:
                winper = win / game_count * 100
                index = 3
                for i in (1, 2, 3):
                    if winper <= 50 - status_step * i:
                        index = 4 - i
                    if winper >= 50 + status_step * i:
                        index = 2 + i
            badge_status = status_badge[index]

    return (badge_status)


def floatfmt_adjust(df):
    """カラム名に応じたfloatfmtのリストを返す

    Args:
        df (pd.DataFrame): チェックするデータ

    Returns:
        list: floatfmtに指定するリスト
    """

    fmt = []
    for x in df.columns:
        match x:
            case "ゲーム数":
                fmt.append(".0f")
            case "通算" | "平均" | "区間ポイント" | "通算ポイント" | "区間平均":
                fmt.append("+.1f")
            case "1st" | "2nd" | "3rd" | "4th":
                fmt.append(".0f")
            case "1st(%)" | "2nd(%)" | "3rd(%)" | "4th(%)":
                fmt.append(".2f")
            case "平均順位" | "平順":
                fmt.append(".2f")
            case "レート":
                fmt.append(".1f")
            case "順位偏差" | "得点偏差":
                fmt.append(".0f")
            case _:
                fmt.append("")

    return (fmt)


def save_output(df, kind, filename, headline=None):
    """指定されたフォーマットでdfを保存する

    Args:
        df (pd.DataFrame): _description_
        kind (str): フォーマット
        filename (str): 保存ファイル名
        headline (str): 集計情報（ヘッダコメント）. Defaults to None.

    Returns:
        Union[str, None]
            - str: 保存したファイルパス
            - None: 指定したフォーマットで保存できなかった場合
    """

    match kind.lower():
        case "csv":
            data = df.to_csv(index=False)
        case "text" | "txt":
            data = df.to_markdown(index=False, tablefmt="outline", floatfmt=floatfmt_adjust(df))
        case _:
            return (None)

    # 保存
    save_file = os.path.join(g.cfg.setting.work_dir, filename)
    with open(save_file, "w") as writefile:
        if not headline:  # ヘッダ書き込み
            for line in headline.splitlines():
                writefile.writelines(f"# {line}\n")
            writefile.writelines("\n")

        writefile.writelines(data)

    return (save_file)


def graph_setup(plt, fm):
    """グラフ設定

    Args:
        plt (matplotlib.font_manager): matplotlibオブジェクト
        fm (matplotlib.pyplot): matplotlibオブジェクト
    """

    # スタイルの適応
    style = g.cfg.config["setting"].get("graph_style", "ggplot")

    if style not in plt.style.available:
        style = "ggplot"

    plt.style.use(style)

    # フォント再設定
    for x in ("family", "serif", "sans-serif", "cursive", "fantasy", "monospace"):
        if f"font.{x}" in plt.rcParams:
            plt.rcParams[f"font.{x}"] = ""

    font_path = os.path.join(os.path.realpath(os.path.curdir), g.cfg.setting.font_file)
    fm.fontManager.addfont(font_path)
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams["font.family"] = font_prop.get_name()

    # グリッド線
    if not plt.rcParams["axes.grid"]:
        plt.rcParams["axes.grid"] = True
        plt.rcParams["grid.alpha"] = 0.3
        plt.rcParams["grid.linestyle"] = "--"
    plt.rcParams["axes.axisbelow"] = True


def scope_coverage(argument: list):
    """キーワードから有効な日付を取得する

    Args:
        argument (list): 引数リスト

    Returns:
        Tuple[list, list]:
            - list: 得られた日付のリスト
            - list: 日付を取り除いた引数リスト
    """

    new_argument = argument.copy()
    target_days = []

    for x in argument:
        if g.search_word.find(x):
            target_days += g.search_word.range(x)
            new_argument.remove(x)

    return (target_days, new_argument)


def debug_out(msg1, msg2=None):
    """メッセージ標準出力(テスト用)

    Args:
        msg1 (str): _description_
        msg2 (str, optional): _description_. Defaults to None.
    """

    print(msg1)
    if type(msg2) is dict:
        [print(msg2[x]) for x in msg2]
    elif msg2:
        print(msg2)
