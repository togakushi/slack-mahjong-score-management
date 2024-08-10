import os
import unicodedata

from lib.function import global_value as g


def len_count(text):
    """
    文字数をカウント(全角文字は2)

    Parameters
    ----------
    text : text
        判定文字列

    Returns
    -------
    count : int
        文字数
    """

    count = 0
    for c in text:
        if unicodedata.east_asian_width(c) in "FWA":
            count += 2
        else:
            count += 1

    return (count)


def HAN2ZEN(text):
    """
    半角文字を全角文字に変換(数字のみ)

    Parameters
    ----------
    text : text
        変換対象文字列

    Returns
    -------
    text : text
        変換後の文字列
    """

    ZEN = "".join(chr(0xff10 + i) for i in range(10))
    HAN = "".join(chr(0x30 + i) for i in range(10))
    trans_table = str.maketrans(HAN, ZEN)
    return (text.translate(trans_table))


def ZEN2HAN(text):
    """
    全角文字を半角文字に変換(数字のみ)

    Parameters
    ----------
    text : text
        変換対象文字列

    Returns
    -------
    text : text
        変換後の文字列
    """

    ZEN = "".join(chr(0xff10 + i) for i in range(10))
    HAN = "".join(chr(0x30 + i) for i in range(10))
    trans_table = str.maketrans(ZEN, HAN)
    return (text.translate(trans_table))


def HIRA2KANA(text):
    """
    ひらがなをカタカナに変換

    Parameters
    ----------
    text : text
        変換対象文字列

    Returns
    -------
    text : text
        変換後の文字列
    """

    HIRA = "".join(chr(0x3041 + i) for i in range(86))
    KANA = "".join(chr(0x30a1 + i) for i in range(86))
    trans_table = str.maketrans(HIRA, KANA)
    return (text.translate(trans_table))


def KANA2HIRA(text):
    """
    カタカナをひらがなに変換

    Parameters
    ----------
    text : text
        変換対象文字列

    Returns
    -------
    text : text
        変換後の文字列
    """

    HIRA = "".join(chr(0x3041 + i) for i in range(86))
    KANA = "".join(chr(0x30a1 + i) for i in range(86))
    trans_table = str.maketrans(KANA, HIRA)
    return (text.translate(trans_table))


def badge_degree(game_count=0):
    """
    プレイしたゲーム数に対して表示される称号を返す

    Parameters
    ----------
    game_count : int
        ゲーム数

    Returns
    -------
    badge_degree : text
        表示する称号
    """

    badge_degree = ""

    if "degree" in g.config.sections():
        if g.config["degree"].getboolean("display", False):
            degree_badge = g.config.get("degree", "badge").split(",")
            degree_counter = [
                x for x in map(int, g.config.get("degree", "counter").split(","))
            ]
            for i in range(len(degree_counter)):
                if game_count >= degree_counter[i]:
                    badge_degree = degree_badge[i]

    return (badge_degree)


def badge_status(game_count=0, win=0):
    """
    勝率に対して付く調子バッジを返す

    Parameters
    ----------
    game_count : int
        ゲーム数

    win : int
        勝ち数

    Returns
    -------
    badge_degree : text
        表示する称号
    """

    badge_status = ""

    if "status" in g.config.sections():
        if g.config["status"].getboolean("display", False):
            status_badge = g.config.get("status", "badge").split(",")
            status_step = g.config.getfloat("status", "step")
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


def save_output(df, format, filename):
    """
    指定されたフォーマットでdfを保存する

    Parameters
    ----------
    df : DataFrame
        保存するデータ

    format : str
        フォーマット

    filename : str
        保存ファイル名

    Returns
    -------
    save_file : file path / None
    """

    match format.lower():
        case "csv":
            data = df.to_csv(index=False)
        case "text" | "txt":
            data = df.to_markdown(index=False, tablefmt="outline")
        case _:
            return (None)

    # 保存
    save_file = os.path.join(g.work_dir, filename)
    with open(save_file, "w") as writefile:
        writefile.writelines(data)

    return (save_file)


def set_graph_font(plt, fm):
    """
    グラフフォント設定
    """

    font_path = os.path.join(os.path.realpath(os.path.curdir), g.font_file)
    fm.fontManager.addfont(font_path)
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams["font.family"] = font_prop.get_name()
