import lib.event as e

def DispMainMenu():
    no = 0
    view = {}
    view["type"] = "home"
    view["blocks"] = []
    view, no = e.Button(view, no, text = "全体成績サマリ", value = "click_summary_menu", action_id = "summary_menu")
    view, no = e.Button(view, no, text = "ランキング", value = "click_ranking_menu", action_id = "ranking_menu")
    view, no = e.Button(view, no, text = "個人成績", value = "click_personal_menu", action_id = "personal_menu")
    view, no = e.Button(view, no, text = "直接対戦", value = "click_versus_menu", action_id = "versus_menu")

    return(view)


def DispSummryMenu():
    no = 0
    view = {}
    view["type"] = "home"
    view["blocks"] = []
    view, no = e.Header(view, no, "集計期間")
    view, no = e.SearchRangeChoice(view, no)
    view, no = e.PeriodSelection(view, no, text = "開始日", block_id = "bid-sday", action_id = "aid-sday")
    view, no = e.PeriodSelection(view, no, text = "終了日", block_id = "bid-eday", action_id = "aid-eday")
    view, no = e.SearchOptions(view, no, block_id = "bid-checkboxes")
    view, no = e.Button(view, no, text = "集計開始", value = "gobrei_search", action_id = "actionId-search")
    view, no = e.Button(view, no, text = "戻る", value = "click_back", action_id = "actionId-back")

    return(view)


def DispVersusMenu():
    no = 0
    view = {}
    view["type"] = "home"
    view["blocks"] = []

    # プレイヤー選択リスト
    view, no = e.UserSelect(view, no, block_id = "target_player", text = "対象プレイヤー")
    view, no = e.UserSelect(view, no, block_id = "vs_player", text = "対戦相手", add_list = ["全員"])

    view, no = e.Header(view, no, "集計期間")
    view, no = e.SearchRangeChoice(view, no)
    view, no = e.PeriodSelection(view, no, text = "開始日", block_id = "bid-sday", action_id = "aid-sday")
    view, no = e.PeriodSelection(view, no, text = "終了日", block_id = "bid-eday", action_id = "aid-eday")

    view, no = e.Button(view, no, text = "集計開始", value = "click_personal", action_id = "actionId-personal")
    view, no = e.Button(view, no, text = "戻る", value = "click_back", action_id = "actionId-back")
    view, no = e.Button(view, no, text = "てすと", value = "click_test", action_id = "actionId-test")

    return(view)
