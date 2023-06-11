import pathlib

import pandas
import pdfplumber
import re
import pandas as pd
import requests
import json

listKeyName = "list"
level1KeyName = "level1TypeName"
level2KeyName = "level2TypeName"
level3KeyName = "level3TypeName"
level4KeyName = "level4TypeName"
level5KeyName = "level5TypeName"


def getListByKey(jsonArray, level, key):
    for value in jsonArray:
        if value[level] == key:
            return value[listKeyName]
    else:
        return None


def buildTypeLevelJson(path):
    originDataFrame = pd.read_excel(str(path), sheet_name="物品列表")  # 读取原始数据
    originDataJsonArray: list = json.loads(originDataFrame.to_json(orient="records", force_ascii=False))  # 转成json格式
    # {'typeID': 18, '物品名称': '斜长岩', '第一市场分类': '制造和研究', '第二市场分类': '材料', '第三市场分类': '原材料', '第四市场分类': '标准矿石', '第五市场分类': '斜长岩'}
    typeLevelJsonArray = []
    for row in originDataJsonArray:
        if not row["第一市场分类"] is None:
            level1TypeName = row["第一市场分类"]
            if getListByKey(typeLevelJsonArray, level1KeyName, level1TypeName) is None:
                typeLevelJsonArray.append({level1KeyName: level1TypeName, listKeyName: []})
            level2List = getListByKey(typeLevelJsonArray, level1KeyName, level1TypeName)

            if not row["第二市场分类"] is None:
                level2TypeName = row["第二市场分类"]
                if getListByKey(level2List, level2KeyName, level2TypeName) is None:
                    level2List.append({level2KeyName: level2TypeName, listKeyName: []})
                level3List = getListByKey(level2List, level2KeyName, level2TypeName)

                if not row["第三市场分类"] is None:
                    level3TypeName = row["第三市场分类"]
                    if getListByKey(level3List, level3KeyName, level3TypeName) is None:
                        level3List.append({level3KeyName: level3TypeName, listKeyName: []})
                    level4List = getListByKey(level3List, level3KeyName, level3TypeName)

                    if not row["第四市场分类"] is None:
                        level4TypeName = row["第四市场分类"]
                        if getListByKey(level4List, level4KeyName, level4TypeName) is None:
                            level4List.append({level4KeyName: level4TypeName, listKeyName: []})
                        level5List = getListByKey(level4List, level4KeyName, level4TypeName)

                        if not row["第五市场分类"] is None:
                            level5TypeName = row["第五市场分类"]
                            if getListByKey(level5List, level5KeyName, level5TypeName) is None:
                                level5List.append({level5KeyName: level5TypeName, listKeyName: []})
    # print(typeLevelJsonArray)
    path = pathlib.Path("../asset/eve_type_level.json")
    if path.exists():
        path.unlink()
    with open(str(path), "w") as file:
        json.dump(typeLevelJsonArray, file, ensure_ascii=False)


def buildFlatItemJson(path):
    originDataFrame = pd.read_excel(str(path), sheet_name="物品列表")  # 读取原始数据
    originDataJsonArray: list = json.loads(originDataFrame.to_json(orient="records", force_ascii=False))  # 转成json格式
    # {'typeID': 18, '物品名称': '斜长岩', '第一市场分类': '制造和研究', '第二市场分类': '材料', '第三市场分类': '原材料', '第四市场分类': '标准矿石', '第五市场分类': '斜长岩'}
    flatItemJsonArray = []
    for row in originDataJsonArray:
        if not row["第一市场分类"] is None:
            flatItemJsonArray.append({
                "id": row["typeID"],
                "name": row["物品名称"],
                "level1TypeName": row["第一市场分类"] if (not row["第一市场分类"] is None) else "",
                "level2TypeName": row["第二市场分类"] if (not row["第二市场分类"] is None) else "",
                "level3TypeName": row["第三市场分类"] if (not row["第三市场分类"] is None) else "",
                "level4TypeName": row["第四市场分类"] if (not row["第四市场分类"] is None) else "",
                "level5TypeName": row["第五市场分类"] if (not row["第五市场分类"] is None) else "",
            })
    # print(flatItemJsonArray)
    path = pathlib.Path("../asset/eve_flat_item.json")
    if path.exists():
        path.unlink()
    with open(str(path), "w") as file:
        json.dump(flatItemJsonArray, file, ensure_ascii=False)


if __name__ == '__main__':
    buildTypeLevelJson("../asset/eve_price.xlsx")
    buildFlatItemJson("../asset/eve_price.xlsx")
