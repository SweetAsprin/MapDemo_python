import pathlib
import pandas as pd
import json
import pypinyin
import re
import cn2an

cityMap = None
tibetNameList = None
codeDictJsonMap = None


# 初始化西藏地区行政区域数组
def prepareTibetCityMap() -> json:
    path = pathlib.Path("../asset/tibetCityMap.json")
    with open(str(path)) as jsonFile:
        return json.load(jsonFile)


# 初始化西藏常见姓名数组
def prepareTibetNameList() -> json:
    path = pathlib.Path("../asset/tibetName.json")
    with open(str(path)) as jsonFile:
        return json.load(jsonFile)


# 填充"判决机关所在地市/县区"
def fillCourtCityDistrict(data: json):
    address: str = data["判决机关"].replace("西藏自治区", "").replace("西藏", "")
    for city in cityMap:
        cityName: str = city["name"].replace("市", "").replace("地区", "")
        if address.__contains__(cityName):  # 当前值包含特定市名称，直接设置市名
            data["判决机关所在地市"] = city["name"]
        for district in city["subCity"]:
            districtName: str = district.replace("县", "").replace("区", "")
            if address.__contains__(districtName):  # 当前值包含特定县区名称，设置县名，并填充对应市名
                data["判决机关所在地市"] = city["name"]
                data["判决机关所在县区"] = district
    if data["判决机关所在地市"] is None and data["判决机关所在县区"] is None:
        data["判决机关所在地市"] = "拉萨市"
        data["判决机关所在县区"] = "城关区"
    else:
        if data["判决机关所在县区"] is None:
            for city in cityMap:
                if city["name"] == data["判决机关所在地市"]:
                    data["判决机关所在县区"] = city["subCity"][0]
                    break

    data["判决机关所在地市"] = data["判决机关所在地市"].replace("市", "").replace("地区", "")
    data["判决机关所在县区"] = data["判决机关所在县区"].replace("县", "").replace("区", "")


# 填充"案号缩写新",值来自旧案号修改
def fillCaseNo(data: json):
    caseNoStr: str = data["案号"]
    oldNo: str = data["案号缩写旧"]
    data["案号缩写新"] = oldNo
    index = caseNoStr.find("）")
    if index != -1 and str(caseNoStr[index + 1]) != "藏" and oldNo.__contains__("z"):
        pinyin = pypinyin.pinyin(str(caseNoStr[index + 1]), style=pypinyin.NORMAL)
        firstPy = pinyin[0][0][0]
        # print(pinyin)
        # print(firstPy)
        data["案号缩写新"] = oldNo.replace("z", firstPy)


# 填充辩护人信息
def fillLawyer(data: json):
    lawyerDesc: str = data["是否请辩护人"]
    if lawyerDesc.startswith("否"):
        data["辩护人"] = "无"
    elif lawyerDesc.startswith("是"):
        if lawyerDesc.__contains__("司法局"):
            data["辩护人"] = "司法指定"
        elif lawyerDesc.__contains__("辩护人"):
            data["辩护人"] = "自请"
        else:
            data["辩护人"] = "未知"
    else:
        data["辩护人"] = "未知"


# 填充被告人户籍县市信息
def fillCulpritHomeInfo(data: json):
    culpritHomeDesc: str = data["被告人户籍"]
    if culpritHomeDesc.__contains__("未显示"):
        data["被告人所在市"] = "未知"
        data["被告人所在县"] = "未知"
    else:
        homeAddress = culpritHomeDesc.replace("西藏自治区", "").replace("西藏", "")
        homeInTibet = False
        for city in cityMap:
            needBreak = False
            cityName: str = city["name"].replace("市", "").replace("地区", "")
            if homeAddress.__contains__(cityName):  # 当前值包含特定市名称，直接设置市名
                data["被告人所在市"] = city["name"]
                homeInTibet = True
            for district in city["subCity"]:
                districtName: str = district.replace("县", "").replace("区", "")
                if homeAddress.__contains__(districtName):  # 当前值包含特定县区名称，设置县名，并填充对应市名
                    data["被告人所在市"] = city["name"]
                    data["被告人所在县"] = district
                    homeInTibet = True
                    needBreak = True
                    break
            if needBreak:
                break
        if not homeInTibet:
            data["被告人所在市"] = "内地"
            data["被告人所在县"] = "内地"

        if data["被告人所在县"] is None and data["被告人所在市"] is not None and data["被告人所在市"] != "未知" and \
                data["被告人所在市"] != "内地":
            # data["被告人所在县"] = cityMap[data["被告人所在市"]][0]
            for city in cityMap:
                if city["name"] == data["被告人所在市"]:
                    data["被告人所在县"] = city["subCity"][0]
                    break

    data["被告人所在市"] = data["被告人所在市"].replace("市", "").replace("地区", "")
    data["被告人所在县"] = data["被告人所在县"].replace("县", "").replace("区", "")


# 格式化赔偿金额数字
def fillMoneyNum(data: json):
    moneyDesc: str = data["谅解协议赔偿数额"]
    if moneyDesc is not None:
        if moneyDesc.__contains__("(") or moneyDesc.__contains__("（"):
            index = moneyDesc.find("(")
            if index == -1:
                index = moneyDesc.find("（")
            moneyDesc = moneyDesc[0:index]
        if moneyDesc.__contains__("元"):
            moneyNumStr = moneyDesc.replace(" ", "").replace(",", "").replace("，", "")
            moneyNum = 0
            if moneyNumStr.__contains__("万元"):
                moneyNumStr = moneyNumStr.replace("万元", "")
                if moneyNumStr.__contains__("."):  # 转小数
                    moneyNum = int(float(moneyNumStr) * 10000)
                else:  # 转整数
                    # print("当前需要转化的数字为：" + moneyNumStr)
                    moneyNum = int(cn2an.cn2an(moneyNumStr, "smart")) * 10000
            else:
                # print("当前需要转化的数字为：" + moneyNumStr)
                moneyNumStr = moneyNumStr.replace("元", "").replace("余", "").replace("多", "")
                moneyNum = int(cn2an.cn2an(moneyNumStr, "smart"))
            data["赔偿数额格式化"] = moneyNum
        else:
            data["赔偿数额格式化"] = moneyDesc
    else:
        data["赔偿数额格式化"] = "未赔偿"


# 判断姓名是否包含常见藏语名称
def checkIfNameIsTibet(name: str) -> bool:
    for tibetName in tibetNameList:
        if name.__contains__(tibetName):
            return True
    else:
        return False


# 填充审判长姓名及民族
def fillJudgeNameAndNation(data: json):
    judgeInfoDesc: str = data["法官或合议庭民族"]
    if judgeInfoDesc.startswith("审判"):
        tempJudgeDesc = judgeInfoDesc[2:len(judgeInfoDesc)]
        if tempJudgeDesc.__contains__(",") or tempJudgeDesc.__contains__("，") or tempJudgeDesc.__contains__(
                "审判") or tempJudgeDesc.__contains__("书记") or tempJudgeDesc.__contains__(
            "法官") or tempJudgeDesc.__contains__("人民"):
            indexList = []
            secondJudgeIndex = 999
            if tempJudgeDesc.find("审判") != -1:
                indexList.append(tempJudgeDesc.find("审判"))
            if tempJudgeDesc.find("书记") != -1:
                indexList.append(tempJudgeDesc.find("书记"))
            if tempJudgeDesc.find("法官") != -1:
                indexList.append(tempJudgeDesc.find("法官"))
            if tempJudgeDesc.find("人民") != -1:
                indexList.append(tempJudgeDesc.find("人民"))
            if tempJudgeDesc.find(",") != -1:
                indexList.append(tempJudgeDesc.find(","))
            if tempJudgeDesc.find("，") != -1:
                indexList.append(tempJudgeDesc.find("，"))

            for index in indexList:
                if index < secondJudgeIndex:
                    secondJudgeIndex = index

            judgeNameDesc = "审判" + tempJudgeDesc[0:secondJudgeIndex]
            judgeName = judgeNameDesc.replace("审判长", "").replace("审判员", "").replace(",", "").replace("，",
                                                                                                           "").replace(
                "：", "")
            isTibetName = checkIfNameIsTibet(judgeName)
            # if not isTibetName:
            #     print("当前判断得到的审判长姓名为：" + judgeName + " 非藏族")
            data["审判长姓名"] = judgeName
            if isTibetName:
                data["审判长民族"] = "藏"
            else:
                data["审判长民族"] = "汉"


# 对特定数据格式做优化
def formatData(row: dict):
    isBaoLi: str = row["前科是否是八种暴力性犯罪"]
    if isBaoLi is None or isBaoLi == "":
        row["前科是否是八种暴力性犯罪"] = "未知"
    elif len(isBaoLi) > 1:
        row["前科是否是八种暴力性犯罪"] = isBaoLi[0]

    # 处理所在市/县字段为拼音
    if row["判决机关所在地市"] is not None:
        row["判决机关所在地市"] = pypinyin.slug(row["判决机关所在地市"], separator="")
    if row["判决机关所在县区"] is not None:
        row["判决机关所在县区"] = pypinyin.slug(row["判决机关所在县区"], separator="")
    if row["被告人所在市"] is not None:
        row["被告人所在市"] = pypinyin.slug(row["被告人所在市"], separator="")
    if row["被告人所在县"] is not None:
        row["被告人所在县"] = pypinyin.slug(row["被告人所在县"], separator="")

    # 处理被告年龄字段
    age: str = row["被告人年龄"]
    if age.__contains__("（"):
        row["被告人年龄"] = age[0:age.find("（")]

    for key, value in row.items():
        # 处理是否类字段值后面跟括号备注的情况
        if key.startswith("是否") and value != "未知" and value is not None:
            row[key] = row[key][0]
        # 处理所有字段的"未显示"值
        if str(value).__contains__("未显示") or value is None:
            row[key] = "未知"
        # 处理所有字段值中的空格
        if str(value).__contains__(" "):
            row[key] = value.replace(" ", "")


# 计算被告人人数并根据人数排序
def calcCulpritNumAndSort(originDataJsonArray: list):
    # 计算人数
    for data in originDataJsonArray:
        culpritDesc: str = data["被告人"]
        culpritList = re.split("，|,|、", culpritDesc)
        data["被告人人数"] = len(culpritList)
    # 根据人数排序
    # print("总条数：" + len(originDataJsonArray).__str__())
    multipleCulpritDataList = []
    for data in originDataJsonArray:
        culpritNum = data["被告人人数"]
        if culpritNum > 1:
            multipleCulpritDataList.append(data)
    for data in multipleCulpritDataList:
        originDataJsonArray.remove(data)
    # print("单被告条数：" + len(originDataJsonArray).__str__())
    # print("多被告条数：" + len(multipleCulpritDataList).__str__())
    multipleCulpritDataList.sort(key=lambda x: x["被告人人数"])
    return multipleCulpritDataList


# 拆分多被告数据为多条
def splitMultipleCulpritData(multipleCulpritDataList):
    newDataList = []
    for data in multipleCulpritDataList:
        culpritList = re.split("，|,|。|、", data["被告人"].replace(" ", ""))
        culpritNationList = re.split("，|,|。|、", data["被告人民族"].replace(" ", ""))
        culpritHomeList = re.split("，|,|。|、", data["被告人户籍"].replace(" ", ""))
        culpritGenderList = re.split("，|,|。|、", data["被告人性别"].replace(" ", ""))
        culpritAgeList = re.split("，|,|。|、", data["被告人年龄"].replace(" ", ""))
        culpritResultList = re.split("，|,|。|、", data["判处结果"].replace(" ", ""))
        culpritIsZiShouList = re.split("，|,|。|、", data["是否自首"].replace(" ", ""))
        culpritIsLiGongList = re.split("，|,|。|、", data["是否立功"].replace(" ", ""))
        culpritIsTanBaiList = re.split("，|,|。|、", data["是否坦白"].replace(" ", ""))
        culpritIsCongFanList = re.split("，|,|。|、", data["是否从犯"].replace(" ", ""))
        culpritIsRenZuiList = re.split("，|,|。|、", data["是否认罪"].replace(" ", ""))
        culpritIsHuaiYunList = re.split("，|,|。|、", data["是否怀孕"].replace(" ", ""))
        culpritIsCanRenList = re.split("，|,|。|、", data["是否特别残忍"].replace(" ", ""))
        culpritIsGongKaiList = re.split("，|,|。|、", data["是否公开场合行凶"].replace(" ", ""))
        culpritIsXiongQiList = re.split("，|,|。|、", data["是否使用凶器"].replace(" ", ""))
        culpritIsChuFanList = re.split("，|,|。|、", data["是否初犯偶犯"].replace(" ", ""))
        culpritIsLeiFanList = re.split("，|,|。|、", data["是否构成累犯"].replace(" ", ""))
        culpritIsBaoLiList = re.split("，|,|。|、", data["前科是否是八种暴力性犯罪"].replace(" ", "")) \
            if data["前科是否是八种暴力性犯罪"] is not None else [" "]
        culpritIsGuoCuoList = re.split("，|,|。|、", data["被害人是否有过错"].replace(" ", ""))
        culpritIsLiangJieList = re.split("，|,|。|、", data["是否积极赔偿被害人损失并取得刑事谅解"].replace(" ", ""))

        for index, culpritName in enumerate(culpritList):
            culpritInfo = {}
            culpritInfo["判决书"] = data["判决书"]
            culpritInfo["判决机关"] = data["判决机关"]
            culpritInfo["判决机关所在地市"] = data["判决机关所在地市"]
            culpritInfo["判决机关所在县区"] = data["判决机关所在县区"]
            culpritInfo["案号"] = data["案号"]
            culpritInfo["案号缩写旧"] = data["案号缩写旧"] + "-" + str(index + 1)
            culpritInfo["案号缩写新"] = data["案号缩写新"]
            culpritInfo["判决日期"] = data["判决日期"]
            culpritInfo["判决年份"] = data["判决年份"]
            culpritInfo["是否请辩护人"] = data["是否请辩护人"]
            culpritInfo["辩护人"] = data["辩护人"]
            culpritInfo["被告人"] = culpritName
            culpritInfo["被告人人数"] = str(data["被告人人数"]) + "-" + str(index + 1)
            culpritInfo["被告人所在市"] = data["被告人所在市"]
            culpritInfo["被告人所在县"] = data["被告人所在县"]
            culpritInfo["被害人伤残等级"] = data["被害人伤残等级"]
            culpritInfo["谅解协议赔偿数额"] = data["谅解协议赔偿数额"]
            culpritInfo["赔偿数额格式化"] = data["赔偿数额格式化"]
            culpritInfo["法官或合议庭民族"] = data["法官或合议庭民族"]
            culpritInfo["审判长姓名"] = data["审判长姓名"]
            culpritInfo["审判长民族"] = data["审判长民族"]

            culpritInfo["被告人民族"] = culpritNationList[index if len(culpritNationList) > index else 0]
            culpritInfo["被告人户籍"] = culpritHomeList[index if len(culpritHomeList) > index else 0]
            culpritInfo["被告人性别"] = culpritGenderList[index if len(culpritGenderList) > index else 0]
            culpritInfo["被告人年龄"] = culpritAgeList[index if len(culpritAgeList) > index else 0]
            culpritInfo["判处结果"] = culpritResultList[index if len(culpritResultList) > index else 0]
            culpritInfo["是否自首"] = culpritIsZiShouList[index if len(culpritIsZiShouList) > index else 0]
            culpritInfo["是否立功"] = culpritIsLiGongList[index if len(culpritIsLiGongList) > index else 0]
            culpritInfo["是否坦白"] = culpritIsTanBaiList[index if len(culpritIsTanBaiList) > index else 0]
            culpritInfo["是否从犯"] = culpritIsCongFanList[index if len(culpritIsCongFanList) > index else 0]
            culpritInfo["是否认罪"] = culpritIsRenZuiList[index if len(culpritIsRenZuiList) > index else 0]
            culpritInfo["是否怀孕"] = culpritIsHuaiYunList[index if len(culpritIsHuaiYunList) > index else 0]
            culpritInfo["是否特别残忍"] = culpritIsCanRenList[index if len(culpritIsCanRenList) > index else 0]
            culpritInfo["是否公开场合行凶"] = culpritIsGongKaiList[index if len(culpritIsGongKaiList) > index else 0]
            culpritInfo["是否使用凶器"] = culpritIsXiongQiList[index if len(culpritIsXiongQiList) > index else 0]
            culpritInfo["是否初犯偶犯"] = culpritIsChuFanList[index if len(culpritIsChuFanList) > index else 0]
            culpritInfo["是否构成累犯"] = culpritIsLeiFanList[index if len(culpritIsLeiFanList) > index else 0]
            culpritInfo["前科是否是八种暴力性犯罪"] = culpritIsBaoLiList[
                index if len(culpritIsBaoLiList) > index else 0][0].replace(" ", "")
            culpritInfo["被害人是否有过错"] = culpritIsGuoCuoList[index if len(culpritIsGuoCuoList) > index else 0]
            culpritInfo["是否积极赔偿被害人损失并取得刑事谅解"] = culpritIsLiangJieList[
                index if len(culpritIsLiangJieList) > index else 0]

            newDataList.append(culpritInfo)
    return newDataList


# 保存新数据到excel
def saveDataToExcel(resultDF, fineName):
    path = pathlib.Path(fineName)
    if path.exists():
        path.unlink()
    resultDF.to_excel(str(path), sheet_name='故意伤害罪', index=False)


# 将原始数据填充格式化
def modifyData():
    global cityMap
    global tibetNameList
    cityMap = prepareTibetCityMap()
    tibetNameList = prepareTibetNameList()
    # print(cityMap)
    # print(tibetNameList)
    # path = pathlib.Path("asset/西藏案件量刑数据(缩略版本).xlsx")
    path = pathlib.Path("../asset/西藏案件量刑数据(完整版本).xlsx")
    originDataFrame = pd.read_excel(str(path), sheet_name="故意伤害罪")  # 读取原始数据
    originDataJsonArray: list = json.loads(originDataFrame.to_json(orient="records", force_ascii=False))  # 转成json格式

    multipleCulpritDataList = calcCulpritNumAndSort(originDataJsonArray)  # 计算被告人人数并根据人数排序
    originDataJsonArray.extend(splitMultipleCulpritData(multipleCulpritDataList))  # 拆分多被告数据为多条

    for row in originDataJsonArray:
        fillCourtCityDistrict(row)  # 处理判决地市县
        fillCaseNo(row)  # 处理案号缩写
        fillLawyer(row)  # 处理辩护人
        fillCulpritHomeInfo(row)  # 处理被告人户籍县市数据
        fillMoneyNum(row)  # 处理赔偿金额
        fillJudgeNameAndNation(row)  # 处理审判长姓名及民族信息
        formatData(row)  # 处理特定数据格式
    # print(originDataJsonArray)
    resultDF = pd.json_normalize(originDataJsonArray)  # 转回dataFrame
    saveDataToExcel(resultDF, "asset/西藏案件量刑数据(修复版本).xlsx")


# 将格式化之后的数据进行编码处理
def codingData():
    global codeDictJsonMap
    path = pathlib.Path("../asset/西藏案件量刑数据(待编码).xlsx")
    codeDictFrame = pd.read_excel(str(path), sheet_name="编码字典")  # 读取编码字典数据
    codeDictJsonMap = json.loads(codeDictFrame.to_json(force_ascii=False))  # 转成json格式
    # print(codeDictJsonMap)

    originDataFrame = pd.read_excel(str(path), sheet_name="故意伤害罪")  # 读取原始数据
    originDataJsonArray: list = json.loads(originDataFrame.to_json(orient="records", force_ascii=False))  # 转成json格式

    for data in originDataJsonArray:  # 判决机关地市
        court_city = data["判决机关地市"]
        for k, v in codeDictJsonMap["判决机关地市"].items():
            if v is not None and v == court_city:
                data["court_city"] = int(k) + 1
                break
    for data in originDataJsonArray:  # 判决机关县区
        court_district = data["判决机关县区"]
        for k, v in codeDictJsonMap["判决机关县区"].items():
            if v is not None and v == court_district:
                data["court_district"] = int(k) + 1
                break
    for data in originDataJsonArray:  # 判决年份
        year = data["判决年份"]
        for k, v in codeDictJsonMap["判决年份"].items():
            if v is not None and v == year:
                data["year"] = int(k) + 1
                break
    for data in originDataJsonArray:  # 辩护人
        lawyer = data["辩护人"]
        for k, v in codeDictJsonMap["辩护人"].items():
            if v is not None and v == lawyer:
                data["lawyer"] = int(k) + 1
                break
    for data in originDataJsonArray:  # 被告人民族
        suspect_nation = data["被告人民族"]
        for k, v in codeDictJsonMap["被告人民族"].items():
            if v is not None and v == suspect_nation:
                data["suspect_nation"] = int(k) + 1
                break
    for data in originDataJsonArray:  # 被告人人数
        suspect_count = data["被告人人数"]
        for k, v in codeDictJsonMap["被告人人数"].items():
            if v is not None and v == suspect_count:
                data["suspect_count"] = int(k) + 1
                break
    for data in originDataJsonArray:  # 被告人户籍地市
        suspect_city = data["被告人户籍地市"]
        for k, v in codeDictJsonMap["被告人户籍地市"].items():
            if v is not None and v == suspect_city:
                data["suspect_city"] = int(k) + 1
                break
    for data in originDataJsonArray:  # 被告人户籍县区
        suspect_district = data["被告人户籍县区"]
        for k, v in codeDictJsonMap["被告人户籍县区"].items():
            if v is not None and v == suspect_district:
                data["suspect_district"] = int(k) + 1
                break
    for data in originDataJsonArray:  # 被告人性别
        gender = data["被告人性别"]
        for k, v in codeDictJsonMap["被告人性别"].items():
            if v is not None and v == gender:
                data["gender"] = int(k) + 1
                break
    for data in originDataJsonArray:  # 被告人年龄
        age = data["被告人年龄"]
        for k, v in codeDictJsonMap["被告人年龄"].items():
            if v is not None and v == age:
                data["age"] = int(k) + 1
                break
    for data in originDataJsonArray:  # 被害人伤残等级
        disability_degree = data["被害人伤残等级"]
        for k, v in codeDictJsonMap["被害人伤残等级"].items():
            if v is not None and v == disability_degree:
                data["disability_degree"] = int(k) + 1
                break
    for data in originDataJsonArray:  # 审判长民族
        justice_nation = data["审判长民族"]
        for k, v in codeDictJsonMap["审判长民族"].items():
            if v is not None and v == justice_nation:
                data["justice_nation"] = int(k) + 1
                break
    for data in originDataJsonArray:  # 是否自首
        is_confess = data["是否自首"]
        for k, v in codeDictJsonMap["是否自首"].items():
            if v is not None and v == is_confess:
                data["is_confess"] = int(k) + 1
                break
    for data in originDataJsonArray:  # 是否立功
        is_meritorious = data["是否立功"]
        for k, v in codeDictJsonMap["是否立功"].items():
            if v is not None and v == is_meritorious:
                data["is_meritorious"] = int(k) + 1
                break
    for data in originDataJsonArray:  # 是否坦白
        is_honest = data["是否坦白"]
        for k, v in codeDictJsonMap["是否坦白"].items():
            if v is not None and v == is_honest:
                data["is_honest"] = int(k) + 1
                break
    for data in originDataJsonArray:  # 是否从犯
        is_accessary = data["是否从犯"]
        for k, v in codeDictJsonMap["是否从犯"].items():
            if v is not None and v == is_accessary:
                data["is_accessary"] = int(k) + 1
                break
    for data in originDataJsonArray:  # 是否认罪
        is_peccavi = data["是否认罪"]
        for k, v in codeDictJsonMap["是否认罪"].items():
            if v is not None and v == is_peccavi:
                data["is_peccavi"] = int(k) + 1
                break
    for data in originDataJsonArray:  # 是否怀孕
        is_pregnancy = data["是否怀孕"]
        for k, v in codeDictJsonMap["是否怀孕"].items():
            if v is not None and v == is_pregnancy:
                data["is_pregnancy"] = int(k) + 1
                break
    for data in originDataJsonArray:  # 是否特别残忍
        is_particularly_cruel = data["是否特别残忍"]
        for k, v in codeDictJsonMap["是否特别残忍"].items():
            if v is not None and v == is_particularly_cruel:
                data["is_particularly_cruel"] = int(k) + 1
                break
    for data in originDataJsonArray:  # 是否公开场合行凶
        is_public = data["是否公开场合行凶"]
        for k, v in codeDictJsonMap["是否公开场合行凶"].items():
            if v is not None and v == is_public:
                data["is_public"] = int(k) + 1
                break
    for data in originDataJsonArray:  # 是否使用凶器
        is_weapon = data["是否使用凶器"]
        for k, v in codeDictJsonMap["是否使用凶器"].items():
            if v is not None and v == is_weapon:
                data["is_weapon"] = int(k) + 1
                break
    for data in originDataJsonArray:  # 是否初犯偶犯
        is_casual_offender = data["是否初犯偶犯"]
        for k, v in codeDictJsonMap["是否初犯偶犯"].items():
            if v is not None and v == is_casual_offender:
                data["is_casual_offender"] = int(k) + 1
                break
    for data in originDataJsonArray:  # 是否构成累犯
        is_recidivism = data["是否构成累犯"]
        for k, v in codeDictJsonMap["是否构成累犯"].items():
            if v is not None and v == is_recidivism:
                data["is_recidivism"] = int(k) + 1
                break
    for data in originDataJsonArray:  # 前科是否是八种暴力性犯罪
        is_violence_record = data["前科是否是八种暴力性犯罪"]
        for k, v in codeDictJsonMap["前科是否是八种暴力性犯罪"].items():
            if v is not None and v == is_violence_record:
                data["is_violence_record"] = int(k) + 1
                break
    for data in originDataJsonArray:  # 被害人是否有过错
        is_victim_fault = data["被害人是否有过错"]
        for k, v in codeDictJsonMap["被害人是否有过错"].items():
            if v is not None and v == is_victim_fault:
                data["is_victim_fault"] = int(k) + 1
                break
    for data in originDataJsonArray:  # 是否积极赔偿被害人损失并取得刑事谅解
        is_compensation = data["是否积极赔偿被害人损失并取得刑事谅解"]
        for k, v in codeDictJsonMap["是否积极赔偿被害人损失并取得刑事谅解"].items():
            if v is not None and v == is_compensation:
                data["is_compensation"] = int(k) + 1
                break

    for data in originDataJsonArray:  # 判处结果
        sentence_result = data["判处结果"]
        for k, v in codeDictJsonMap["判处结果"].items():
            if v is not None and v == sentence_result:
                sentence_result_desc = codeDictJsonMap["判处结果分段"][k]
                # print("当前判处结果：" + sentence_result + " 判处结果分段值为：" + sentence_result_desc)
                for k_code, v_code in codeDictJsonMap["判处结果编码"].items():
                    if v_code is not None and v_code == sentence_result_desc:
                        data["sentence_result"] = int(k_code) + 1
                        # print("当前判处结果分段id为：" + str(int(k_code) + 1))
                        break
                break
    for data in originDataJsonArray:  # 赔偿数额
        compensation_amount = data["赔偿数额"]
        for k, v in codeDictJsonMap["赔偿数额"].items():
            if v is not None and v == compensation_amount:
                compensation_amount_desc = codeDictJsonMap["赔偿数额分段"][k]
                print("当前赔偿数额：" + str(compensation_amount) + " 赔偿数额分段值为：" + str(compensation_amount_desc))
                for k_code, v_code in codeDictJsonMap["赔偿数额编码"].items():
                    if v_code is not None and v_code == compensation_amount_desc:
                        data["compensation_amount"] = int(k_code) + 1
                        print("当前赔偿数额分段id为：" + str(int(k_code) + 1))
                        break
                break

    # 判处结果
    # 判决结果是否过重
    # 赔偿数额

    resultDF = pd.json_normalize(originDataJsonArray)  # 转回dataFrame
    saveDataToExcel(resultDF, "asset/西藏案件量刑数据(编码版本).xlsx")


if __name__ == '__main__':
    # modifyData()
    codingData()
