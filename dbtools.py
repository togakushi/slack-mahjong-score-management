#!/usr/bin/env python3

import lib.function as f
import lib.database as d

if __name__ == "__main__":
    # --- メンバーリスト
    f.configure.read_memberslist()

    # --- 突合
    count, msg, fts = d.comparison.score_comparison()
    if fts:
        d.comparison.remarks_comparison(fts)

    print(f">>> mismatch:{count['mismatch']}, missing:{count['missing']}, delete:{count['delete']}")
