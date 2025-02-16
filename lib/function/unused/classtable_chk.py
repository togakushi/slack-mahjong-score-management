#!/usr/bin/env python3

import json
import random

tablefile = "classtable_mahjongsoul.json"
tablefile = "classtable_tenho.json"

with open(tablefile) as f:
    class_data = json.load(f)

for i in range(len(class_data["table"])):
    print(i, class_data["table"][i])


def d(dani, point, rank):
    get_point = class_data["table"][dani]["acquisition"][rank - 1]
    new_point = point + get_point

    if new_point >= class_data["table"][dani]["point"][1]:  # level up
        if dani < len(class_data["table"]) - 1:  # カンストしてなければ判定
            dani += 1
            new_point = class_data["table"][dani]["point"][0]  # 初期値
        else:
            new_point = 0

    if new_point < 0:  # level down
        if class_data["table"][dani]["point"][0] == 0:  # 初期値が0は降段しない
            new_point = 0
        else:
            dani -= 1
            new_point = class_data["table"][dani]["point"][0]  # 初期値

    print("着順({}) [獲得:{}] [段位ポイント:{} -> {} ({}/{})] {}".format(
        rank,
        get_point,
        point, point + get_point,
        new_point,
        class_data["table"][dani]["point"][1],
        class_data["table"][dani]["class"],
    ))

    return (new_point, dani)


p = 0
dani = 0
r = None

# for r in [4,3,4,4,1,1,4,4,1,1,2,1,1,2,2,2,1,2,4,2,3,3,1,1,3,3,3,3,4,1,4,3,3,2,1,3,2,1,2,2,1,2,2,2,1,2,3,1,4,2,2,2,2,4,2,2,1,1,2,1,3,2,2,3,4,3,1,4,1,2,3,2,1,3,3,4,2,1,3,1,3,4,2,3,4,2,3,3,2,1,3,3,2,1,1,3,2,1,1,2,4,1,1,1,1,2,4,2,3,3,2,4,1,4,1,4,2,2,2,2,1,2,3,2,2,1,1,2,1,2,1,1,4,1,2,4,3,1,1,3,1,3,3,2,2,1,1,1,1,2,1,1,2,1,4,4,3,1,2,2,3,2,1,2,3,4,3,1,1,1,3,2,1,1,3,1,2,1,3,3,4,2,2,1,2,2,2,3,1,4,3,4,3,2,2,2,3,4,1,1,2,1,1,2,1,2,3,2,2,3,1,1,2,2,3,1,4,1,3,3,1,2,2,2,1,3,3,4,2,4,1,3,1,2,1,3,4,1]:
for i in range(1000):
    r = random.choice([1, 3, 2, 4, 1, 4])
    p, dani = d(dani, p, r)
