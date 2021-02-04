import requests
import sys
import re
import os
import json

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36'}


def getVideoUrl(shareurl):
    response = requests.get(shareurl, headers=headers, allow_redirects=False)
    id = re.findall(r'./share/video/(.*)/.?region=', response.headers['location'])[0]

    url = 'https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids=' + id
    print(url)

    videoUrlResponse = requests.get(url, headers=headers, allow_redirects=False)
    videojson = json.loads(videoUrlResponse.text)
    name = videojson["item_list"][0]["desc"].replace('"', '').replace('“', '').replace('”', '')
    video_url = videojson["item_list"][0]["video"]['play_addr']['url_list'][0]
    author = videojson["item_list"][0]["author"]['nickname']
    print(author)
    print(name)
    print(video_url)
    douyinvideo(video_url, name, author)


def douyinvideo(url, name, author):
    r = requests.get(url, headers=headers).content

    video_path = 'E:\\Douyin\\%s' % (author)
    if not os.path.exists(video_path):
        os.makedirs(video_path)

    video_file = r'%s\%s.mp4' % (video_path, name)
    print(video_file)
    with open(video_file, "wb+") as fw:
        fw.write(r)


def main(argv):
    if (len(argv) < 2):
        # url = 'https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids=6921289745691610375'
        # url = 'https://aweme.snssdk.com/aweme/v1/playwm/?video_id=v0300f8f0000c06lo7pcdlhmtt9ikd50&amp;ratio=720p&amp;line=0'
        url = 'https://v.douyin.com/J3a3g5V/'
    else:
        print("argv:" + argv[1])
        url = argv[1]
    getVideoUrl(url)


if __name__ == '__main__':
    main(sys.argv)
