#!/usr/bin/env python3

import lib.function as f
import lib.database as d

if __name__ == "__main__":
    # ---
    f.configure.read_memberslist()
    command_option = f.configure.command_option_initialization("results")
    command_option["unregistered_replace"] = False # ゲスト無効
    command_option["aggregation_range"] = "全部" # 検索範囲

    # --- 突合
    count, msg, fts = d.comparison.score_comparison(command_option)
    if fts:
        d.comparison.remarks_comparison(fts)

    print(f">>> mismatch:{count['mismatch']}, missing:{count['missing']}, delete:{count['delete']}")
