import pathlib

import pdfplumber
import re
import numpy as np
import pandas as pd


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


if __name__ == '__main__':
    # parse_people("asset/1.pdf")
    # parse_location("asset/1.pdf")
    find_all_file()
