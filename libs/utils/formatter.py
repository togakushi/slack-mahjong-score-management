"""
libs/utils/formatter.py
"""

import os
import random
import re

import pandas as pd
from tabulate import tabulate

import libs.global_value as g
from libs.data import lookup
from libs.utils import textutil


def floatfmt_adjust(df: pd.DataFrame, index: bool = False) -> list:
    """カラム名に応じたfloatfmtのリストを返す

    Args:
        df (pd.DataFrame): チェックするデータ
        index (bool, optional): リストにIndexを含める. Defaults to False.

    Returns:
        list: floatfmtに指定するリスト
    """

    fmt: list = []
    if df.empty:
        return fmt

    field: list = df.columns.tolist()
    if index:
        field.insert(0, df.index.name)

    for x in field:
        match x:
            case "ゲーム数" | "game_count":
                fmt.append(".0f")
            case "win" | "lose" | "draw" | "top2" | "top3" | "gs_count":
                fmt.append(".0f")
            case "通算" | "通算ポイント" | "point_sum":
                fmt.append("+.1f")
            case "平均" | "平均ポイント" | "point_avg" | "区間ポイント" | "区間平均":
                fmt.append("+.1f")
            case "1st" | "2nd" | "3rd" | "4th" | "1位" | "2位" | "3位" | "4位" | "rank1" | "rank2" | "rank3" | "rank4":
                fmt.append(".0f")
            case "1st(%)" | "2nd(%)" | "3rd(%)" | "4th(%)" | "1位率" | "2位率" | "3位率" | "4位率":
                fmt.append(".2%")
            case "top2_rate" | "連対率" | "top3_rate" | "ラス回避率":
                fmt.append(".2%")
            case"yakuman(%)" | "gs_rate" | "役満和了率":
                fmt.append(".2%")
            case "トビ" | "flying":
                fmt.append(".0f")
            case "トビ率" | "flying(%)" | "yakuman(%)":
                fmt.append(".2%")
            case "平均順位" | "平順" | "rank_avg":
                fmt.append(".2f")
            case "順位差" | "トップ差":
                fmt.append(".1f")
            case "平均素点" | "レート":
                fmt.append(".1f")
            case "順位偏差" | "得点偏差":
                fmt.append(".0f")
            case "rpoint_max" | "rpoint_min" | "rpoint_mean":
                fmt.append(".0f")
            case "participation_rate" | "ゲーム参加率":
                fmt.append(".2%")
            case _:
                fmt.append("")

    return fmt


def column_alignment(df: pd.DataFrame, header: bool = False, index: bool = False) -> list:
    """カラム位置

    Args:
        df (pd.DataFrame): チェックするデータ
        header (bool, optional): ヘッダを対象にする
        index (bool, optional): リストにIndexを含める. Defaults to False.

    Returns:
        list: colalignに指定するリスト
    """

    fmt: list = []  # global, right, center, left, decimal, None
    if df.empty:
        return fmt

    field: list = df.columns.tolist()
    if index:
        field.insert(0, df.index.name)

    if header:  # ヘッダ(すべて左寄せ)
        fmt = ["left"] * len(field)
    else:
        for x in field:
            match x:
                case "ゲーム数":
                    fmt.append("right")
                case "通算" | "平均" | "1位" | "2位" | "3位" | "4位" | " 平順" | "トビ":
                    fmt.append("right")
                case "通算" | "順位差" | "トップ差":
                    fmt.append("right")
                case "レート" | "平均順位" | "順位偏差" | "平均素点" | "得点偏差":
                    fmt.append("right")
                case _:
                    fmt.append("left")

    return fmt


def save_output(df: pd.DataFrame, kind: str, filename: str, headline: str | None = None) -> str:
    """指定されたフォーマットでdfを保存する

    Args:
        df (pd.DataFrame): 描写対象データ
        kind (str): フォーマット
        filename (str): 保存ファイル名
        headline (str | None, optional): 集計情報（ヘッダコメント）. Defaults to None.

    Returns:
        str: 保存したファイルパス
    """

    match kind.lower():
        case "csv":
            data = df.to_csv(index=False)
        case "text" | "txt":
            data = df.to_markdown(
                index=False,
                tablefmt="outline",
                floatfmt=floatfmt_adjust(df),
                colalign=column_alignment(df, False),
                # headersalign=column_alignment(df, True),  # ToDo: python-tabulate >= 0.10.0
            )
        case _:
            return ""

    # 保存
    save_file = os.path.join(g.cfg.setting.work_dir, filename)
    with open(save_file, "w", encoding="utf-8") as writefile:
        if headline is not None:  # ヘッダ書き込み
            for line in headline.splitlines():
                writefile.writelines(f"# {line}\n")
            writefile.writelines("\n")

        writefile.writelines(data)

    return save_file


def name_replace(pname: str, add_mark: bool = False) -> str:
    """表記ブレ修正(正規化)

    Args:
        pname (str): 対象プレイヤー名
        add_mark (bool, optional): ゲストマークを付与する. Defaults to False.

    Returns:
        str: 表記ブレ修正後のプレイヤー名
    """

    check_list = list(set(g.member_list.keys()))  # 別名を含むリスト
    check_team = lookup.internal.get_team()

    def _judge(check: str) -> str:
        if g.params.get("individual", True):
            if check in check_list:
                return g.member_list.get(check, check)
        else:
            if check in check_team:
                return check
        return ""

    if (ret_name := _judge(textutil.str_conv(pname, "h2z"))):  # 半角数字 -> 全角数字
        return ret_name

    pname = honor_remove(pname)  # 敬称削除

    if (ret_name := _judge(pname)):
        return ret_name

    if (ret_name := _judge(textutil.str_conv(pname, "k2h"))):  # カタカナ -> ひらがな
        return ret_name

    if (ret_name := _judge(textutil.str_conv(pname, "h2k"))):  # ひらがな -> カタカナ
        return ret_name

    # メンバーリストに見つからない場合
    if g.params.get("unregistered_replace", True):
        pname = g.cfg.member.guest_name
    if pname != g.cfg.member.guest_name and add_mark:
        pname = f"{pname}({g.cfg.setting.guest_mark})"

    return pname


def honor_remove(name: str) -> str:
    """敬称削除

    Args:
        name (str): 対象の名前

    Returns:
        str: 敬称を削除した名前
    """

    honor = r"(くん|さん|ちゃん|クン|サン|チャン|君)$"
    if re.match(fr".*{honor}", name):
        if not re.match(fr".*(っ|ッ|ー){honor}", name):
            name = re.sub(fr"{honor}", "", name)

    return name


def anonymous_mapping(name_list: list, initial: int = 0) -> dict:
    """名前リストから変換用辞書を生成

    Args:
        name_list (list): 名前リスト
        initial (int, optional): インデックス初期値. Defaults to 0.

    Returns:
        dict: マッピング用辞書
    """

    ret: dict = {}

    if g.params.get("individual", True):
        prefix = "Player"
        id_list = lookup.db.get_member_id()
    else:
        prefix = "Team"
        id_list = {x["team"]: x["id"] for x in g.team_list}

    if len(name_list) == 1:
        name = name_list[0]
        if name in id_list:
            idx = id_list[name]
        else:
            idx = int(random.random() * 100 + 100)
        ret[name] = f"{prefix}_{idx + initial:03d}"
    else:
        random.shuffle(name_list)
        for idx, name in enumerate(name_list):
            ret[name] = f"{prefix}_{idx + initial:03d}"

    return ret


def df_rename(df: pd.DataFrame, short=True, kind=0) -> pd.DataFrame:
    """カラム名をリネームする

    Args:
        df (pd.DataFrame): 対象データフレーム
        short (bool, optional): 略語にリネーム. Defaults to True.
        kind (int, optional): メモの種類

    Returns:
        pd.DataFrame: リネーム後のデータフレーム
    """

    rename_dict: dict = {
        "playtime": "日時",
        "rate": "レート",
        "participation_rate": "ゲーム参加率",
        "total_count": "集計ゲーム数",
        #
        "rpoint": "素点",
        "point": "獲得ポイント",
        "rpoint_avg": "平均素点",
        "top2_rate": "連対率", "top2": "連対数",
        "top3_rate": "ラス回避率", "top3": "ラス回避数",
        "point_dev": "得点偏差", "rank_dev": "順位偏差",
        "grade": "段位",
        # レコード
        "max_top": "連続トップ", "max_top2": "連続連対", "max_top3": "連続ラス回避",
        "max_low": "連続トップなし", "max_low2": "連続逆連対", "max_low4": "連続ラス",
        "point_max": "最大獲得ポイント", "point_min": "最小獲得ポイント",
        "rpoint_max": "最大素点", "rpoint_min": "最小素点",
        # 直接対決
        "results": "対戦結果", "win%": "勝率",
        "my_point_sum": "獲得ポイント(自分)", "my_point_avg": "平均ポイント(自分)",
        "vs_point_sum": "獲得ポイント(相手)", "vs_point_avg": "平均ポイント(相手)",
        "my_rpoint_avg": "平均素点(自分)", "my_rank_avg": "平均順位(自分)", "my_rank_distr": "順位分布(自分)",
        "vs_rpoint_avg": "平均素点(相手)", "vs_rank_avg": "平均順位(相手)", "vs_rank_distr": "順位分布(相手)",
    }

    for x in df.columns:
        match x:
            case "rank":
                rename_dict[x] = "#" if short else "順位"
            case "name" | "player":
                rename_dict[x] = "名前" if short else "プレイヤー名"
            case "team":
                rename_dict[x] = "チーム" if short else "チーム名"
            case "count" | "game" | "game_count":
                rename_dict[x] = "ゲーム数"
            case "pt_total" | "total_point" | "point_sum" | "total_mix":
                rename_dict[x] = "通算" if short else "通算ポイント"
            case "pt_avg" | "avg_point" | "point_avg" | "avg_mix":
                rename_dict[x] = "平均" if short else "平均ポイント"
            case "ex_point":
                rename_dict[x] = "卓外" if short else "卓外ポイント"
            case "rank_distr" | "rank_distr1" | "rank_distr2":
                rename_dict[x] = "順位分布"
            case "rank_avg":
                rename_dict[x] = "平順" if short else "平均順位"
            case "1st" | "rank1" | "1st_mix":
                rename_dict[x] = "1位数"
            case "2nd" | "rank2" | "2nd_mix":
                rename_dict[x] = "2位数"
            case "3rd" | "rank3" | "3rd_mix":
                rename_dict[x] = "3位数"
            case "4th" | "rank4" | "4th_mix":
                rename_dict[x] = "4位数"
            case "1st(%)" | "rank1_rate":
                rename_dict[x] = "1位率"
            case "2nd(%)" | "rank2_rate":
                rename_dict[x] = "2位率"
            case "3rd(%)" | "rank3_rate":
                rename_dict[x] = "3位率"
            case "4th(%)" | "rank4_rate":
                rename_dict[x] = "4位率"
            case "1st_count":
                rename_dict[x] = "1位数"
            case "2nd_count":
                rename_dict[x] = "2位数"
            case "3rd_count":
                rename_dict[x] = "3位数"
            case "4th_count":
                rename_dict[x] = "4位数"
            case "flying" | "flying_mix":
                rename_dict[x] = "トビ" if short else "トビ数"
            case "flying_count":
                rename_dict[x] = "トビ数"
            case "flying_rate" | "flying(%)":
                rename_dict[x] = "トビ率"
            case "pt_diff":
                rename_dict[x] = "差分"
            case "diff_from_above":
                rename_dict[x] = "順位差"
            case "diff_from_top":
                rename_dict[x] = "トップ差"
            case "yakuman_mix" | "grandslam":
                rename_dict[x] = "役満和了"
            case "yakuman_count" | "gs_count":
                rename_dict[x] = "役満和了数"
            case "yakuman(%)" | "gs_rate":
                rename_dict[x] = "役満和了率"
            case "matter":
                match kind:
                    case 0:
                        rename_dict[x] = "和了役"
                    case 1:
                        rename_dict[x] = "内容"
                    case 2:
                        rename_dict[x] = "内容"

    if not g.params.get("individual"):
        rename_dict.update(name="チーム" if short else "チーム名")

    return df.rename(columns=rename_dict)


def df_to_dict(df: pd.DataFrame, step: int = 40, index: bool = False) -> dict:
    """DataFrameからテキスト変換

    Args:
        df (pd.DataFrame): 対象データ
        step (int, optional): 分割行. Defaults to 40.
        index (bool, optional): インデックスを含める. Defaults to False.

    Returns:
        dict: 整形テキスト
    """

    msg: dict = {}
    floatfmt = floatfmt_adjust(df, index)

    # インデックスの振りなおし
    df.reset_index(inplace=True, drop=True)
    df.index += 1

    def _to_text(tmp_df: pd.DataFrame) -> str:
        ret = tmp_df.to_markdown(
            index=index,
            tablefmt="simple",
            numalign="right",
            floatfmt=floatfmt,
        ).replace("   nan", "******")
        ret = re.sub(r"  -([0-9]+)", r" ▲\1", ret)  # マイナスを記号に置換
        return ret

    if step:
        for s_line, e_line in textutil.split_line(len(df), step):
            t = _to_text(df[s_line:e_line])
            msg[str(s_line)] = t
    else:
        t = _to_text(df)
        msg["0"] = t

    return msg


def df_to_ranking(df: pd.DataFrame, title: str, step: int = 40) -> dict:
    """DataFrameからランキングテーブルを生成

    Args:
        df (pd.DataFrame): ランキングデータ
        title (str): 種別
        step (int, optional): 分割行. Defaults to 40.

    Returns:
        dict: 整形テキスト
    """

    # 表示内容
    match title:
        case "ゲーム参加率":
            df["内容"] = df.apply(lambda x: f"<>{x["ゲーム参加率"]:>7.2%} ({x["ゲーム数"]:4d}G /{x["集計ゲーム数"]:4d}G)", axis=1)
        case "通算ポイント":
            df["内容"] = df.apply(lambda x: f"<>{x["通算ポイント"]:>+7.1f}pt ({x["ゲーム数"]:4d}G)", axis=1)
        case "平均ポイント":
            df["内容"] = df.apply(lambda x: f"<>{x["平均ポイント"]:>+7.1f}pt ( {x["通算ポイント"]:>+7.1f}pt /{x["ゲーム数"]:4d}G)", axis=1)
        case "平均収支":
            df["内容"] = df.apply(lambda x: f"<>{x["平均素点"] - 25000:>6.0f}点 ({x["平均素点"]:>6.0f}点 /{x["ゲーム数"]:4d}G)", axis=1)
        case "トップ率":
            df["内容"] = df.apply(lambda x: f"<>{x["1位率"]:>7.2%} ({x["1位数"]:3d} /{x["ゲーム数"]:4d}G)", axis=1)
        case "連対率":
            df["内容"] = df.apply(lambda x: f"<>{x["連対率"]:>7.2%} ({x["連対数"]:3d} /{x["ゲーム数"]:4d}G)", axis=1)
        case "ラス回避率":
            df["内容"] = df.apply(lambda x: f"<>{x["ラス回避率"]:>7.2%} ({x["ラス回避数"]:3d} /{x["ゲーム数"]:4d}G)", axis=1)
        case "トビ率":
            df["内容"] = df.apply(lambda x: f"<>{x["トビ率"]:>7.2%} ({x["トビ数"]:3d} /{x["ゲーム数"]:4d}G)", axis=1)
        case "平均順位":
            df["内容"] = df.apply(lambda x: f"<>{x["平均順位"]:>4.2f} ({x["順位分布"]})", axis=1)
        case "役満和了率":
            df["内容"] = df.apply(lambda x: f"<>{x["役満和了率"]:>7.2%} ({x["役満和了数"]:3d} /{x["ゲーム数"]:4d}G)", axis=1)
        case "最大素点":
            df["内容"] = df.apply(lambda x: f"<>{x["最大素点"]:>6.0f}点 ({x["最大獲得ポイント"]:>+7.1f}pt)", axis=1)
        case "連続トップ":
            df["内容"] = df.apply(lambda x: f"<>{x["連続トップ"]:>2d}連続 ({x["ゲーム数"]:4d}G)", axis=1)
        case "連続連対":
            df["内容"] = df.apply(lambda x: f"<>{x["連続連対"]:>2d}連続 ({x["ゲーム数"]:4d}G)", axis=1)
        case "連続ラス回避":
            df["内容"] = df.apply(lambda x: f"<>{x["連続ラス回避"]:>2d}連続 ({x["ゲーム数"]:4d}G)", axis=1)
        case _:
            return {}

    # 整形と分割
    ret_list: list = []
    for s_line, e_line in textutil.split_line(len(df), step):
        work_df = df[s_line:e_line]
        tbl = tabulate(work_df.filter(items=["順位", "プレイヤー名", "内容"]).values, showindex=False)
        ret = ""
        for line in tbl.splitlines()[1:-1]:
            line = re.sub(r"^(\s*\d+)(.*)", r"\1：\2", line)
            line = line.replace(" -", "▲")
            line = line.replace("<>", "")
            ret += f"{line}\n"
        ret_list.append(ret.rstrip())

    return {str(idx): data for idx, data in enumerate(ret_list)}


def df_to_remarks(df: pd.DataFrame) -> dict:
    """DataFrameからメモテーブルを生成

    Args:
        df (pd.DataFrame): データ

    Returns:
        dict: 整形テキスト
    """

    for col in df.columns:
        match col:
            case "日時":
                df["日時"] = df["日時"].map(lambda x: str(x).replace("-", "/"))
            case "卓外":
                df["卓外"] = df["卓外"].map(lambda x: f"{x}pt".replace("-", "▲"))

    if "卓外" in df.columns:
        df["表示"] = df.apply(lambda x: f"{x["日時"]} {x["内容"]} {x["卓外"]} ({x["名前"]})", axis=1)
    elif "和了役" in df.columns:
        df["表示"] = df.apply(lambda x: f"{x["日時"]} {x["和了役"]} ({x["名前"]})", axis=1)
    else:
        df["表示"] = df.apply(lambda x: f"{x["日時"]} {x["内容"]} ({x["名前"]})", axis=1)

    tbl = tabulate(df.filter(items=["表示"]).values, showindex=False).splitlines()[1:-1]

    return {"0": "\n".join(tbl)}


def group_strings(lines: list[str], limit: int = 3000) -> list[str]:
    """指定文字数まで改行で連結

    Args:
        lines (list[str]): 連結対象
        limit (int, optional): 制限値. Defaults to 3000.

    Returns:
        list[str]: 連結結果
    """

    result: list = []
    buffer: list = []

    for i, line in enumerate(lines):
        is_last = i == len(lines) - 1  # 最終ブロック判定
        max_char = limit * 1.5 if is_last else limit  # 1ブロックの最大値

        # 仮に追加したときの文字列長を計算
        temp = buffer + [line]
        total_len = len("".join(temp))

        if total_len <= max_char:
            buffer.append(line)
        else:
            if buffer:
                result.append("\n".join(buffer))
            buffer = [line]

    if buffer:
        result.append("\n".join(buffer))

    return result
