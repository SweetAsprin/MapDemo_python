import pathlib
from bs4 import BeautifulSoup
import chardet
import re


def parseHtml(path):
    subTitleBefore = ""  # 副标题1
    title = ""  # 主标题
    subTitleAfter = ""  # 副标题2
    author = ""  # 作者
    year = ""  # 年
    month = ""  # 月
    day = ""  # 日
    pageIndex = ""  # 版面序号
    pageName = ""  # 版面名称
    content = ""  # 正文内容

    #下面这段代码是先预读文件检测编码
    # soup = ""
    # with open(path, 'rb') as f:
    #     detect_result = chardet.detect(f.read(200))
    #     encoding = detect_result['encoding']
    #     print('编码检测结果: {}，概率: {}'.format(encoding, detect_result['confidence']))
    #     soup = BeautifulSoup(open(path), 'lxml', from_encoding=encoding)

    soup = BeautifulSoup(open(path, 'rb'), 'lxml')
    divList = list(soup.find_all('div'))
    for div in divList:
        if div.attrs is not None:
            if "class" in div.attrs:
                firstClass = div["class"][0]
                if firstClass == "title":  # 解析标题
                    title = div.text
                if firstClass == "subtitle":  # 解析副标题
                    if title == "":
                        subTitleBefore = div.text
                    else:
                        subTitleAfter = div.text
                if firstClass == "author":  # 解析作者
                    author = str(div.text).replace("【作者：", "").replace("】", "")
                if firstClass == "sha_left":
                    for child in list(div.children):
                        if child.name == "span":
                            spanContent = child.text
                            if str(spanContent).__contains__("年") and str(spanContent).__contains__("月") and str(spanContent).__contains__(
                                    "日"):
                                date = re.split("年|月|日", spanContent)
                                if len(date) >= 3:
                                    year = date[0]
                                    month = date[1]
                                    day = date[2]
                            elif str(spanContent).isnumeric():
                                pageIndex = spanContent
                            else:
                                pageName = spanContent
            if "id" in div.attrs and div["id"] == "FontZoom":  # 解析正文
                content = str(div.text)
                content = content.strip()
    return subTitleBefore, title, subTitleAfter, author, year, month, day, pageIndex, pageName, content


def printParseResult(subTitleBefore, title, subTitleAfter, author, year, month, day, pageIndex, pageName, content):
    if not subTitleBefore == "":
        print("前副标题:", subTitleBefore)
    if not title == "":
        print("文章标题:", title)
    if not subTitleAfter == "":
        print("后副标题:", subTitleAfter)
    if not author == "":
        print("文章作者:", author)
    if not year == "" and not month == "" and not day == "":
        print("报纸期数:", str(year) + "年" + month + "月" + day + "日")
    if not pageIndex == "":
        print("报纸版面:", "第" + pageIndex + "版")
    if not pageName == "":
        print("版面名称:", pageName)
    print("正文:", content)


def createTxtFile(htmlFile, txtFileDir, renameHtmlFileDir, subTitleBefore, title, subTitleAfter, author, year, month, day, pageIndex, pageName,
                  content):
    dirPath = pathlib.Path(txtFileDir)
    if not dirPath.exists():
        dirPath.mkdir()
    strDate = year + "-" \
              + (month if (int(month) >= 10) else ("0" + month)) + "-" \
              + (day if (int(day) >= 10) else ("0" + day))
    strPage = "第" + pageIndex + "版" \
              + (("(" + pageName + ")") if not pageName == "" else "")
    strTitle = ((subTitleBefore + "——") if (not subTitleBefore == "" and len(subTitleBefore) < 50) else "") \
               + title \
               + (("——" + subTitleAfter) if (not subTitleAfter == "" and len(subTitleAfter) < 50) else "")
    txtFileName = strDate + "-" + strPage + "-" + strTitle

    renameHtmlFilePath = pathlib.Path(str(renameHtmlFileDir + "/" + txtFileName + ".html"))
    if renameHtmlFilePath.exists():
        print("文件： " + txtFileName + ".html" + " 已存在！删除后重新生成！")
        renameHtmlFilePath.unlink()
    renameHtmlFilePath.write_bytes(htmlFile.read_bytes())

    txtFilePath = pathlib.Path(str(txtFileDir + "/" + txtFileName + ".txt"))
    if txtFilePath.exists():
        print("文件： " + txtFileName + ".txt" + " 已存在！删除后重新生成！")
        txtFilePath.unlink()
    else:
        # print("创建文件：" + txtFileName)
        with open(str(txtFilePath), "a") as f:
            if not subTitleBefore == "":
                f.write(subTitleBefore)
                f.write("\n")
            f.write(title)
            f.write("\n")
            if not subTitleAfter == "":
                f.write(subTitleAfter)
                f.write("\n")
            f.write("时间：" + strDate + " " + strPage)
            f.write("\n")
            f.write("作者：" + author)
            f.write("\n")
            f.write(content)
            f.close()


if __name__ == '__main__':
    sourceHtmlFileDir = "/Users/asprinchang/Downloads/人民日报资源/原始网页"
    renameHtmlFileDir = "/Users/asprinchang/Downloads/人民日报资源/重命名网页"
    txtFileDir = "/Users/asprinchang/Downloads/人民日报资源/txt版本"
    sourceHtmlFileDirPath = pathlib.Path(sourceHtmlFileDir)
    renameHtmlFileDirPath = pathlib.Path(renameHtmlFileDir)
    txtFileDirPath = pathlib.Path(txtFileDir)
    if not renameHtmlFileDirPath.exists():
        renameHtmlFileDirPath.mkdir()
    if not txtFileDirPath.exists():
        txtFileDirPath.mkdir()
    for file in sourceHtmlFileDirPath.iterdir():
        if file.name.startswith("."):
            continue
        # print("开始处理：" + str(file.name))
        subTitleBefore, title, subTitleAfter, author, year, month, day, pageIndex, pageName, content = parseHtml(str(file))  # 解析网页内容
        # # printParseResult(subTitleBefore, title, subTitleAfter, author, year, month, day, pageIndex, pageName, content)
        createTxtFile(file, txtFileDir, renameHtmlFileDir, subTitleBefore, title, subTitleAfter, author, year, month, day, pageIndex, pageName,
                      content)  # 创建对应txt文件
