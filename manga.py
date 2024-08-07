import requests
import opencc
import asyncio
import time
from datetime import datetime
from bs4 import BeautifulSoup

lastTime = time.time()
DBPath = "manhuagui" 

def printTitle(titleText: str, listing: bool = False) -> str:
    converter = opencc.OpenCC('s2t')
    lenn = len(titleText)
    returnText = ''
    titleText = converter.convert(titleText)
    
    if not listing: returnText += '標題: '
    for i in range(lenn-2):
        if(titleText[i:i+2] == '漫畫'):
            if not listing: returnText += '\n'
            return returnText
        returnText += titleText[i]
    return returnText

def sliceTitle(listText: str) -> str:
    try:
        start_index = listText.find(')') + 1
        end_index = listText.find('更')
        return listText[start_index:end_index].strip()
    except Exception:
        return ''

def convertTime(listText: str) -> datetime:
    lenn = len(listText)
    for i in range(lenn-5):
        if(listText[i:i+5] == '更新時間:'):
            date_object = datetime.strptime(listText[i+6:i+16], '%Y-%m-%d')
            return date_object

def test_list(username: str) -> bool:
    dbname = f".\\{DBPath}\\{username}.txt"
    try:
        with open(dbname, 'r', encoding="utf-8") as bookList:
            lines = bookList.readlines()
            totalLen = int(lines[0].strip())
            return True
    except Exception:
        reset_manga(username)
        return True
    
async def add_manga(numLink, username: str) -> str:
    if(test_list(username) == False): return False
    try:
        numLink = str(numLink)
        dbname = f".\\{DBPath}\\{username}.txt"
        with open(dbname, 'r', encoding="utf-8") as bookList:
            lines = bookList.readlines()
            totalLen = int(lines[0].strip())
            lines[0] = str(totalLen+1) + '\n'
            
            for i in range(1, totalLen+1):
                if(lines[i][1:6] == numLink):
                    return ''
            
            mangaText = f'({numLink}) '
            mangaText += await find_manga(numLink, True)
            mangaText += f' https://m.manhuagui.com/comic/{numLink}'
            mangaText += '\n'
            addTitle = sliceTitle(mangaText)
            lines.append(mangaText)
        with open(dbname, 'w', encoding="utf-8") as bookList:
            bookList.writelines(lines)
        sort_manga(username)
        return addTitle
    except Exception as e:
        print(e)
        return ''

def list_manga(username: str, start=1, end=99999) -> str:
    if(test_list(username) == False): return 'No user found'
    returnText = ''
    dbname = f".\\{DBPath}\\{username}.txt"
    with open(dbname, 'r', encoding="utf-8") as bookList:
        lines = bookList.readlines()
        totalLen = int(lines[0].strip())
        if(totalLen == 0):
            return 'The list is empty'
        
        for i in range(max(1,start), min(totalLen+1, end)):
            ind = lines[i].find('https')
            returnText += (lines[i][:ind] + '\n' + lines[i][ind:])
    if(len(returnText)>=2000): return 'The list is too long, try a smaller range'
    return returnText

async def find_manga(numLink, listing: bool = False) -> str:
    converter = opencc.OpenCC('s2t')
    baseUrl = 'https://m.manhuagui.com/comic/'
    url = baseUrl + str(numLink)
    r = requests.get(url)
    print(f'requested: {url}')
    
    global lastTime
    curTime = time.time()
    diffTime = curTime - lastTime
    if diffTime < 10:
        await asyncio.sleep(10 - diffTime)
    lastTime = time.time()
    
    soup = BeautifulSoup(r.text, 'html.parser')
    
    returnText = ''
    titleTag = soup.title
    aTags = soup.find_all('dd')
    if listing:
        returnText += printTitle(titleTag.get_text(), True)
        returnText += f' 更新時間: {converter.convert(aTags[1].get_text())}'
        return returnText
    else:
        returnText += printTitle(titleTag.get_text())
    
    returnText += f'最新集數: {converter.convert(aTags[0].get_text())}\n'
    returnText += f'更新時間: {converter.convert(aTags[1].get_text())}\n'
    returnText += f'漫畫連結: https://m.manhuagui.com/comic/{numLink}'
    
    return returnText

def reset_manga(username: str) -> bool:
    try:
        lines = []
        dbname = f".\\{DBPath}\\{username}.txt"
        with open(dbname, 'w', encoding="utf-8") as bookList:
            bookList.write('0\n')
        return True  
    except Exception:
        return False

def remove_manga(numLink, username: str) -> str:
    if(test_list(username) == False): return False
    try:
        numLink = int(numLink)
        dbname = f".\\{DBPath}\\{username}.txt"
        with open(dbname, 'r', encoding="utf-8") as bookList:
            lines = bookList.readlines()
            totalLen = int(lines[0].strip())
            lines[0] = str(totalLen-1) + '\n'
        
        lineNum = -1
        for i in range(1, totalLen+1):
            if lines[i].find(f'{numLink}') != -1:
                lineNum = i
                
        removeTitle = sliceTitle(lines[lineNum])
        del lines[lineNum]
        with open(dbname, 'w', encoding="utf-8") as bookList:
            bookList.writelines(lines)
        return removeTitle
    except Exception:
        return ''

async def update_manga(username: str):
    if(test_list(username) == False): return 'Cant find user'
    try:
        returnText = ''
        dbname = f".\\{DBPath}\\{username}.txt"
        with open(dbname, 'r', encoding="utf-8") as bookList:
            lines = bookList.readlines()
            totalLen = int(lines[0].strip())
            for i in range(1, totalLen+1):
                newText = await find_manga(lines[i][1:6], True)
                newTime = convertTime(newText)
                oldTime = convertTime(lines[i])
                if(newTime > oldTime):
                    returnText += sliceTitle(lines[i])
                    returnText += ' updated!\n'
                    returnText += f' https://m.manhuagui.com/comic/{lines[i][1:6]}\n'
                    mangaText = f'({lines[i][1:6]}) ' + newText + f' https://m.manhuagui.com/comic/{lines[i][1:6]}' + '\n'
                    lines[i] = mangaText
        with open(dbname, 'w', encoding="utf-8") as bookList:
            bookList.writelines(lines)
        sort_manga(username)
        print('update completed!')
        return returnText
    except Exception as e:
        print(e)
        return ''

def sort_manga(username: str) -> str:
    if(test_list(username) == False): return 'Cant find user'
    try:
        dbname = f".\\{DBPath}\\{username}.txt"
        with open(dbname, 'r', encoding="utf-8") as bookList:
            lines = bookList.readlines()
            line1 = [lines[0],]
            lineRest = lines[1:]
            lineRest = sorted(lineRest, key=lambda x: convertTime(x), reverse=True)
        with open(dbname, 'w', encoding="utf-8") as bookList:
            lines = line1 + lineRest
            bookList.writelines(lines)
        return 'manga list sorted'
    except Exception as e:
        print(e)
        return 'Failed to sort manga'

def main() -> None:
    print(update_manga('dandan0922'))

if __name__ == '__main__':
    main()
