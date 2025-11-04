"""
integrations/slack/events/comparison.py
"""

import logging
from typing import TYPE_CHECKING, cast

import libs.global_value as g
from cls.score import GameResult
from cls.timekit import ExtendedDatetime as ExtDt
from libs.data import modify
from libs.datamodels import ComparisonResults
from libs.functions import search
from libs.types import RemarkDict, StyleOptions
from libs.utils import formatter

if TYPE_CHECKING:
    from integrations.protocols import MessageParserProtocol
    from integrations.slack.adapter import ServiceAdapter


def main(m: "MessageParserProtocol") -> None:
    """突合処理

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    g.adapter = cast("ServiceAdapter", g.adapter)
    results = ComparisonResults(search_after=-g.adapter.conf.search_after)

    check_omission(results)
    check_remarks(results)
    check_total_score(results)

    m.set_data("データ突合", results.output("headline"), StyleOptions(key_title=True))
    if results.pending:
        m.set_data("保留", results.output("pending"), StyleOptions(key_title=False))
    m.set_data("不一致", results.output("mismatch"), StyleOptions(key_title=False))
    m.set_data("取りこぼし", results.output("missing"), StyleOptions(key_title=False))
    m.set_data("削除漏れ", results.output("delete"), StyleOptions(key_title=False))
    m.set_data("メモ更新", results.output("remark_mod"), StyleOptions(key_title=False))
    m.set_data("メモ削除", results.output("remark_del"), StyleOptions(key_title=False))
    if results.invalid_score:
        m.set_data("供託残り", results.output("invalid_score"), StyleOptions(key_title=False))

    m.post.thread = True
    m.post.ts = m.data.event_ts
    m.status.action = "nothing"


def check_omission(results: ComparisonResults):
    g.adapter = cast("ServiceAdapter", g.adapter)
    slack_score: list[GameResult] = []

    for work_m in set(g.adapter.functions.pickup_score()):
        if (score := GameResult(**work_m.get_score(g.cfg.setting.keyword), **g.cfg.mahjong.to_dict())):
            for k, v in score.to_dict().items():  # 名前の正規化
                if str(k).endswith("_name"):
                    score.set(**{k: formatter.name_replace(str(v), not_replace=True)})
            # 保留チェック
            if check_pending(work_m.data.event_ts, work_m.data.edited_ts):
                results.pending.append(score)
            else:
                slack_score.append(score)
                results.score_list.update({work_m.data.event_ts: work_m})

    db_score = search.for_db_score(float(results.after.format("ts")))

    # SLACK -> DATABASE
    ts_list = [x.ts for x in db_score]
    for score in slack_score:
        work_m = results.score_list[score.ts]
        if score.ts in ts_list:
            target = db_score[ts_list.index(score.ts)]
            if score != target:  # 不一致(更新)
                results.mismatch.append({"before": target, "after": score})
                logging.info("mismatch: %s (%s)", score.ts, ExtDt(float(score.ts)).format("ymdhms"))
                logging.debug("  * slack: %s", score.to_text("detail"))
                logging.debug("  *    db: %s", target.to_text("detail"))
                modify.db_update(score, work_m)
                g.adapter.functions.post_processing(work_m)
        else:  # 取りこぼし(追加)
            results.missing.append(score)
            logging.info("missing: %s (%s)", score.ts, ExtDt(float(score.ts)).format("ymdhms"))
            logging.debug(score.to_text("logging"))
            modify.db_insert(score, work_m)
            g.adapter.functions.post_processing(work_m)

    # DATABASE -> SLACK
    ts_list = [x.ts for x in slack_score]
    work_m = g.adapter.parser()
    work_m.status.command_type = "comparison"
    for score in db_score:
        if score.ts not in ts_list:  # 削除漏れ
            results.delete.append(score)
            work_m.data.event_ts = score.ts
            if score.source:
                work_m.data.channel_id = score.source.replace("slack_", "")
            logging.info("delete (Only database): %s (%s)", score.ts, ExtDt(float(score.ts)).format("ymdhms"))
            modify.db_delete(work_m)
            g.adapter.functions.post_processing(work_m)


def check_remarks(results: ComparisonResults):
    """メモ突合

    Args:
        results (ComparisonResults): 結果格納データクラス
    """

    g.adapter = cast("ServiceAdapter", g.adapter)
    slack_remarks: list[RemarkDict] = []
    score_list: dict[str, GameResult] = {}

    for loop_m in results.score_list.values():
        if (score := GameResult(**loop_m.get_score(g.cfg.setting.keyword), **g.cfg.mahjong.to_dict())):
            for k, v in score.to_dict().items():  # 名前の正規化
                if str(k).endswith("_name"):
                    score.set(**{k: formatter.name_replace(str(v), not_replace=True)})
            score_list.update({loop_m.data.event_ts: score})

    for loop_m in g.adapter.functions.pickup_remarks():
        for name, matter in zip(loop_m.argument[0::2], loop_m.argument[1::2]):
            # 対象外のメモはスキップ
            if not float(loop_m.data.thread_ts):
                continue  # リプライになっていない
            if loop_m.data.thread_ts not in score_list:
                continue  # ゲーム結果に紐付かない
            pname = formatter.name_replace(str(name), not_replace=True)
            if pname not in score_list[loop_m.data.thread_ts].to_list("name"):
                continue  # ゲーム結果に名前がない

            slack_remarks.append({
                "thread_ts": loop_m.data.thread_ts,
                "event_ts": loop_m.data.event_ts,
                "name": pname,
                "matter": matter,
            })

    db_remarks = search.for_db_remarks(float(results.after.format("ts")))

    # SLACK -> DATABASE
    work_m = g.adapter.parser()
    work_m.status.command_type = "comparison"

    for remark in slack_remarks:
        if remark in db_remarks:  # 変化なし
            continue
        results.remark_mod.append(remark)

    for event_ts in {x["event_ts"] for x in results.remark_mod}:
        work_m.data.event_ts = event_ts
        modify.remarks_delete(work_m)
    modify.remarks_append(work_m, results.remark_mod)

    # DATABASE -> SLACK
    for remark in db_remarks:
        if remark not in slack_remarks:  # slackに記録なし
            results.remark_del.append(remark)
            modify.remarks_delete_compar(remark, work_m)


def check_total_score(results: ComparisonResults):
    for loop_m in results.score_list.values():
        if (score := GameResult(**loop_m.get_score(g.cfg.setting.keyword), **g.cfg.mahjong.to_dict())):
            for k, v in score.to_dict().items():  # 名前の正規化
                if str(k).endswith("_name"):
                    score.set(**{k: formatter.name_replace(str(v), not_replace=True)})
            if score.deposit:
                results.invalid_score.append(score)


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
