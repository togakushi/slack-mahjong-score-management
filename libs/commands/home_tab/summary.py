"""
libs/commands/home_tab/summary.py
"""

import logging

import libs.global_value as g
from cls.timekit import ExtendedDatetime as ExtDt
from integrations import factory
from libs.commands import graph, ranking, results
from libs.commands.home_tab import ui_parts
from libs.functions.events.handler_registry import register
from libs.utils import dictutil


def build_summary_menu():
    """サマリメニュー生成"""
    g.app_var["screen"] = "SummaryMenu"
    g.app_var["no"] = 0
    g.app_var["view"] = {"type": "home", "blocks": []}
    ui_parts.header("【成績サマリ】")

    # 検索範囲設定
    date_dict = {x: ExtDt(hours=-g.cfg.setting.time_adjust).range(x).dict_format("ymd", "-") for x in ["今月", "先月", "全部"]}
    ui_parts.divider()
    ui_parts.radio_buttons(
        id_suffix="search_range",
        title="検索範囲",
        flag={
            "今月": f"今月：{date_dict["今月"]["start"]} ～ {date_dict["今月"]["end"]}",
            "先月": f"先月：{date_dict["先月"]["start"]} ～ {date_dict["先月"]["end"]}",
            "全部": f"全部：{date_dict["全部"]["start"]} ～ {date_dict["全部"]["end"]}",
            "指定": f"範囲指定：{g.app_var["sday"]} ～ {g.app_var["eday"]}",
        },
    )
    ui_parts.button(text="検索範囲設定", action_id="modal-open-period")

    # オプション
    ui_parts.divider()
    ui_parts.checkboxes(
        id_suffix="search_option",
        title="検索オプション",
        flag={
            "unregistered_replace": "ゲスト無効",
        },
        initial=["unregistered_replace"],
    )
    ui_parts.radio_buttons(
        id_suffix="output_option",
        title="出力オプション",
        flag={
            "normal": "通算ポイント",
            "score_comparisons": "通算ポイント比較",
            "point": "ポイント推移グラフ",
            "rank": "順位推移グラフ",
            "rating": "レーティング",
        },
    )

    ui_parts.divider()
    ui_parts.button(text="集計", action_id="summary_aggregation", style="primary")
    ui_parts.button(text="戻る", action_id="actionId-back", style="danger")


@register
def register_summary_handlers(app):
    """サマリメニュー"""
    @app.action("summary_menu")
    def handle_menu_action(ack, body):
        """メニュー項目生成

        Args:
            ack (_type_): ack
            body (dict): イベント内容
        """

        ack()
        logging.trace(body)  # type: ignore

        g.app_var["user_id"] = body["user"]["id"]
        g.app_var["view_id"] = body["view"]["id"]
        logging.info("[summary_menu] %s", g.app_var)

        build_summary_menu()
        g.appclient.views_publish(
            user_id=g.app_var["user_id"],
            view=g.app_var["view"],
        )

    @app.action("summary_aggregation")
    def handle_aggregation_action(ack, body):
        """成績サマリ集計

        Args:
            ack (_type_): ack
            body (dict): イベント内容
            client (slack_bolt.App.client): slack_boltオブジェクト
        """

        ack()
        logging.trace(body)  # type: ignore

        api_adapter = factory.select_adapter(g.selected_service)
        m = factory.select_parser(g.selected_service)

        m.parser(body)
        add_argument, app_msg, update_flag = ui_parts.set_command_option(body)
        g.cfg.results.always_argument.extend(add_argument)
        g.params = dictutil.placeholder(g.cfg.results, m)
        g.params.update(update_flag)

        g.appclient.views_update(
            view_id=g.app_var["view_id"],
            view=ui_parts.plain_text(f"{chr(10).join(app_msg)}"),
        )

        app_msg.pop()
        app_msg.append("集計完了")
        msg1: str = ""

        match g.app_var.get("operation"):
            case "point":
                count, ret = graph.summary.point_plot(m)
                if count:
                    m.post.file_list = [{"ポイント推移": ret}]
                    api_adapter.fileupload(m)
                else:
                    m.post.message = ret
                    api_adapter.post_message(m)
            case "rank":
                count, ret = graph.summary.rank_plot(m)
                if count:
                    m.post.file_list = [{"順位変動": ret}]
                    api_adapter.fileupload(m)
                else:
                    m.post.message = ret
                    api_adapter.post_message(m)
            case "rating":
                g.params["command"] = "ranking"
                m.post.headline, m.post.message, m.post.file_list = ranking.rating.aggregation(m)
                m.post.summarize = False
                api_adapter.post(m)
            case _:
                m.post.headline, m.post.message, m.post.file_list = results.summary.aggregation(m)
                m.post.summarize = False
                api_adapter.post(m)

        g.appclient.views_update(
            view_id=g.app_var["view_id"],
            view=ui_parts.plain_text(f"{chr(10).join(app_msg)}\n\n{msg1}".strip()),
        )

    @app.view("SummaryMenu_ModalPeriodSelection")
    def handle_view_submission(ack, view):
        """view更新

        Args:
            ack (_type_): ack
            view (dict): 描写内容
            client (slack_bolt.App.client): slack_boltオブジェクト
        """

        ack()
        for i in view["state"]["values"].keys():
            if "aid-sday" in view["state"]["values"][i]:
                g.app_var["sday"] = view["state"]["values"][i]["aid-sday"]["selected_date"]
            if "aid-eday" in view["state"]["values"][i]:
                g.app_var["eday"] = view["state"]["values"][i]["aid-eday"]["selected_date"]

        logging.info("[global var] %s", g.app_var)

        g.appclient.views_update(
            view_id=g.app_var["view_id"],
            view=build_summary_menu(),
        )
