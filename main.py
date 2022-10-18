import pathlib

import pdfplumber
import re
import numpy as np
import pandas as pd


# 97,山南地区
# 98,林芝地区
# 99,昌都地区
# 100,拉萨市
# 101,那曲地区
# 102,日喀则地区
# 103,阿里地区

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
    highLocation = []
    middleLocation = []
    for sentence in sentences:
        # print(sentence)
        if sentence.__contains__("高风险区") or sentence.__contains__("中风险区"):
            print("    " + sentence)


def find_all_file():
    dirPath = pathlib.Path("/Users/asprinchang/Downloads/疫情数据相关/2022年西藏疫情防控/拉萨")
    if dirPath.exists() or dirPath.is_dir():
        for file in dirPath.iterdir():
            if file.is_file() and file.name.endswith(".pdf") and file.name.__contains__("公告"):
                print("文件名： " + str(file))
                parse_location(file)


def read_location_from_excel(path):
    df = pd.read_excel(path)
    print(df.head())


if __name__ == '__main__':
    # parse_people("asset/1.pdf")
    # parse_location("asset/1.pdf")
    # find_all_file()
    read_location_from_excel("asset/林芝市测试数据.xlsx")

# 林芝
# GET https://api.map.baidu.com/place/v2/search?query=巴宜区百盛药业有限公司&region=林芝地区&city_limit=98&output=json&scope=2&ak=EBRZYvda30n9EdMvL3k4veu8i7EeCsac
# Accept: application/json

### 日喀则
# GET https://api.map.baidu.com/place/v2/search?query=拉孜县曲下镇上退休基地东侧第三排&region=日喀则地区&city_limit=102&output=json&scope=2&ak=EBRZYvda30n9EdMvL3k4veu8i7EeCsac
# Accept: application/json

### 拉萨
# GET https://api.map.baidu.com/place/v2/search?query=西藏大学河坝林校区&region=拉萨市&city_limit=100&output=json&scope=2&ak=EBRZYvda30n9EdMvL3k4veu8i7EeCsac
# Accept: application/json
