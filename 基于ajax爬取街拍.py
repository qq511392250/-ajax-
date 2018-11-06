import os
from _md5 import md5
from multiprocessing.pool import Pool
from urllib.parse import urlencode

import pymongo
import requests
import json

from config import *

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]



def get_one_page(offset):
    parse ={
        'offset': offset,
        'format': 'json',
        'keyword': '街拍',
        'autoload': 'true',
        'count': '20',
        'cur_tab': '1',
        'from': 'search_tab'

    }
    headers = {'User-Agent' :'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'}
    url = 'https://www.toutiao.com/search_content/?'+urlencode(parse)
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
    except requests.ConnectionError:
        return None

def get_images(json):
    if json.get('data'):
        for item in json.get('data'):
            title = item.get('title')
            images = item.get('image_list',[])
            for image in images:
                yield {
                    'image':'http:'+image.get('url'),
                    'title':title
                }

def save_image(item):
    if not os.path.exists(item.get('title')):
        os.mkdir(item.get('title'))
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'}
        response = requests.get(item.get('image'),headers=headers)
        if response.status_code ==200:
            file_path = '{0}/{1}.{2}'.format(item.get('title'),md5(response.content).hexdigest(),'jpg')
            if not os.path.exists(file_path):
                with open(file_path,'wb')as f:
                    f.write(response.content)
            else:
                print('Already Download',file_path)
    except requests.ConnectionError:
        print('Fail to save Image')

def save_to_mongo(item):
    if db[MONGO_TABLE].insert(item):
        print('存储到mongoDB成功',item)
        return True
    return False

def main(offset):
    json = get_one_page(offset)
    for item in get_images(json):
        print(item)
        save_image(item)
        save_to_mongo(item)

GROUP_START = 1
GROUP_END = 2

if __name__=='__main__':
    pool = Pool()
    groups = ([x*20 for x in range(GROUP_START,GROUP_END+1)])
    pool.map(main,groups)
    pool.close()
    pool.join()




