"""
libs/utils/textutil.py
"""

import os
from math import ceil, floor
from typing import TYPE_CHECKING, Literal

import libs.global_value as g

if TYPE_CHECKING:
    from pathlib import Path


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

    zen = "".join(chr(0xFF10 + i) for i in range(10))
    han = "".join(chr(0x30 + i) for i in range(10))
    hira = "".join(chr(0x3041 + i) for i in range(86))
    kana = "".join(chr(0x30A1 + i) for i in range(86))

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


def save_file_path(filename: str, delete: bool = False) -> "Path":
    """保存ファイルのフルパスを取得

    Args:
        filename (str): デフォルトファイル名
        delete (bool, optional): 生成済みファイルを削除. Defaults to False.

    Returns:
        Path: 保存ファイルパス
    """

    _, file_ext = os.path.splitext(filename)
    file_name = f"{g.params['filename']}{file_ext}" if g.params.get("filename") else f"{filename}"
    file_path = g.cfg.setting.work_dir / file_name

    if file_path.exists() and delete:
        os.remove(file_path)

    return file_path


def split_balanced(data: list, target_size: int, tolerance: float = 0.15) -> list:
    """リストデータを指定個数で分割

    Args:
        data (list): 対象データ
        target_size (int): 分割サイズ
        tolerance (float, optional): 個数誤差. Defaults to 0.15.

    Returns:
        list: 分割したリスト
    """

    # 分割サイズに0が指定されている場合は何もしない
    if not target_size:
        return data

    n = len(data)
    if n == 0:
        return []

    min_size = int(target_size * (1 - tolerance))
    max_size = int(target_size * (1 + tolerance))

    # 最小ブロック数の候補を計算
    min_blocks = ceil(n / max_size)
    max_blocks = floor(n / min_size)

    # 許容範囲内でブロック数を決める（なるべく少ない）
    for num_blocks in range(min_blocks, max_blocks + 1):
        size = n / num_blocks
        if min_size <= size <= max_size:
            break
    else:
        # 条件を満たすブロック数がない場合は単純均等割り
        num_blocks = ceil(n / target_size)

    # 実際の分割処理
    base_size = n // num_blocks
    remainder = n % num_blocks

    result: list = []
    start = 0
    for i in range(num_blocks):
        end = start + base_size + (1 if i < remainder else 0)
        result.append(data[start:end])
        start = end

    return result


def split_text_blocks(text: str, limit: int = 2000) -> list[str]:
    """指定文字数でテキストを行単位で分割してリストにする

    Args:
        text (str): 対象文字列
        limit (int, optional): 分割文字数. Defaults to 2000.

    Returns:
        list[str]: 分割リスト
    """

    blocks = []
    current_data = ""
    buffer_data = ""
    in_code = False
    min_gap_after_code_start = 10
    lines_count = 0

    for _, line in enumerate(text.splitlines(keepends=True)):
        stripped = line.strip()
        buffer_data += line

        # --- コードブロック開始／終了検出 ---
        if stripped.startswith("```"):
            in_code = not in_code
            if not in_code:
                current_data += buffer_data
                buffer_data = ""
            continue

        lines_count += 1 if in_code else 0

        # --- 文字数チェック ---
        if len(current_data + buffer_data) > limit:
            if lines_count > min_gap_after_code_start:
                if in_code:
                    blocks.append(current_data + buffer_data + "```\n")
                    buffer_data = "```\n"
                else:
                    blocks.append(current_data + buffer_data)
                    buffer_data = ""
            else:
                blocks.append(current_data)  # 先頭の改行は削除されてしまう
            current_data = ""

    return blocks
