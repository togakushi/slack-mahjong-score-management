"""
integrations/discord/events/comparison.py
"""

import asyncio
import logging
import re
from typing import TYPE_CHECKING, cast

from discord import Message
from discord.channel import TextChannel

import libs.global_value as g
from cls.score import GameResult
from cls.timekit import ExtendedDatetime as ExtDt
from cls.timekit import Format
from integrations.protocols import CommandType
from libs.data import modify, search
from libs.datamodels import ComparisonResults
from libs.types import RemarkDict, StyleOptions
from libs.utils import formatter, validator

if TYPE_CHECKING:
    from integrations.discord.adapter import ServiceAdapter
    from integrations.protocols import MessageParserProtocol


def main(m: "MessageParserProtocol"):
    """突合処理(非同期関数呼び出しラッパー)

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    asyncio.create_task(_wrapper(m))


async def _wrapper(m: "MessageParserProtocol"):
    g.adapter = cast("ServiceAdapter", g.adapter)
    results = ComparisonResults(search_after=-g.adapter.conf.search_after)
    messages_list: list["MessageParserProtocol"] = []

    await search_messages(results, messages_list)
    await check_omission(results, messages_list)
    await check_remarks(results, messages_list)
    await check_total_score(results, messages_list)

    m.post.headline = {m.keyword: results.output("headline")}
    m.set_data("不一致", results.output("mismatch"), StyleOptions(key_title=False))
    m.set_data("取りこぼし", results.output("missing"), StyleOptions(key_title=False))
    m.set_data("削除漏れ", results.output("delete"), StyleOptions(key_title=False))
    m.set_data("メモ更新", results.output("remark_mod"), StyleOptions(key_title=False))
    m.set_data("メモ削除", results.output("remark_del"), StyleOptions(key_title=False))
    if results.invalid_score:
        m.set_data("供託残り", results.output("invalid_score"), StyleOptions(key_title=False))

    m.post.thread = True
    m.status.action = "nothing"
    g.adapter.api.post(m)


async def search_messages(results: ComparisonResults, messages_list: list["MessageParserProtocol"]):
    """メッセージ全検索

    Args:
        results (ComparisonResults): 結果格納データクラス
        messages_list (list[MessageParserProtocol]): 検索結果
    """

    g.adapter = cast("ServiceAdapter", g.adapter)

    for ch in g.adapter.api.bot.get_all_channels():
        # アクセス権がないチャンネルはスキップ
        if not ch.permissions_for(ch.guild.me).read_messages:
            continue

        if isinstance(ch, TextChannel):
            channel = g.adapter.api.bot.get_channel(ch.id)
            if not isinstance(channel, TextChannel):
                continue

            logging.debug("channel: %s, after: %s", ch.name, results.after.format(Format.YMDHMS))

            messages = await channel.history(after=results.after.dt, oldest_first=True).flatten()
            for message in messages:
                if not isinstance(message, Message):
                    continue
                if message.author.bot:
                    continue

                work_m = g.adapter.parser()  # 検索結果格納用
                work_m.parser(message)
                if not work_m.check_updatable:  # DB更新不可チャンネルは対象外
                    logging.debug("skip limited channel.")
                    break

                messages_list.append(work_m)


async def check_omission(results: ComparisonResults, messages_list: list["MessageParserProtocol"]):
    """スコア突合

    Args:
        results (ComparisonResults): 結果格納データクラス
        messages_list (list[MessageParserProtocol]): 検索結果
    """

    g.adapter = cast("ServiceAdapter", g.adapter)
    discord_score: list[GameResult] = []

    for work_m in messages_list:
        if work_m.keyword in g.keyword_dispatcher:  # コマンドキーワードはスキップ
            continue
        if detection := validator.check_score(work_m):
            score = GameResult(**detection)
            for k, v in score.to_dict().items():  # 名前の正規化
                if str(k).endswith("_name"):
                    score.set(**{k: formatter.name_replace(str(v), not_replace=True)})
            discord_score.append(score)
            results.score_list.update({work_m.data.event_ts: work_m})
            logging.debug(score.to_text("logging"))

    db_score = search.for_db_score(float(results.after.format(Format.TS)))

    # DISCORD -> DATABASE
    ts_list = [x.ts for x in db_score]
    for score in discord_score:
        work_m = results.score_list[score.ts]
        if score.ts in ts_list:
            target = db_score[ts_list.index(score.ts)]
            if score != target:  # 不一致(更新)
                results.mismatch.append({"before": target, "after": score})
                logging.info("mismatch: %s (%s)", score.ts, ExtDt(float(score.ts)).format(Format.YMDHMS))
                logging.debug("  * discord: %s", score.to_text("detail"))
                logging.debug("  *      db: %s", target.to_text("detail"))
                modify.db_update(score, work_m)
        else:  # 取りこぼし(追加)
            results.missing.append(score)
            logging.info("missing: %s (%s)", score.ts, ExtDt(float(score.ts)).format(Format.YMDHMS))
            logging.debug(score.to_text("logging"))
            modify.db_insert(score, work_m)

    # DATABASE -> DISCORD
    ts_list = [x.ts for x in discord_score]
    work_m = g.adapter.parser()
    work_m.status.command_type = CommandType.COMPARISON
    for score in db_score:
        if score.ts not in ts_list:  # 削除漏れ
            results.delete.append(score)
            work_m.data.event_ts = score.ts
            if score.source:
                work_m.data.channel_id = score.source.replace("discord_", "")
            logging.info("delete (Only database): %s (%s)", score.ts, ExtDt(float(score.ts)).format(Format.YMDHMS))
            modify.db_delete(work_m)


async def check_remarks(results: ComparisonResults, messages_list: list["MessageParserProtocol"]):
    """メモ突合

    Args:
        results (ComparisonResults): 結果格納データクラス
        messages_list (list[MessageParserProtocol]): 検索結果
    """

    g.adapter = cast("ServiceAdapter", g.adapter)
    discord_remarks: list[RemarkDict] = []
    score_list: dict[str, GameResult] = {}

    for loop_m in messages_list:
        if detection := validator.check_score(loop_m):
            score = GameResult(**detection)
            for k, v in score.to_dict().items():  # 名前の正規化
                if str(k).endswith("_name"):
                    score.set(**{k: formatter.name_replace(str(v), not_replace=True)})
            score_list.update({loop_m.data.event_ts: score})

        if re.match(rf"^{g.cfg.setting.remarks_word}$", loop_m.keyword):
            for name, matter in zip(loop_m.argument[0::2], loop_m.argument[1::2]):
                # 対象外のメモはスキップ
                if not float(loop_m.data.thread_ts):
                    continue  # リプライになっていない
                if loop_m.data.thread_ts not in score_list:
                    continue  # ゲーム結果に紐付かない
                pname = formatter.name_replace(str(name), not_replace=True)
                if pname not in score_list[loop_m.data.thread_ts].to_list("name"):
                    continue  # ゲーム結果に名前がない

                discord_remarks.append(
                    {
                        "thread_ts": loop_m.data.thread_ts,
                        "event_ts": loop_m.data.event_ts,
                        "name": pname,
                        "matter": matter,
                        "source": loop_m.status.source,
                    }
                )

    db_remarks = search.for_db_remarks(float(results.after.format(Format.TS)))

    # DISCORD -> DATABASE
    work_m = g.adapter.parser()
    work_m.status.command_type = CommandType.COMPARISON

    for remark in discord_remarks:
        if remark in db_remarks:  # 変化なし
            continue
        results.remark_mod.append(remark)

    for event_ts in {x["event_ts"] for x in results.remark_mod}:
        work_m.data.event_ts = event_ts
        modify.remarks_delete(work_m)
    modify.remarks_append(work_m, results.remark_mod)

    # DATABASE -> DISCORD
    for remark in db_remarks:
        if remark not in discord_remarks:  # Discordに記録なし
            results.remark_del.append(remark)
            modify.remarks_delete_compar(remark, work_m)


async def check_total_score(results: ComparisonResults, messages_list: list["MessageParserProtocol"]):
    """素点合計の再チェック

    Args:
        results (ComparisonResults): 結果格納データクラス
        messages_list (list[MessageParserProtocol]): 検索結果
    """

    for work_m in messages_list:
        if detection := validator.check_score(work_m):
            score = GameResult(**detection)
            for k, v in score.to_dict().items():  # 名前の正規化
                if str(k).endswith("_name"):
                    score.set(**{k: formatter.name_replace(str(v), not_replace=True)})
            if score.deposit:
                results.invalid_score.append(score)
