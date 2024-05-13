#!/usr/bin/env python3

import lib.function as f
import lib.command as c
import lib.database as d
from lib.function import global_value as g

# ---
f.configure.read_memberslist()
command_option = f.configure.command_option_initialization("report")
argument = ["今月", "ゲスト無効"]
#argument = ["今月"]
_, _, _, command_option = f.common.argument_analysis(argument, command_option)

print(">>>", command_option)

print("=" * 80)
a = d.aggregate.game_summary(argument, command_option)
print(a)
print(d.aggregate.game_count(argument, command_option))
print("flying:", a["flying"].sum())
print("-" * 80)
for _, row in a.iterrows():
    print("{}\t{:>+6.1f}\t{:>6.1f}".format(
        row["name"],
        row["pt_total"],
        row["pt_diff"],
    ).replace("-", "▲").replace("nan", "******"))
#print("=" * 80)
#print(d.aggregate.personal_record(argument, command_option))
#print("=" * 80)
#print(d.aggregate.personal_results(argument, command_option))
