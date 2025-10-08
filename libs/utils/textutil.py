"""
libs/utils/textutil.py
"""

import os
import unicodedata
from typing import Literal

import libs.global_value as g


def len_count(text: str) -> int:
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

    return count


def str_conv(text: str, kind: Literal["h2z", "z2h", "h2k", "k2h"]) -> str:
    """文字列変換

    Args:
        text (str): 変換対象文字列
        kind (str): 変換種類
        - h2z: 半角文字を全角文字に変換(数字のみ)
        - z2h: 全角文字を半角文字に変換(数字のみ)
        - h2k: ひらがなをカタカナに変換
        - k2h: カタカナをひらがなに変換

    Returns:
        str: 変換後の文字列
    """

    zen = "".join(chr(0xff10 + i) for i in range(10))
    han = "".join(chr(0x30 + i) for i in range(10))
    hira = "".join(chr(0x3041 + i) for i in range(86))
    kana = "".join(chr(0x30a1 + i) for i in range(86))

    match kind:
        case "h2z":  # 半角文字を全角文字に変換(数字のみ)
            trans_table = str.maketrans(han, zen)
        case "z2h":  # 全角文字を半角文字に変換(数字のみ)
            trans_table = str.maketrans(zen, han)
        case "h2k":  # ひらがなをカタカナに変換
            trans_table = str.maketrans(hira, kana)
        case "k2h":  # カタカナをひらがなに変換
            trans_table = str.maketrans(kana, hira)
        case _:
            return text

    return text.translate(trans_table)


def count_padding(data):
    """プレイヤー名一覧の中の最も長い名前の文字数を返す

    Args:
        data (list, dict): 対象プレイヤー名の一覧

    Returns:
        int: 文字数
    """

    name_list = []

    if isinstance(data, list):
        name_list = data

    if isinstance(data, dict):
        for i in data.keys():
            for name in [data[i][x]["name"] for x in ("東家", "南家", "西家", "北家")]:
                if name not in name_list:
                    name_list.append(name)

    if name_list:
        return max(len_count(x) for x in name_list)
    return 0


def save_file_path(extension: str, delete: bool = False) -> str:
    """保存ファイルのフルパスを取得

    Args:
        extension (str): 拡張子(ドットを含める)
        delete (bool, optional): 生成済みファイルを削除. Defaults to False.

    Returns:
        str: 保存ファイルパス
    """

    file_path = os.path.join(
        g.cfg.setting.work_dir,
        f"{g.params["filename"]}{extension}" if g.params.get("filename") else f"graph{extension}",
    )

    if os.path.exists(file_path) and delete:
        os.remove(file_path)

    return file_path


def split_line(last_line: int, step: int) -> list[tuple[int, int]]:
    """step単位で分割する

    Args:
        last_line (int): 最終位置
        step (int): 分割単位

    Returns:
        list[tuple[int, int]]: 分割単位のペア
    """

    step_count: list = []

    for i in range(int(last_line / step + 1)):
        s_line = i * step
        e_line = (i + 1) * step

        if last_line - e_line < step / 2:  # 最終ブロックがstep/2で収まるならまとめる
            step_count.append((s_line, last_line))
            break
        step_count.append((s_line, e_line))

    return step_count
