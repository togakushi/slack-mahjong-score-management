"""
integrations/slack/events/comparison.py
"""

import logging
from typing import TYPE_CHECKING, cast

import libs.global_value as g
from cls.score import GameResult
from cls.timekit import ExtendedDatetime as ExtDt
from libs.data import lookup, modify, search
from libs.datamodels import ComparisonResults
from libs.types import StyleOptions
from libs.utils import formatter, validator

if TYPE_CHECKING:
    from integrations.protocols import MessageParserProtocol
    from integrations.slack.adapter import ServiceAdapter
    from libs.types import RemarkDict


def main(m: "MessageParserProtocol") -> None:
    """突合処理

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    g.adapter = cast("ServiceAdapter", g.adapter)

    if g.cfg.main_parser.has_section(m.status.source):
        g.adapter.conf.search_channel = lookup.internal.get_config_value(
            config_file=g.cfg.config_file,
            section=m.status.source,
            name="search_channel",
            val_type=str,
            fallback=g.adapter.conf.search_channel,
        )
        g.adapter.conf.search_after = lookup.internal.get_config_value(
            config_file=g.cfg.config_file,
            section=m.status.source,
            name="search_after",
            val_type=int,
            fallback=g.adapter.conf.search_after,
        )

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
    m.status.message = results


def check_omission(results: ComparisonResults):
    """スコア突合

    Args:
        results (ComparisonResults): 結果格納データクラス
    """

    g.adapter = cast("ServiceAdapter", g.adapter)
    slack_score: list[GameResult] = []
    keep_channel_id: list = []

    for work_m in set(g.adapter.functions.pickup_score()):
        if work_m.keyword in g.keyword_dispatcher:  # コマンドキーワードはスキップ
            continue
        if detection := validator.check_score(work_m):
            score = GameResult(**detection)
            for k, v in score.to_dict().items():  # 名前の正規化
                if str(k).endswith("_name"):
                    score.set(**{k: formatter.name_replace(str(v), not_replace=True)})
            # 保留チェック
            if check_pending(work_m):
                results.pending.append(score)
            else:
                slack_score.append(score)
                results.score_list.update({work_m.data.event_ts: work_m})
                keep_channel_id.append(work_m.data.channel_id)

    if slack_score:
        first_ts = float(min(x.ts for x in slack_score))
    else:
        first_ts = float(results.after.format("ts"))

    db_score = search.for_db_score(first_ts)

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
        else:  # 取りこぼし(追加)
            results.missing.append(score)
            logging.info("missing: %s (%s)", score.ts, ExtDt(float(score.ts)).format("ymdhms"))
            logging.debug(score.to_text("logging"))
            modify.db_insert(score, work_m)

    # DATABASE -> SLACK
    ts_list = [x.ts for x in slack_score]
    work_m = g.adapter.parser()
    work_m.status.command_type = "comparison"
    for score in db_score:
        if score.ts not in ts_list:  # 削除漏れ
            work_m.data.event_ts = score.ts
            if score.source:
                work_m.data.channel_id = score.source.replace("slack_", "")
            if work_m.data.channel_id in set(keep_channel_id):
                results.delete.append(score)
                logging.info("delete (Only database): %s (%s)", score.ts, ExtDt(float(score.ts)).format("ymdhms"))
                modify.db_delete(work_m)


def check_remarks(results: ComparisonResults):
    """メモ突合

    Args:
        results (ComparisonResults): 結果格納データクラス
    """

    g.adapter = cast("ServiceAdapter", g.adapter)
    slack_remarks: list["RemarkDict"] = []
    score_list: dict[str, GameResult] = {}

    for loop_m in results.score_list.values():
        if detection := validator.check_score(loop_m):
            score = GameResult(**detection)
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
            if loop_m.data.thread_ts in [x.ts for x in results.pending]:
                continue  # 紐付くゲーム結果が保留中
            slack_remarks.append(
                {
                    "thread_ts": loop_m.data.thread_ts,
                    "event_ts": loop_m.data.event_ts,
                    "name": pname,
                    "matter": matter,
                    "source": loop_m.status.source,
                }
            )

    db_remarks = search.for_db_remarks(float(results.after.format("ts")))

    # SLACK -> DATABASE
    work_m = cast("MessageParserProtocol", g.adapter.parser())

    for remark in slack_remarks:
        if remark in db_remarks:
            continue  # 変化なし
        if remark["thread_ts"] in [x.ts for x in results.pending]:
            continue  # 紐付くゲーム結果が保留中
        results.remark_mod.append(remark)

    if results.remark_mod:
        for remark in results.remark_mod:
            work_m.data.event_ts = remark["event_ts"]
            work_m.status.command_type = "comparison"
            work_m.data.channel_id = remark["source"].replace("slack_", "")
        work_m.status.command_type = "comparison"  # リセットがかかるので再セット
        work_m.data.channel_id = remark["source"].replace("slack_", "")
        modify.remarks_delete(work_m)
        modify.remarks_append(work_m, results.remark_mod)

    # DATABASE -> SLACK
    for remark in db_remarks:
        if remark not in slack_remarks:  # slackに記録なし
            if remark["source"] in {x.source for x in score_list.values()}:
                results.remark_del.append(remark)
                modify.remarks_delete_compar(remark, work_m)


def check_total_score(results: ComparisonResults):
    """素点合計の再チェック

    Args:
        results (ComparisonResults): 結果格納データクラス
    """

    for loop_m in results.score_list.values():
        if detection := validator.check_score(loop_m):
            score = GameResult(**detection)
            for k, v in score.to_dict().items():  # 名前の正規化
                if str(k).endswith("_name"):
                    score.set(**{k: formatter.name_replace(str(v), not_replace=True)})
            if score.deposit:
                results.invalid_score.append(score)


def check_pending(m: "MessageParserProtocol") -> bool:
    """保留チェック

    Args:
        m (MessageParserProtocol): メッセージデータ

    Returns:
        bool: 真偽
        - *True*: 保留中
        - *False*: チェック開始
    """

    g.adapter = cast("ServiceAdapter", g.adapter)

    now_ts = float(ExtDt().format("ts"))

    if m.data.edited_ts == "undetermined":
        check_ts = float(m.data.event_ts) + g.adapter.conf.search_wait
    else:
        check_ts = float(m.data.edited_ts) + g.adapter.conf.search_wait

    if check_ts > now_ts:
        return True
    return False
