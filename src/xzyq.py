import pathlib
import pandas
import pdfplumber
import re
import pandas as pd
import requests
import json

locationHistoryList = {}


def loadRequestedLocationList():
    path = pathlib.Path("../asset/查询历史记录.json")
    if path.exists():
        with open(str(path)) as jsonFile:
            jsonMap = json.load(jsonFile)
        for address in jsonMap.keys():
            locationHistoryList[address] = jsonMap[address]


def saveRequestedLocation():
    if len(locationHistoryList) >= 0:
        print("开始保存当前地址请求记录到json文件")
        path = pathlib.Path("../asset/查询历史记录.json")
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
    result = request_poi_from_address(str(row["city"]), str(row["address"]))
    return result["poi_name"], result["poi_address"], result["poi_city"], result["poi_district"], result["lat"], result[
        "lng"]


def read_location_from_excel(path):
    # 读取文件中所有的sheet
    sheetList = pd.read_excel(path, sheet_name=None)
    print("文件中总共表数量：" + str(len(sheetList)))
    newSheetMap = {}
    for sheetName in sheetList.keys():
        print("正在打开sheet： " + sheetName)
        df = sheetList.get(sheetName)
        df[["poi_name", "poi_address", "poi_city", "poi_district", "lat", "lng"]] \
            = df.apply(search_address, axis=1, result_type="expand")
        newSheetMap[sheetName] = df
        saveRequestedLocation()

    writer = pd.ExcelWriter("../asset/中高风险地区统计表-包含坐标.xlsx")
    for sheetName in newSheetMap.keys():
        newSheetMap[sheetName].to_excel(writer, sheet_name=sheetName)
    writer.close()


def convertLocationExcelToJsonFile(locationExcelPath, patientCountExcelPath):
    locationSheetMap = pd.read_excel(locationExcelPath, sheet_name=None)
    patientCountSheetMap = pd.read_excel(patientCountExcelPath, sheet_name=None, dtype=object)
    print("风险区文件中总共表数量：" + str(len(locationSheetMap)))
    print("病历统计文件中总共表数量：" + str(len(patientCountSheetMap)))
    totalDataMap = {}
    # 开始统计风险区数据
    for sheetName in locationSheetMap.keys():
        nameArray = str(sheetName).split("-")
        if totalDataMap.get("{}-{}".format(nameArray[0], nameArray[1])) is None:
            totalDataMap["{}-{}".format(nameArray[0], nameArray[1])] = {}
        if totalDataMap.get("{}-{}".format(nameArray[0], nameArray[1])).get(nameArray[2]) is None:
            totalDataMap["{}-{}".format(nameArray[0], nameArray[1])][nameArray[2]] = {}

        df = locationSheetMap.get(sheetName).fillna("null")
        cityMap = totalDataMap["{}-{}".format(nameArray[0], nameArray[1])][nameArray[2]]

        for index, row in df.iterrows():
            if not checkLocationPointDataInvalid(row):
                if cityMap.get(row["poi_city"]) is None:
                    cityMap[row["poi_city"]] = {}
                if cityMap.get(row["poi_city"]).get(row["poi_district"]) is None:
                    cityMap[row["poi_city"]][row["poi_district"]] = []
                pointList = cityMap[row["poi_city"]][row["poi_district"]]
                pointData = row.to_dict()
                pointData.pop("Unnamed: 0")
                pointData["date"] = "{}-{}".format(nameArray[0], nameArray[1])
                pointList.append(pointData)

    # 开始统计病例增长数据
    for sheetName in patientCountSheetMap.keys():
        nameArray = str(sheetName).split("-")
        if totalDataMap.get("{}-{}".format(nameArray[0], nameArray[1])) is None:
            totalDataMap["{}-{}".format(nameArray[0], nameArray[1])] = {}
        if totalDataMap.get("{}-{}".format(nameArray[0], nameArray[1])).get("patient") is None:
            totalDataMap["{}-{}".format(nameArray[0], nameArray[1])]["patient"] = {}

        df = patientCountSheetMap.get(sheetName).fillna(0)
        cityMap = totalDataMap["{}-{}".format(nameArray[0], nameArray[1])]["patient"]

        for index, row in df.iterrows():
            if cityMap.get(row["city"]) is None:
                cityMap[row["city"]] = {}
            districtMap = cityMap[row["city"]]
            record = row.to_dict()
            record["date"] = "{}-{}".format(nameArray[0], nameArray[1])
            districtMap[row["district"]] = record

    path = pathlib.Path("../asset/totalData.json")
    if path.exists():
        path.unlink()
    with open(str(path), "w") as file:
        json.dump(totalDataMap, file, ensure_ascii=False)


def checkLocationPointDataInvalid(row):
    return row["poi_name"] == "null" or row["poi_address"] == "null" or row["poi_city"] == "null" or row[
        "poi_district"] == "null" or row["lat"] == 0 or row["lng"] == 0


def request_poi_from_address(city, address):
    if len(locationHistoryList) == 0:
        print("已查询记录尚未读取，开始从文件中读取历史查询记录")
        loadRequestedLocationList()
    if not locationHistoryList.get(city + "-" + address) is None:
        print("缓存中存在地址:" + city + "-" + address)
        return locationHistoryList.get(city + "-" + address)
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
                locationHistoryList[city + "-" + address] = {"address": city + "-" + address,
                                                             "poi_name": firstResult.get("name", "null"),
                                                             "poi_address": firstResult.get("address", "null"),
                                                             "poi_city": firstResult.get("city", "null"),
                                                             "poi_district": firstResult.get("area", "null"),
                                                             "lat": firstResult["location"]["lat"],
                                                             "lng": firstResult["location"]["lng"]}
                return locationHistoryList[city + "-" + address]
            else:
                print("查询 " + address + " ---- 未返回location ：" + str(firstResult))
    else:
        print("请求http返回值异常：" + response.status_code)
    locationHistoryList[city + "-" + address] = {"address": city + "-" + address,
                                                 "poi_name": "null",
                                                 "poi_address": "null",
                                                 "poi_city": "null",
                                                 "poi_district": "null",
                                                 "lat": 0,
                                                 "lng": 0}
    return locationHistoryList[city + "-" + address]


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
    # read_location_from_excel("asset/中高风险地区统计表-原始统计.xlsx")
    convertLocationExcelToJsonFile("asset/中高风险地区统计表-包含坐标.xlsx", "asset/西藏各地区单日新增病例数统计.xlsx")

# 林芝
# GET https://api.map.baidu.com/place/v2/search?query=巴宜区百盛药业有限公司&region=林芝地区&city_limit=98&output=json&scope=2&ak=EBRZYvda30n9EdMvL3k4veu8i7EeCsac
# Accept: application/json

### 日喀则
# GET https://api.map.baidu.com/place/v2/search?query=拉孜县曲下镇上退休基地东侧第三排&region=日喀则地区&city_limit=102&output=json&scope=2&ak=EBRZYvda30n9EdMvL3k4veu8i7EeCsac
# Accept: application/json

### 拉萨
# GET https://api.map.baidu.com/place/v2/search?query=西藏大学河坝林校区&region=拉萨市&city_limit=100&output=json&scope=2&ak=EBRZYvda30n9EdMvL3k4veu8i7EeCsac
# Accept: application/json
