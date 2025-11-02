"""
integrations/discord/events/comparison.py
"""

import asyncio
import logging
from typing import TYPE_CHECKING, cast

from discord import Message
from discord.channel import TextChannel

import libs.global_value as g
from cls.score import GameResult
from cls.timekit import ExtendedDatetime as ExtDt
from libs.data import modify
from libs.datamodels import ComparisonResults
from libs.functions import search
from libs.types import StyleOptions
from libs.utils import formatter

if TYPE_CHECKING:
    from integrations.discord.adapter import ServiceAdapter
    from integrations.discord.parser import MessageParser
    from integrations.protocols import MessageParserProtocol


def main(m: "MessageParserProtocol"):

    asyncio.create_task(_wrapper(m))


async def _wrapper(m: "MessageParserProtocol"):
    g.adapter = cast("ServiceAdapter", g.adapter)
    count = ComparisonResults()

    await check_omission(count)

    message = ""
    message += f"＊ 不一致：{count.count_mismatch}件\n"
    message += "".join(count.mismatch)
    message += f"＊ 取りこぼし：{count.count_missing}件\n"
    message += "".join(count.missing)
    message += f"＊ 削除漏れ：{count.count_delete}件\n"
    message += "".join(count.delete)

    #
    after = ExtDt(days=-g.adapter.conf.search_after).format("ymd")
    before = ExtDt().format("ymd")
    m.post.headline = {"データ突合": f"突合範囲：{after} - {before}"}
    m.set_data("データ突合", message, StyleOptions(key_title=False))
    m.post.thread = True
    g.adapter.api.post(m)


async def check_omission(count: ComparisonResults):
    g.adapter = cast("ServiceAdapter", g.adapter)
    discord_score: list[GameResult] = []
    keep_m: dict[str, "MessageParser"] = {}
    after = ExtDt(days=-g.adapter.conf.search_after)

    # スコア探索
    for ch in g.adapter.api.bot.get_all_channels():
        # アクセス権がないチャンネルはスキップ
        if not ch.permissions_for(ch.guild.me).read_messages:
            continue

        if isinstance(ch, TextChannel):
            channel = g.adapter.api.bot.get_channel(ch.id)
            if not isinstance(channel, TextChannel):
                continue

            logging.debug("channel: %s, after: %s", ch.name, after.format("ymdhms"))

            messages = await channel.history(after=after.dt, oldest_first=True).flatten()
            for message in messages:
                if not isinstance(message, Message):
                    continue

                work_m = g.adapter.parser()  # 検索結果格納用
                work_m.parser(message)
                if not work_m.check_updatable:  # DB更新不可チャンネルは対象外
                    logging.debug("skip limited channel.")
                    break
                if message.author.bot:
                    continue

                if (score := GameResult(**work_m.get_score(g.cfg.setting.keyword), **g.cfg.mahjong.to_dict())):
                    for k, v in score.to_dict().items():  # 名前の正規化
                        if str(k).endswith("_name"):
                            score.set(**{k: formatter.name_replace(str(v), not_replace=True)})
                    discord_score.append(score)
                    keep_m.update({work_m.data.event_ts: work_m})
                    logging.debug(score.to_text("logging"))

    db_score = search.for_db_score2(float(after.format("ts")))
    # db_remarks = search.for_db_remarks(float(after.format("ts")))

    # スコア突合: DISCORD -> DATABASE
    ts_list = [x.ts for x in db_score]
    for score in discord_score:
        work_m = keep_m[score.ts]
        if score.ts in ts_list:
            target = db_score[ts_list.index(score.ts)]
            if score != target:  # 不一致(更新)
                count.mismatch.append(
                    f"{ExtDt(float(score.ts)).format("ymdhms")}\n\t修正前：{target.to_text("simple")}\n\t修正後：{score.to_text("simple")}\n"
                )
                logging.info("mismatch: %s (%s)", score.ts, ExtDt(float(score.ts)).format("ymdhms"))
                logging.debug("  * discord: %s", score.to_text("detail"))
                logging.debug("  *      db: %s", target.to_text("detail"))
                modify.db_update(score, work_m)
                g.adapter.functions.post_processing(work_m)
        else:  # 取りこぼし(追加)
            count.missing.append(f"{ExtDt(float(score.ts)).format("ymdhms")} {score.to_text("simple")}\n")
            logging.info("missing: %s (%s)", score.ts, ExtDt(float(score.ts)).format("ymdhms"))
            logging.debug(score.to_text("logging"))
            modify.db_insert(score, work_m)
            g.adapter.functions.post_processing(work_m)

    # スコア突合: DATABASE -> DISCORD
    ts_list = [x.ts for x in discord_score]
    work_m = g.adapter.parser()
    work_m.status.command_type = "comparison"
    for score in db_score:
        if score.ts not in ts_list:  # 削除漏れ
            count.delete.append(f"{ExtDt(float(score.ts)).format("ymdhms")} {score.to_text("simple")}\n")
            work_m.data.event_ts = score.ts
            if score.source:
                work_m.data.channel_id = score.source.replace("discord_", "")
            logging.info("delete (Only database): %s (%s)", score.ts, ExtDt(float(score.ts)).format("ymdhms"))
            modify.db_delete(work_m)
            g.adapter.functions.post_processing(work_m)
