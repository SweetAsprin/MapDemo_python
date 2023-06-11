import pandas as pd
import json


def readExcel(path):
    sheetList = pd.read_excel(path, sheet_name=None)
    for sheetName in sheetList.keys():
        print("\n当前表名：" + sheetName)

        df = sheetList.get(sheetName)

        totalData = {}
        lastCo1 = None
        lastCo2 = None
        dataKeyList = list(df.to_dict().keys())  # 记录key的顺序
        col1RowMap = {}
        col2RowMap = {}
        co2ValueList = []  # 记录动态key的值的顺序
        resultArray = []

        dataJson = json.loads(df.to_json(force_ascii=False))

        for row in dataJson[dataKeyList[0]]:  # 遍历因变量值
            if dataJson[dataKeyList[0]][row] is not None:
                lastCo1 = dataJson[dataKeyList[0]][row]
                col1RowMap[lastCo1] = []
                col1RowMap[lastCo1].append(row)
            else:
                col1RowMap[lastCo1].append(row)
        # print(col1RowMap)
        for row in dataJson[dataKeyList[1]]:  # 遍历动态变量值
            if dataJson[dataKeyList[1]][row] is not None:
                lastCo2 = dataJson[dataKeyList[1]][row]
                if lastCo2 not in co2ValueList:
                    co2ValueList.append(lastCo2)
                if col2RowMap.get(lastCo2) is None:
                    col2RowMap[lastCo2] = []
                col2RowMap[lastCo2].append(row)
            else:
                col2RowMap[lastCo2].append(row)

        for row in range(len(dataJson[dataKeyList[0]])):
            co1 = dataJson[dataKeyList[0]][str(row)]
            co2 = dataJson[dataKeyList[1]][str(row)]
            co3 = dataJson[dataKeyList[2]][str(row)]
            co4 = dataJson[dataKeyList[3]][str(row)]
            co5 = dataJson[dataKeyList[4]][str(row)]
            co6 = dataJson[dataKeyList[5]][str(row)]
            # print("row(" + str(row) + ") :" + "co1 = " + str(co1) + " co2 = " + str(co2) + " co3 = " + str(
            #     co3) + " co4 = " + str(co4) + " co5 = " + str(co5) + " co6 = " + str(co6))
            if co1 is not None:

                if len(resultArray) > 0:
                    print(str(lastCo1) + " 有差异性结果：" + str(resultArray))
                resultArray.clear()

                lastCo1 = co1
                if totalData.get(lastCo1) is None:
                    totalData[lastCo1] = {}
            if co2 is not None:
                lastCo2 = co2
                if totalData[lastCo1].get(lastCo2) is None:
                    totalData[lastCo1][lastCo2] = {}
            co2_index = co2ValueList.index(lastCo2) + 1
            co3_index = co2ValueList.index(co3) + 1
            totalData[lastCo1][lastCo2][str(co3)] = (
                {"co2": lastCo2, "co2_index": co2_index,
                 "co3": co3, "co3_index": co3_index,
                 "co4": co4, "co5": co5, "co6": co6})
            if co6 < 0.05:
                if co4 > 0:
                    result = str(co2_index) + ">" + str(co3_index)
                else:
                    result = str(co3_index) + ">" + str(co2_index)
                if result not in resultArray:
                    resultArray.append(result)
                # print(result)
        if len(resultArray) > 0:
            print(str(lastCo1) + " 有差异性结果：" + str(resultArray))
        resultArray.clear()


if __name__ == '__main__':
    readExcel("../asset/spss源数据.xlsx")
