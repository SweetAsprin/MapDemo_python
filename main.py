import pathlib

import pdfplumber
import re
import numpy as np
import pandas as pd
import requests
import json


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
            elif file.is_file() and file.name.endswith(".pdf"):
                print("文件名： " + str(file))
                callback(str(file))


def search_address(row):
    return request_point_from_address(row["city"], row["address"])


def read_location_from_excel(path):
    df_red = pd.read_excel(path, sheet_name="red")
    df_red[["poi", "lat", "lng"]] = df_red.apply(search_address, axis=1, result_type="expand")
    df_red.to_excel("asset/林芝市测试数据_修改后.xlsx", sheet_name="red")

    df_yellow = pd.read_excel(path, sheet_name="yellow")
    df_yellow[["poi", "lat", "lng"]] = df_yellow.apply(search_address, axis=1, result_type="expand")
    df_yellow.to_excel("asset/林芝市测试数据_修改后.xlsx", sheet_name="yellow")

    writer = pd.ExcelWriter("asset/林芝市测试数据_修改后.xlsx")
    df_red.to_excel(writer, sheet_name="red")
    df_yellow.to_excel(writer, sheet_name="yellow")
    writer.close()


def request_point_from_address(city, address):
    print("开始查询:" + city + address)
    codeMap = {"山南市": "97", "林芝市": "98", "昌都市": "99", "拉萨市": "100", "那曲市": "101", "日喀则市": "100",
               "阿里地区": "103"}
    url = "https://api.map.baidu.com/place/v2/search"
    param = {"output": "json", "scope": "2", "ak": "EBRZYvda30n9EdMvL3k4veu8i7EeCsac", "region": city,
             "city_limit": codeMap[city], "query": address}

    response = requests.get(url, params=param)
    if response.status_code == 200:
        jsonResponse = json.loads(response.text)
        if not ((jsonResponse is None) or (jsonResponse["results"] is None) or (len(jsonResponse["results"]) <= 0)):
            firstResult = jsonResponse["results"][0]
            if not firstResult.get("location") is None:
                # print("查询 " + address + " 成功：" + str(firstResult))
                return firstResult["name"], firstResult["location"]["lat"], firstResult["location"]["lng"]
            else:
                print("查询 " + address + " ---- 未返回location ：" + str(firstResult))
    else:
        print("请求http返回值异常：" + response.status_code)
    return "地址解析异常", 0, 0


if __name__ == '__main__':
    # parse_people("asset/1.pdf")
    # parse_location("asset/1.pdf")
    # find_all_file()
    # read_location_from_excel("asset/林芝市测试数据.xlsx")
    # print(request_point_from_address("日喀则市", "拉孜县曲下镇上退休基地东侧第三排"))
    # convertPdfToTxt("/Users/asprinchang/Downloads/疫情数据相关/2022年西藏疫情防控/阿里/202205西藏自治区阿里地区应对新冠肺炎疫情工作领导小组办公室公告(第5号）.pdf")
    find_all_file("/Users/asprinchang/Downloads/疫情数据相关/2022年西藏疫情防控",convertPdfToTxt)

# 林芝
# GET https://api.map.baidu.com/place/v2/search?query=巴宜区百盛药业有限公司&region=林芝地区&city_limit=98&output=json&scope=2&ak=EBRZYvda30n9EdMvL3k4veu8i7EeCsac
# Accept: application/json

### 日喀则
# GET https://api.map.baidu.com/place/v2/search?query=拉孜县曲下镇上退休基地东侧第三排&region=日喀则地区&city_limit=102&output=json&scope=2&ak=EBRZYvda30n9EdMvL3k4veu8i7EeCsac
# Accept: application/json

### 拉萨
# GET https://api.map.baidu.com/place/v2/search?query=西藏大学河坝林校区&region=拉萨市&city_limit=100&output=json&scope=2&ak=EBRZYvda30n9EdMvL3k4veu8i7EeCsac
# Accept: application/json
