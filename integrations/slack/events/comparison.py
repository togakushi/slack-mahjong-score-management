"""
integrations/slack/events/comparison.py
"""

import copy
import logging
from typing import TYPE_CHECKING, TypedDict, cast

import libs.global_value as g
from cls.score import GameResult, Score
from cls.timekit import ExtendedDatetime as ExtDt
from libs.data import modify
from libs.data.lookup import db
from libs.functions import search
from libs.types import RemarkDict
from libs.utils import dictutil, formatter

if TYPE_CHECKING:
    from integrations.protocols import MessageParserProtocol
    from integrations.slack.adapter import ServiceAdapter

DBSearchDict = dict[str, GameResult]


class ComparisonDict(TypedDict, total=False):
    """メモ突合用辞書"""
    mismatch: str
    """差分"""
    missing: str
    """追加"""
    delete: str
    """削除"""
    remark_mod: str
    """メモの修正(追加/削除)"""
    remark_del: str
    """削除"""
    invalid_score: str
    """素点合計不一致"""
    pending: list[str]
    """保留"""


def main(m: "MessageParserProtocol") -> None:
    """データ突合の実施、その結果をslackにpostする"""

    g.adapter = cast("ServiceAdapter", g.adapter)

    if m.data.status == "message_changed":  # 編集イベントは無視
        return

    # 応答先
    m.post.thread = True
    m.post.ts = m.data.event_ts

    # データ突合
    count, msg = data_comparison(m)
    logging.debug("count=%s", count)
    # 突合結果
    after = ExtDt(days=-g.adapter.conf.search_after).format("ymd")
    before = ExtDt().format("ymd")

    message = f"*【データ突合】* ({after} - {before})\n"
    if count["pending"]:
        message += f"＊ 保留：{count["pending"]}件\n"
        for x in msg["pending"]:
            message += f"\t\t{ExtDt(float(x)).format("ymdhms")}\n"
    message += f"＊ 不一致：{count["mismatch"]}件\n{msg["mismatch"]}"
    message += f"＊ 取りこぼし：{count["missing"]}件\n{msg["missing"]}"
    message += f"＊ 削除漏れ：{count["delete"]}件\n{msg["delete"]}"
    message += f"＊ メモ更新：{count["remark_mod"]}件\n{msg["remark_mod"]}"
    message += f"＊ メモ削除：{count["remark_del"]}件\n{msg["remark_del"]}"
    if count["invalid_score"] > 0:
        message += "\n*【素点合計不一致】*\n"
        message += msg["invalid_score"]

    m.set_data("データ突合", message)
    m.post.key_header = False


def data_comparison(m: "MessageParserProtocol") -> tuple[dict, ComparisonDict]:
    """データ突合処理

    Args:
        m (MessageParserProtocol): メッセージデータ

    Returns:
        tuple[dict,ComparisonDict]:
        - dict: 処理された更新/追加/削除の件数
        - ComparisonDict: slackに返すメッセージ
    """

    g.adapter = cast("ServiceAdapter", g.adapter)
    count: dict = {}
    msg: dict = {}

    # slackログからゲーム結果を取得
    slack_score = g.adapter.functions.pickup_score()
    slack_remarks = g.adapter.functions.pickup_remarks()

    if slack_score:
        first_ts = float(min(x.data.event_ts for x in slack_score))
    else:
        first_ts = float(ExtDt(days=-g.adapter.conf.search_after).format("ts"))

    # データベースからゲーム結果を取得
    db_score = search.for_db_score(first_ts)
    db_remarks = search.for_db_remarks(first_ts)

    # 比較データ
    if g.args.debug:
        for s_val in set(slack_score):
            result = GameResult(**s_val.get_score(g.cfg.setting.keyword), **g.cfg.mahjong.to_dict())
            logging.info("slack data: %s", result)
        for _, d_val in db_score.items():
            logging.info("db data: %s", d_val)

    # --- スコア突合
    ret_count, ret_msg = check_omission(m, slack_score, db_score)
    count = dictutil.merge_dicts(count, ret_count)
    msg = dictutil.merge_dicts(msg, ret_msg)

    # --- 素点合計の再チェック(修正可能なslack側のみチェック)
    ret_count, ret_msg = check_total_score(slack_score)
    count = dictutil.merge_dicts(count, ret_count)
    msg = dictutil.merge_dicts(msg, ret_msg)

    # --- メモ突合
    ret_count, ret_msg = check_remarks(m, slack_remarks, db_remarks)
    count = dictutil.merge_dicts(count, ret_count)
    msg = dictutil.merge_dicts(msg, ret_msg)

    count.update(pending=len(msg["pending"]))

    return (count, cast(ComparisonDict, msg))


def check_omission(
    m: "MessageParserProtocol",
    slack_data: list["MessageParserProtocol"],
    db_data: DBSearchDict
) -> tuple[dict, ComparisonDict]:
    """スコア取りこぼしチェック

    Args:
        m (MessageParserProtocol): メッセージデータ
        slack_data (list["MessageParserProtocol"]): slack検索結果
        db_data (DBSearchDict): DB登録状況

    Returns:
        tuple[dict, ComparisonDict]: 修正内容(結果)
    """

    g.adapter = cast("ServiceAdapter", g.adapter)
    count: dict[str, int] = {"mismatch": 0, "missing": 0, "delete": 0}
    msg: ComparisonDict = {"mismatch": "", "missing": "", "delete": "", "pending": []}

    for slack_m in set(slack_data):
        slack_m.data.channel_id = m.data.channel_id

        # 保留チェック
        if check_pending(slack_m.data.event_ts, slack_m.data.edited_ts):
            msg["pending"].append(str(slack_m.data.event_ts))
            logging.info("pending(slack -> DB): %s", ExtDt(float(slack_m.data.event_ts)).format("ymdhms"))
            continue

        # "score"が取得できていない場合は処理をスキップ
        slack_score = GameResult(**slack_m.get_score(g.cfg.setting.keyword), **g.cfg.mahjong.to_dict())
        if not slack_score:
            continue

        # 名前の正規化
        g.params.update(unregistered_replace=False)
        for prefix in ("p1", "p2", "p3", "p4"):
            prefix_obj = cast(Score, getattr(slack_score, prefix))
            prefix_obj.name = formatter.name_replace(prefix_obj.name)

        if slack_score.ts in db_data:  # slack -> DB チェック
            db_score = db_data[slack_score.ts]
            if not g.adapter.conf.thread_report:  # スレッド内報告が禁止されているパターン
                if slack_m.in_thread:
                    count["delete"] += 1
                    logging.debug("delete (In-thread report): %s", slack_score.to_text("logging"))
                    msg["delete"] += f"\t{ExtDt(float(slack_m.data.event_ts)).format("ymdhms")} {slack_score.to_text()}\n"
                    modify.db_delete(slack_m)
                    g.adapter.functions.post_processing(slack_m)
                    continue

            if slack_score.to_dict() == db_score.to_dict():  # スコア比較
                logging.info("score check pass: %s %s", ExtDt(float(slack_score.ts)).format("ymdhms"), db_score.to_text())
                continue

            # 更新
            if db_data[slack_score.ts].rule_version == g.cfg.mahjong.rule_version:
                count["mismatch"] += 1
                logging.debug("mismatch: %s (%s)", slack_m.data.event_ts, ExtDt(float(slack_m.data.event_ts)).format("ymdhms"))
                logging.info("  *  slack: %s", db_score.to_text("detail"))
                logging.info("  *     db: %s", slack_score.to_text("detail"))
                msg["mismatch"] += f"\t{ExtDt(float(slack_score.ts)).format("ymdhms")}\n"
                msg["mismatch"] += f"\t\t修正前：{db_score.to_text()}\n"
                msg["mismatch"] += f"\t\t修正後：{slack_score.to_text()}\n"
                modify.db_update(slack_score, slack_m)
                g.adapter.functions.post_processing(slack_m)
            else:
                logging.info("score check skip: %s", db_score.to_text("logging"))
            continue

        # 追加
        if not g.adapter.conf.thread_report and slack_m.in_thread:
            logging.debug("skip (In-thread report): %s", slack_score.to_text("logging"))
            continue

        count["missing"] += 1
        logging.debug("missing: %s", slack_score.to_text("logging"))
        msg["missing"] += f"\t{ExtDt(float(slack_score.ts)).format("ymdhms")} {slack_score.to_text()}\n"
        modify.db_insert(slack_score, slack_m)
        g.adapter.functions.post_processing(slack_m)

    for _, db_score in db_data.items():  # DB -> slack チェック
        # 保留チェック
        if check_pending(db_score.ts):
            msg["pending"].append(db_score.ts)
            logging.info("pending(DB -> slack): %s", ExtDt(float(db_score.ts)).format("ymdhms"))
            continue

        # 登録済みデータは処理をスキップ
        if db_score.ts in [x.data.event_ts for x in slack_data]:
            continue

        # 削除
        count["delete"] += 1
        work_m = copy.deepcopy(m)
        work_m.data.event_ts = db_score.ts

        logging.debug("delete (Only database): %s", db_score.to_text("logging"))
        msg["delete"] += f"\t{ExtDt(float(db_score.ts)).format("ymdhms")} {db_score.to_text()}\n"
        modify.db_delete(work_m)
        g.adapter.functions.post_processing(work_m)

    return (count, msg)


def check_remarks(
    m: "MessageParserProtocol",
    slack_data: list["MessageParserProtocol"],
    db_data: list
) -> tuple[dict, ComparisonDict]:
    """メモの取りこぼしチェック

    Args:
        m (MessageParserProtocol): メッセージデータ
        slack_data (list["MessageParserProtocol"]): slack検索結果
        db_data (list): DB登録状況

    Returns:
        tuple[dict, ComparisonDict]: 修正内容(結果)
    """

    g.adapter = cast("ServiceAdapter", g.adapter)

    count: dict[str, int] = {"remark_mod": 0, "remark_del": 0}
    msg: ComparisonDict = {"remark_mod": "", "remark_del": "", "pending": []}
    work_m = copy.deepcopy(m)

    # 比較用リスト生成
    slack_remarks: list[RemarkDict] = []
    for val in slack_data:
        detection = db.exsist_record(val.data.thread_ts)
        for (name, matter) in val.data.remarks:
            pname = formatter.name_replace(name)
            if pname in detection.to_list() and val.in_thread:
                slack_remarks.append({
                    "thread_ts": str(val.data.thread_ts),
                    "event_ts": str(val.data.event_ts),
                    "name": pname,
                    "matter": matter,
                })

    # slack -> DB チェック
    for remark in slack_remarks:
        if check_pending(remark["event_ts"]):
            msg["pending"].append(remark["event_ts"])
            logging.info("pending(slack -> DB): %s", ExtDt(float(remark["event_ts"])).format("ymdhms"))
            continue

        if remark in db_data:
            logging.info("remark pass(slack -> DB): %s", remark)
        else:
            work_m.data.event_ts = remark["thread_ts"]
            count["remark_mod"] += 1
            modify.remarks_delete(work_m)
            modify.remarks_append(work_m, [remark])
            logging.debug("modification(data mismatch): %s", remark)

    # DB -> slack チェック
    for remark in db_data:
        if remark in slack_remarks:
            logging.info("remark pass(DB -> slack): %s", remark)
        else:
            m.data.event_ts = remark["thread_ts"]
            count["remark_del"] += 1
            modify.remarks_delete_compar(remark, m)
            logging.debug("delete(missed deletion): %s", remark)

    return (count, msg)


def check_total_score(slack_data: list["MessageParserProtocol"]) -> tuple[dict, ComparisonDict]:
    """素点合計の再チェック

    Args:
        slack_data (list["MessageParserProtocol"]): slack検索結果

    Returns:
        tuple[dict, ComparisonDict]: 修正内容(結果)
    """

    g.adapter = cast("ServiceAdapter", g.adapter)

    count: dict[str, int] = {"invalid_score": 0}
    msg: ComparisonDict = {"invalid_score": "", "pending": []}

    for val in set(slack_data):
        # 保留チェック
        if check_pending(val.data.event_ts, val.data.edited_ts):
            msg["pending"].append(str(val.data.event_ts))
            logging.info("pending(slack -> DB): %s", ExtDt(float(val.data.event_ts)).format("ymdhms"))
            continue

        # "score"が取得できていない場合は処理をスキップ
        slack_score = GameResult(**val.get_score(g.cfg.setting.keyword), **g.cfg.mahjong.to_dict())
        if not slack_score:
            continue

        # 判定条件外のデータはスキップ
        if not g.adapter.conf.thread_report and val.in_thread:
            continue
        if slack_score.rule_version != g.cfg.mahjong.rule_version:
            continue

        if slack_score.deposit != 0:  # 素点合計と配給原点が不一致
            count["invalid_score"] += 1
            logging.debug("invalid score: %s deposit=%s", slack_score.ts, slack_score.deposit)
            msg["invalid_score"] += f"\t{ExtDt(float(slack_score.ts)).format("ymdhms")} [供託：{slack_score.deposit}]{slack_score.to_text()}\n"
            if slack_score.ts in val.data.reaction_ok:
                g.adapter.functions.reaction_remove(g.adapter.conf.reaction_ok, ts=slack_score.ts, ch=val.data.channel_id)
            if slack_score.ts not in val.data.reaction_ng:
                g.adapter.functions.reaction_append(g.adapter.conf.reaction_ng, ts=slack_score.ts, ch=val.data.channel_id)
        else:
            if slack_score.ts in val.data.reaction_ng:
                g.adapter.functions.reaction_remove(g.adapter.conf.reaction_ng, ts=slack_score.ts, ch=val.data.channel_id)
            if slack_score.ts not in val.data.reaction_ok:
                g.adapter.functions.reaction_append(g.adapter.conf.reaction_ok, ts=slack_score.ts, ch=val.data.channel_id)

    return (count, msg)


def check_pending(event_ts: str, edited_ts: str = "undetermined") -> bool:
    """保留チェック

    Args:
        event_ts (str): イベント発生タイムスタンプ
        edited_ts (str, optional): イベント編集タイムスタンプ. Defaults to "undetermined".

    Returns:
        bool: 真偽
        - *True*: 保留中
        - *False*: チェック開始
    """

    g.adapter = cast("ServiceAdapter", g.adapter)

    now_ts = float(ExtDt().format("ts"))

    if edited_ts == "undetermined":
        check_ts = float(event_ts) + g.adapter.conf.search_wait
    else:
        check_ts = float(max(edited_ts)) + g.adapter.conf.search_wait

    if check_ts > now_ts:
        return True
    return False
