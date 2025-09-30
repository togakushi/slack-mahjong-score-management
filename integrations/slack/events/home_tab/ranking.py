"""
integrations/slack/events/home_tab/ranking.py
"""

import logging

import libs.global_value as g
from cls.timekit import ExtendedDatetime as ExtDt
from integrations.slack.adapter import ServiceAdapter
from integrations.slack.events.handler_registry import register
from integrations.slack.events.home_tab import ui_parts
from libs.commands import ranking
from libs.utils import dictutil


def build_ranking_menu(adapter: ServiceAdapter):
    """ランキングメニュー生成

    Args:
        adapter (ServiceAdapter): インターフェースアダプタ
    """

    adapter.conf.tab_var["screen"] = "RankingMenu"
    adapter.conf.tab_var["no"] = 0
    adapter.conf.tab_var["view"] = {"type": "home", "blocks": []}
    adapter.conf.tab_var.setdefault("sday", ExtDt().format("ymd", "-"))
    adapter.conf.tab_var.setdefault("eday", ExtDt().format("ymd", "-"))
    ui_parts.header(adapter, text="【ランキング】")

    # 検索範囲設定
    date_dict = {x: ExtDt(hours=-g.cfg.setting.time_adjust).range(x).dict_format("ymd", "-") for x in ["今月", "先月", "全部"]}
    ui_parts.divider(adapter)
    ui_parts.radio_buttons(
        adapter=adapter,
        id_suffix="search_range",
        title="検索範囲",
        flag={
            "今月": f"今月：{date_dict["今月"]["start"]} ～ {date_dict["今月"]["end"]}",
            "先月": f"先月：{date_dict["先月"]["start"]} ～ {date_dict["先月"]["end"]}",
            "全部": f"全部：{date_dict["全部"]["start"]} ～ {date_dict["全部"]["end"]}",
            "指定": f"範囲指定：{adapter.conf.tab_var["sday"]} ～ {adapter.conf.tab_var["eday"]}",
        }
    )
    ui_parts.button(adapter, text="検索範囲設定", action_id="modal-open-period")

    # 検索オプション
    ui_parts.divider(adapter)
    ui_parts.checkboxes(
        adapter=adapter,
        id_suffix="search_option",
        title="検索オプション",
        flag={
            "unregistered_replace": "ゲスト無効",
        },
        initial=["unregistered_replace"],
    )

    ui_parts.input_ranked(adapter, block_id="bid-ranked")

    ui_parts.divider(adapter)
    ui_parts.button(adapter, text="集計", action_id="ranking_aggregation", style="primary")
    ui_parts.button(adapter, text="戻る", action_id="actionId-back", style="danger")


@register
def register_ranking_handlers(app, adapter: ServiceAdapter):
    """ランキングメニュー"""

    @app.action("ranking_menu")
    def handle_menu_action(ack, body):
        """メニュー項目生成

        Args:
            ack (_type_): ack
            body (dict): イベント内容
        """

        ack()
        logging.trace(body)  # type: ignore

        adapter.conf.tab_var["user_id"] = body["user"]["id"]
        adapter.conf.tab_var["view_id"] = body["view"]["id"]
        logging.info("[ranking_menu] %s", adapter.conf.tab_var)

        build_ranking_menu(adapter)
        adapter.conf.appclient.views_publish(
            user_id=adapter.conf.tab_var["user_id"],
            view=adapter.conf.tab_var["view"],
        )

    @app.action("ranking_aggregation")
    def handle_aggregation_action(ack, body):
        """メニュー項目生成

        Args:
            ack (_type_): ack
            body (dict): イベント内容
        """

        ack()
        logging.trace(body)  # type: ignore

        m = adapter.parser()

        m.parser(body)
        add_argument, app_msg, update_flag = ui_parts.set_command_option(adapter, body)
        m.data.text = f"dummy {" ".join(add_argument)}"
        g.params = dictutil.placeholder(g.cfg.ranking, m)
        g.params.update(update_flag)

        adapter.conf.appclient.views_update(
            view_id=adapter.conf.tab_var["view_id"],
            view=ui_parts.plain_text(f"{chr(10).join(app_msg)}"),
        )

        search_options = body["view"]["state"]["values"]
        if "bid-ranked" in search_options:
            if "value" in search_options["bid-ranked"]["aid-ranked"]:
                ranked = int(search_options["bid-ranked"]["aid-ranked"]["value"])
                if ranked > 0:
                    g.params.update(ranked=ranked)

        app_msg.pop()
        app_msg.append("集計完了")

        m.data.command_type = "ranking"
        ranking.ranking.aggregation(m)
        adapter.api.post(m)

        ui_parts.update_view(adapter, m, app_msg)

    @app.view("RankingMenu_ModalPeriodSelection")
    def handle_view_submission(ack, view):
        """view更新

        Args:
            ack (_type_): ack
            view (dict): 描写内容
        """

        ack()

        for i in view["state"]["values"].keys():
            if "aid-sday" in view["state"]["values"][i]:
                adapter.conf.tab_var["sday"] = view["state"]["values"][i]["aid-sday"]["selected_date"]
            if "aid-eday" in view["state"]["values"][i]:
                adapter.conf.tab_var["eday"] = view["state"]["values"][i]["aid-eday"]["selected_date"]

        adapter.conf.appclient.views_update(
            view_id=adapter.conf.tab_var["view_id"],
            view=build_ranking_menu(adapter),
        )
