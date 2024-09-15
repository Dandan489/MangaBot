import requests
import urllib.parse
import re
import time
import asyncio
from datetime import datetime
from bs4 import BeautifulSoup

lastTime = time.time()
DBPath = "animeone" 

async def getAnimeTitle(animeURL: str) -> str:
    url = urllib.parse.unquote(animeURL)
    r = requests.get(url)
    print(f'requested: {url}')
    
    global lastTime
    curTime = time.time()
    diffTime = curTime - lastTime
    if diffTime < 1:
        await asyncio.sleep(1 - diffTime)
    lastTime = time.time()
    
    soup = BeautifulSoup(r.text, 'html.parser')
    titleText = soup.title.string
    ind = titleText.find(' – Anime1.me')
    return titleText[:ind]

async def getUpdateTime(animeURL: str, getURL: bool = False) -> str:
    url = urllib.parse.unquote(animeURL).strip()
    r = requests.get(url)
    print(f'requested: {url}')
    
    global lastTime
    curTime = time.time()
    diffTime = curTime - lastTime
    if diffTime < 1:
        await asyncio.sleep(1 - diffTime)
    lastTime = time.time()
    
    soup = BeautifulSoup(r.text, 'html.parser')
    attr = {"class": "entry-date published updated"}
    updateTime = soup.find_all("time", attrs=attr)
    if(getURL): return updateTime[0].get_text().strip() + f' {animeURL}'
    else: return updateTime[0].get_text().strip()

def printTitle(titleText: str, listing: bool = False) -> str:
    lenn = len(titleText)
    returnText = ''
    ind = titleText.find(' - Anime1')
    return titleText[:ind]

def sliceTitle(listText: str) -> str:
    try:
        end_index = listText.find(' 更新時間')
        return listText[:end_index].strip()
    except Exception:
        return ''

def convertTime(listText: str) -> datetime:
    ind = listText.find("更新時間:")
    date_object = datetime.strptime(listText[ind+6:ind+16], '%Y-%m-%d')
    return date_object

def test_list(username: str) -> bool:
    dbname = f".\\{DBPath}\\{username}.txt"
    try:
        with open(dbname, 'r', encoding="utf-8") as bookList:
            lines = bookList.readlines()
            totalLen = int(lines[0].strip())
            return True
    except Exception:
        reset_anime(username)
        return True
    
async def add_anime(animeURL, username: str) -> str:
    if(test_list(username) == False): return False
    try:
        animeName = await getAnimeTitle(animeURL)
        dbname = f".\\{DBPath}\\{username}.txt"
        with open(dbname, 'r', encoding="utf-8") as bookList:
            lines = bookList.readlines()
            totalLen = int(lines[0].strip())
            lines[0] = str(totalLen+1) + '\n'
            
            for i in range(1, totalLen+1):
                if(lines[i].find(animeName) != -1):
                    return ''
            
            mangaText = f'{animeName} '
            mangaText += f'更新時間: {await getUpdateTime(animeURL, True)}'
            mangaText += '\n'
            addTitle = sliceTitle(mangaText)
            lines.append(mangaText)
        with open(dbname, 'w', encoding="utf-8") as bookList:
            bookList.writelines(lines)
        sort_anime(username)
        return addTitle
    except Exception as e:
        print(e)
        return ''

def list_anime(username: str, start=1, end=99999) -> str:
    if(test_list(username) == False): return 'No user found'
    try:
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
        return returnText
    except Exception as e:
        print(e)
        return 'failed to output the list'

def reset_anime(username: str) -> bool:
    try:
        lines = []
        dbname = f".\\{DBPath}\\{username}.txt"
        with open(dbname, 'w', encoding="utf-8") as bookList:
            bookList.write('0\n')
        return True  
    except Exception:
        return False

def remove_anime(animeName, username: str) -> str:
    if(test_list(username) == False): return False
    try:
        dbname = f".\\{DBPath}\\{username}.txt"
        with open(dbname, 'r', encoding="utf-8") as bookList:
            lines = bookList.readlines()
            totalLen = int(lines[0].strip())
            lines[0] = str(totalLen-1) + '\n'
        
        lineNum = -1
        for i in range(1, totalLen+1):
            if lines[i].find(f'{animeName}') != -1:
                lineNum = i
                
        removeTitle = sliceTitle(lines[lineNum])
        del lines[lineNum]
        with open(dbname, 'w', encoding="utf-8") as bookList:
            bookList.writelines(lines)
        return removeTitle
    except Exception:
        return ''

async def update_anime(username: str) -> str:
    if(test_list(username) == False): return 'Cant find user'
    try:
        returnText = ''
        dbname = f".\\{DBPath}\\{username}.txt"
        with open(dbname, 'r', encoding="utf-8") as bookList:
            lines = bookList.readlines()
            totalLen = int(lines[0].strip())
            
            for i in range(1, totalLen+1):
                title = sliceTitle(lines[i])       
                urlInd = lines[i].find('https:')
                url = lines[i][urlInd:]
                newTimeText = await getUpdateTime(url, False)
                newTime = datetime.strptime(newTimeText, '%Y-%m-%d')
                oldTime = convertTime(lines[i])
                
                if(newTime > oldTime):
                    returnText += title
                    returnText += ' updated!\n'
                    returnText += f'{url}'
                    mangaText = f'{title} 更新時間: {newTimeText} {url}'
                    lines[i] = mangaText
                
        with open(dbname, 'w', encoding="utf-8") as bookList:
            bookList.writelines(lines)
        sort_anime(username)
        print('update completed!')
        return returnText
    except Exception as e:
        print(e)
        return ''

def sort_anime(username: str) -> str:
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
        return 'anime list sorted'
    except Exception as e:
        print(e)
        return 'Failed to sort anime'

async def main() -> None:
    pass
    # print(await add_anime('12345', 'dandan0922'))
    # print(await add_anime('45678', 'dandan0922'))

if __name__ == '__main__':
    asyncio.run(main())
