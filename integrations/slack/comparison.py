"""
libs/api/slack/comparison.py
"""

import logging
from typing import TypedDict, cast

import libs.global_value as g
from cls.score import GameResult
from cls.timekit import ExtendedDatetime as ExtDt
from cls.types import RemarkDict
from integrations import factory
from integrations.protocols import MessageParserProtocol
from integrations.slack import functions
from libs.data import modify
from libs.functions import search
from libs.utils import dictutil

SlackSearchDict = dict[str, MessageParserProtocol]
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


def main(m: MessageParserProtocol) -> None:
    """データ突合の実施、その結果をslackにpostする"""
    api_adapter = factory.select_adapter(g.selected_service)

    # データ突合
    count, msg = data_comparison(m)
    logging.notice("count=%s", count)  # type: ignore

    # 突合結果
    after = ExtDt(days=-g.cfg.search.after).format("ymd")
    before = ExtDt().format("ymd")

    m.post.message = f"*【データ突合】* ({after} - {before})\n"
    if count["pending"]:
        m.post.message += f"＊ 保留：{count["pending"]}件\n"
        for x in msg["pending"]:
            m.post.message += f"\t\t{ExtDt(float(x)).format("ymdhms")}\n"
    m.post.message += f"＊ 不一致：{count["mismatch"]}件\n{msg["mismatch"]}"
    m.post.message += f"＊ 取りこぼし：{count["missing"]}件\n{msg["missing"]}"
    m.post.message += f"＊ 削除漏れ：{count["delete"]}件\n{msg["delete"]}"
    m.post.message += f"＊ メモ更新：{count["remark_mod"]}件\n{msg["remark_mod"]}"
    m.post.message += f"＊ メモ削除：{count["remark_del"]}件\n{msg["remark_del"]}"
    if count["invalid_score"] > 0:
        m.post.message += "\n*【素点合計不一致】*\n"
        m.post.message += msg["invalid_score"]

    m.post.thread = True
    api_adapter.post_message(m)


def data_comparison(m: MessageParserProtocol) -> tuple[dict, ComparisonDict]:
    """データ突合処理

    Args:
        m (MessageParserProtocol): メッセージデータ

    Returns:
        tuple[dict,ComparisonDict]:
        - dict: 処理された更新/追加/削除の件数
        - ComparisonDict: slackに返すメッセージ
    """

    count: dict = {}
    msg: dict = {}

    # slackログからゲーム結果を取得
    slack_score = functions.pickup_score()
    slack_remarks = functions.pickup_remarks()

    if slack_score:
        first_ts = float(min(slack_score))
    else:
        first_ts = float(ExtDt(days=-g.cfg.search.after).format("ts"))

    # データベースからゲーム結果を取得
    db_score = search.for_db_score(first_ts)
    db_remarks = search.for_db_remarks(first_ts)

    # 比較データ
    if g.args.debug:
        for _, s_val in slack_score.items():
            result = GameResult()
            result.calc(**s_val.get_score(g.cfg.search.keyword), rule_version=g.cfg.mahjong.rule_version)
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


def check_omission(m: MessageParserProtocol, slack_data: SlackSearchDict, db_data: DBSearchDict) -> tuple[dict, ComparisonDict]:
    """スコア取りこぼしチェック

    Args:
        m (MessageParserProtocol): メッセージデータ
        slack_data (SlackSearchDict): slack検索結果
        db_data (DBSearchDict): DB登録状況

    Returns:
        tuple[dict, ComparisonDict]: 修正内容(結果)
    """

    api_adapter = factory.select_adapter(g.selected_service)

    now_ts = float(ExtDt().format("ts"))
    count: dict[str, int] = {"mismatch": 0, "missing": 0, "delete": 0}
    msg: ComparisonDict = {"mismatch": "", "missing": "", "delete": "", "pending": []}

    for key, val in slack_data.items():
        # 保留チェック
        if val.data.edited_ts:
            check_ts = float(max(val.data.edited_ts)) + g.cfg.search.wait
        else:
            check_ts = float(key) + g.cfg.search.wait

        if check_ts > now_ts:
            msg["pending"].append(str(key))
            logging.info("pending(slack -> DB): %s", ExtDt(float(key)).format("ymdhms"))
            continue

        # "score"が取得できていない場合は処理をスキップ
        slack_score = GameResult()
        slack_score.calc(**val.get_score(g.cfg.search.keyword), rule_version=g.cfg.mahjong.rule_version)
        if not slack_score:
            continue

        reactions_data = []
        reactions_data.append(val.data.reaction_ok)
        reactions_data.append(val.data.reaction_ng)

        if key in db_data:  # slack -> DB チェック
            m.data.event_ts = key  # event_ts
            db_score = db_data[m.data.event_ts]
            if not g.cfg.setting.thread_report:  # スレッド内報告が禁止されているパターン
                if val.in_thread:
                    count["delete"] += 1
                    logging.notice("delete: %s (In-thread report)", slack_score)  # type: ignore
                    msg["delete"] += f"\t{ExtDt(float(m.data.event_ts)).format("ymdhms")} {slack_score.to_text()}\n"
                    modify.db_delete(m)

                    # リアクションの削除
                    if key in val.data.reaction_ok:
                        api_adapter.reactions.remove(g.cfg.setting.reaction_ok, ts=m.data.event_ts, ch=val.data.channel_id)
                    if key in val.data.reaction_ng:
                        api_adapter.reactions.remove(g.cfg.setting.reaction_ng, ts=m.data.event_ts, ch=val.data.channel_id)
                    continue

            if slack_score.to_dict() == db_score.to_dict():  # スコア比較
                logging.info("score check pass: %s %s", ExtDt(float(key)).format("ymdhms"), db_score.to_text())
                continue

            # 更新
            if db_score.rule_version == g.cfg.mahjong.rule_version:
                count["mismatch"] += 1
                logging.notice("mismatch: %s", ExtDt(float(key)).format("ymdhms"))  # type: ignore
                logging.info("  *  slack: %s", db_score.to_text())
                logging.info("  *     db: %s", slack_score.to_text())
                msg["mismatch"] += f"\t{ExtDt(float(key)).format("ymdhms")}\n"
                msg["mismatch"] += f"\t\t修正前：{db_score.to_text()}\n"
                msg["mismatch"] += f"\t\t修正後：{slack_score.to_text()}\n"
                modify.db_update(slack_score, m)
                functions.score_verification(slack_score, m, reactions_data)
            else:
                logging.info("score check skip: %s %s", ExtDt(float(key)).format("ymdhms"), db_score.to_text())
            continue

        # 追加
        if not g.cfg.setting.thread_report and val.in_thread:
            logging.notice("skip: %s (In-thread report)", slack_score)  # type: ignore
            continue

        count["missing"] += 1
        logging.notice("missing: %s (%s)", slack_score.ts, ExtDt(float(slack_score.ts)).format("ymdhms"))  # type: ignore
        msg["missing"] += f"\t{ExtDt(float(key)).format("ymdhms")} {slack_score.to_text()}\n"
        modify.db_insert(slack_score, val)
        functions.score_verification(slack_score, val, reactions_data)

    for key in db_data:  # DB -> slack チェック
        m.data.event_ts = key  # event_ts
        # 保留チェック
        if float(key) + g.cfg.search.wait > now_ts:
            msg["pending"].append(str(m.data.event_ts))
            logging.info("pending(DB -> slack): %s", ExtDt(float(m.data.event_ts)).format("ymdhms"))
            continue

        # 登録済みデータは処理をスキップ
        if key in slack_data:
            continue

        # 削除
        count["delete"] += 1
        logging.notice("delete: %s (Only database)", db_data[m.data.event_ts])  # type: ignore
        msg["delete"] += f"\t{ExtDt(float(m.data.event_ts)).format("ymdhms")} {db_data[m.data.event_ts].to_text()}\n"
        modify.db_delete(m)

        # メッセージが残っているならリアクションを外す
        if not m.data.channel_id:
            m.data.channel_id = api_adapter.lookup.get_channel_id()
        for icon in api_adapter.reactions.status(ts=m.data.event_ts, ch=m.data.channel_id):
            api_adapter.reactions.remove(icon, ts=m.data.event_ts, ch=m.data.channel_id)

    return (count, msg)


def check_remarks(m: MessageParserProtocol, slack_data: SlackSearchDict, db_data: list) -> tuple[dict, ComparisonDict]:
    """メモの取りこぼしチェック

    Args:
        slack_data (SlackSearchDict): slack検索結果
        db_data (list): DB登録状況

    Returns:
        tuple[dict, ComparisonDict]: 修正内容(結果)
    """

    now_ts = float(ExtDt().format("ts"))
    count: dict[str, int] = {"remark_mod": 0, "remark_del": 0}
    msg: ComparisonDict = {"remark_mod": "", "remark_del": "", "pending": []}

    # 比較用リスト生成
    slack_remarks: list[RemarkDict] = []
    detection = GameResult()
    for val in slack_data.values():
        detection.calc(**val.get_score(g.cfg.search.keyword))
        remark_list = val.get_remarks(g.cfg.cw.remarks_word)
        if remark_list:
            for name, matter in remark_list:
                if name in detection.to_list() and val.in_thread:
                    slack_remarks.append({
                        "thread_ts": str(val.data.thread_ts),
                        "event_ts": str(val.data.event_ts),
                        "name": name,
                        "matter": matter,
                    })

    # slack -> DB チェック
    for remark in slack_remarks:
        m.data.event_ts = remark["event_ts"]

        # 保留チェック
        if float(m.data.event_ts) + g.cfg.search.wait > now_ts:
            msg["pending"].append(m.data.event_ts)
            logging.info("pending(slack -> DB): %s", ExtDt(float(m.data.event_ts)).format("ymdhms"))
            continue

        if remark in db_data:
            logging.info("remark pass(slack -> DB): %s", remark)
        else:
            count["remark_mod"] += 1
            modify.remarks_delete(m)
            modify.remarks_append(m, [remark])
            logging.notice("modification(data mismatch): %s", remark)  # type: ignore

    # DB -> slack チェック
    for remark in db_data:
        if remark in slack_remarks:
            logging.info("remark pass(DB -> slack): %s", remark)
        else:
            count["remark_del"] += 1
            modify.remarks_delete_compar(remark, m)
            logging.notice("delete(missed deletion): %s", remark)  # type: ignore

    return (count, msg)


def check_total_score(slack_data: SlackSearchDict) -> tuple[dict, ComparisonDict]:
    """素点合計の再チェック

    Args:
        slack_data (SlackSearchDict): slack検索結果

    Returns:
        tuple[dict, ComparisonDict]: 修正内容(結果)
    """

    api_adapter = factory.select_adapter(g.selected_service)

    now_ts = float(ExtDt().format("ts"))
    count: dict[str, int] = {"invalid_score": 0}
    msg: ComparisonDict = {"invalid_score": "", "pending": []}

    for key, val in slack_data.items():
        # 保留チェック
        if val.data.edited_ts:
            check_ts = float(max(val.data.edited_ts)) + g.cfg.search.wait
        else:
            check_ts = float(key) + g.cfg.search.wait

        if check_ts > now_ts:
            msg["pending"].append(str(key))
            logging.info("pending(slack -> DB): %s", ExtDt(float(key)).format("ymdhms"))
            continue

        # "score"が取得できていない場合は処理をスキップ
        score_data = GameResult()  # fixme  バージョン情報がない
        score_data.calc(**val.get_score(g.cfg.search.keyword))
        if score_data:
            continue

        # 判定条件外のデータはスキップ
        if not g.cfg.setting.thread_report and val.in_thread:
            continue
        if score_data.rule_version != g.cfg.mahjong.rule_version:
            continue

        # 情報更新
        channel_id = val.data.channel_id

        score_data.calc()
        reaction_ok = val.data.reaction_ok
        reaction_ng = val.data.reaction_ng

        if score_data.deposit != 0:  # 素点合計と配給原点が不一致
            count["invalid_score"] += 1
            logging.notice("invalid score: %s deposit=%s", key, score_data.deposit)  # type: ignore
            msg["invalid_score"] += f"\t{ExtDt(float(key)).format("ymdhms")} [供託：{score_data.deposit}]{score_data.to_text()}\n"
            if reaction_ok is not None and key in reaction_ok:
                api_adapter.reactions.remove(g.cfg.setting.reaction_ok, ts=key, ch=channel_id)
            if reaction_ng is not None and key not in reaction_ng:
                api_adapter.reactions.append(g.cfg.setting.reaction_ng, ts=key, ch=channel_id)
        else:
            if reaction_ng is not None and key in reaction_ng:
                api_adapter.reactions.remove(g.cfg.setting.reaction_ng, ts=key, ch=channel_id)
            if reaction_ok is not None and key not in reaction_ok:
                api_adapter.reactions.append(g.cfg.setting.reaction_ok, ts=key, ch=channel_id)

    return (count, msg)
