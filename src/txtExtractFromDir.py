import shutil
from pathlib import Path
import string
from typing import List


def extractSpecFile(sourcePath: Path, targetPath: Path, fileSuffixNameList: List[string]):
    if sourcePath.is_dir():
        for subPath in sourcePath.iterdir():
            extractSpecFile(subPath, targetPath, fileSuffixNameList)
    elif sourcePath.is_file():
        if sourcePath.suffix in fileSuffixNameList:
            copyFile(sourcePath, targetPath)
        else:
            wrongFileTargetPath = targetPath.joinpath("wrongFile")
            copyFile(sourcePath, wrongFileTargetPath)


def copyFile(sourcePath, targetPath):
    if not targetPath.exists():
        targetPath.mkdir(parents=True)
    shutil.copy(str(sourcePath.absolute()), str(targetPath.absolute()))
    print("将文件 " + str(sourcePath.absolute()) + " 复制到 " + str(targetPath.absolute()))


if __name__ == '__main__':
    extractSpecFile(Path("/Users/asprinchang/Downloads/testSrc"), Path("/Users/asprinchang/Downloads/testTar"), [".a", ".c", ".e", ".g"])
