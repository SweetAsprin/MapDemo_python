import pathlib

import pandas
import pdfplumber
import re
import numpy as np
import pandas as pd
import requests
import json

locationHistoryList = {}


def loadRequestedLocationList():
    path = pathlib.Path("asset/查询历史记录.json")
    if path.exists():
        with open(str(path)) as jsonFile:
            jsonMap = json.load(jsonFile)
        for address in jsonMap.keys():
            locationHistoryList[address] = jsonMap[address]


def saveRequestedLocation():
    if len(locationHistoryList) >= 0:
        path = pathlib.Path("asset/查询历史记录.json")
        if path.exists():
            path.unlink()
        with open(str(path), "w") as file:
            json.dump(locationHistoryList, file, ensure_ascii=False)


def parse_people(path):
    pdf = pdfplumber.open(path)
    text = ""
    for page in pdf.pages:
        text += (page.extract_text().replace(" ", "").replace("\n", ""))
    sentences = re.split("。|：", text)
    peoples = []
    for sentence in sentences:
        # print(sentence)
        if sentence.startswith("无症状") or sentence.startswith("确诊"):
            peoples.append(sentence.split("，"))
    for people in peoples:
        print(people)


def parse_location(path):
    pdf = pdfplumber.open(path)
    text = ""
    for page in pdf.pages:
        text += (page.extract_text().replace(" ", "").replace("\n", ""))
    sentences = re.split("。|：", text)
    for sentence in sentences:
        # print(sentence)
        if sentence.__contains__("高风险区") or sentence.__contains__("中风险区"):
            print("    " + sentence)


def convertPdfToTxt(path):
    if not str(path).endswith("pdf"):
        return
    pdfFile = pathlib.Path(path)
    # print(file.parent)
    # print(file.name.split(".")[0])
    txtFilePath = str(pdfFile.parent) + "/" + pdfFile.name.split(".")[0] + ".txt"
    # print(txtFilePath)
    txtFile = pathlib.Path(txtFilePath)
    if txtFile.exists():
        txtFile.unlink()
    text = ""
    if pdfFile.exists() and pdfFile.is_file():
        pdf = pdfplumber.open(pdfFile)
        for page in pdf.pages:
            text += (page.extract_text())
    sentenceArray = re.split("。|：|，|、|；| |\n", text)
    with open(str(txtFile), "a") as f:
        for sentence in sentenceArray:
            f.write(sentence)
            f.write("\n")
            # print(sentence, file=f)
    f.close()
    # for sentence in sentences:
    #     print(sentence)


def find_all_file(path, callback):
    dirPath = pathlib.Path(path)
    if dirPath.exists() or dirPath.is_dir():
        for file in dirPath.iterdir():
            if file.is_dir():
                find_all_file(str(file), callback)
            elif file.is_file():
                print("文件名： " + str(file))
                callback(str(file))


def search_address(row):
    result = request_poi_from_address(row["city"], row["address"])
    # "address": address,
    # "poi_name": firstResult["name"],
    # "poi_address": firstResult["address"],
    # "poi_city": firstResult["city"],
    # "poi_district": firstResult["area"],
    # "lat": firstResult["location"]["lat"],
    # "lng": firstResult["location"]["lng"]
    return result["poi_name"], result["poi_address"], result["poi_city"], result["poi_district"], result["lat"], result[
        "lng"]


def read_location_from_excel(path):
    # 读取文件中所有的表
    sheetList = pd.read_excel(path, sheet_name=None)
    print("文件中总共表数量：" + str(len(sheetList)))
    # for sheetName in sheetList.keys():
    #     df = sheetList.get(sheetName)
    #     print(df.head())
    df = list(sheetList.values())[1]
    print(df.head())
    df[["poi_name", "poi_address", "poi_city", "poi_district", "lat", "lng"]] = df.apply(search_address, axis=1,
                                                                                         result_type="expand")
    print(df.head())

    # df_yellow = pd.read_excel(path, sheet_name="yellow")
    # df_yellow[["poi", "lat", "lng"]] = df_yellow.apply(search_address, axis=1, result_type="expand")
    # df_yellow.to_excel("asset/林芝市测试数据_修改后.xlsx", sheet_name="yellow")
    #
    # writer = pd.ExcelWriter("asset/林芝市测试数据_修改后.xlsx")
    # df_red.to_excel(writer, sheet_name="red")
    # df_yellow.to_excel(writer, sheet_name="yellow")
    # writer.close()


def request_poi_from_address(city, address):
    if len(locationHistoryList) == 0:
        print("已查询记录尚未读取，开始从文件中读取历史查询记录")
        loadRequestedLocationList()
    if not locationHistoryList.get(address) is None:
        print("缓存中存在地址：" + city + "-" + address + "，直接返回结果")
        return locationHistoryList.get(address)
    else:
        print("开始从网络查询:" + city + "-" + address)
    codeMap = {"山南市": "97", "林芝市": "98", "昌都市": "99", "拉萨市": "100", "那曲市": "101", "日喀则市": "100",
               "阿里地区": "103"}
    url = "https://api.map.baidu.com/place/v2/search"
    param = {"output": "json", "scope": "2", "ak": "EBRZYvda30n9EdMvL3k4veu8i7EeCsac", "region": city,
             "city_limit": codeMap[city], "query": (city + address)}

    response = requests.get(url, params=param)
    if response.status_code == 200:
        jsonResponse = json.loads(response.text)
        if not ((jsonResponse is None) or (jsonResponse["results"] is None) or (len(jsonResponse["results"]) <= 0)):
            firstResult = jsonResponse["results"][0]
            if not firstResult.get("location") is None:
                # print("查询 " + address + " 成功：" + str(firstResult))
                locationHistoryList[address] = {"address": city + "-" + address,
                                                "poi_name": firstResult["name"],
                                                "poi_address": firstResult["address"],
                                                "poi_city": firstResult["city"],
                                                "poi_district": firstResult["area"],
                                                "lat": firstResult["location"]["lat"],
                                                "lng": firstResult["location"]["lng"]}
                return locationHistoryList[address]
            else:
                print("查询 " + address + " ---- 未返回location ：" + str(firstResult))
    else:
        print("请求http返回值异常：" + response.status_code)
    locationHistoryList[address] = {"address": city + "-" + address,
                                    "poi_name": "地址解析异常",
                                    "poi_address": "未知地址",
                                    "poi_city": "未知城市",
                                    "poi_district": "未知区县",
                                    "lat": 0,
                                    "lng": 0}
    return locationHistoryList[address]


def trimTxtBlankRow(path):
    if not str(path).endswith("txt"):
        return
    txtFile = pathlib.Path(path)
    sentenceArray = []
    with open(str(txtFile), "r") as f:
        for line in f:
            line.strip()
            if not line == "\n":
                array = re.split(".|，|。", line)
                if len(array) > 1 and array[0].isdigit():
                    for s in array[1:len(array)]:
                        sentenceArray.append(s)
                        # print(s)
                else:
                    sentenceArray.append(line)
    # print(sentenceArray)
    newTxtFilePath = str(path).replace("txt版", "txt版_改")
    newTxtFile = pathlib.Path(newTxtFilePath)
    if newTxtFile.exists():
        newTxtFile.unlink()
    elif not newTxtFile.parent.exists():
        newTxtFile.parent.mkdir(parents=True)
    with open(newTxtFilePath, "a+") as newF:
        for sentence in sentenceArray:
            newF.write(str(sentence))
            # print(sentence, file=f)
    newF.close()


if __name__ == '__main__':
    # parse_people("asset/1.pdf")
    # parse_location("asset/1.pdf")
    # find_all_file()
    # print(request_point_from_address("日喀则市", "拉孜县曲下镇上退休基地东侧第三排"))
    # convertPdfToTxt("/Users/asprinchang/Downloads/疫情数据相关/2022年西藏疫情防控/阿里/202205西藏自治区阿里地区应对新冠肺炎疫情工作领导小组办公室公告(第5号）.pdf")
    # find_all_file("/Users/asprinchang/Downloads/疫情数据相关/2022年西藏疫情防控", convertPdfToTxt)
    # trimTxtBlankRow("/Users/asprinchang/Downloads/txt版/阿里/202219西藏自治区阿里地区应对新冠肺炎疫情工作领导小组办公室公告(19号).txt")
    # find_all_file("/Users/asprinchang/Downloads/txt版", trimTxtBlankRow)
    read_location_from_excel("asset/中高风险地区统计表.xlsx")
    saveRequestedLocation()

# 林芝
# GET https://api.map.baidu.com/place/v2/search?query=巴宜区百盛药业有限公司&region=林芝地区&city_limit=98&output=json&scope=2&ak=EBRZYvda30n9EdMvL3k4veu8i7EeCsac
# Accept: application/json

### 日喀则
# GET https://api.map.baidu.com/place/v2/search?query=拉孜县曲下镇上退休基地东侧第三排&region=日喀则地区&city_limit=102&output=json&scope=2&ak=EBRZYvda30n9EdMvL3k4veu8i7EeCsac
# Accept: application/json

### 拉萨
# GET https://api.map.baidu.com/place/v2/search?query=西藏大学河坝林校区&region=拉萨市&city_limit=100&output=json&scope=2&ak=EBRZYvda30n9EdMvL3k4veu8i7EeCsac
# Accept: application/json
