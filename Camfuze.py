import threading
import time
import requests
import sys
import os
import queue
import re
import json
from hyper.contrib import HTTP20Adapter

'''
快速一键生成 Python 爬虫请求头
https://curl.trillworks.com/
1，Chrome 打开开发者选项（ f12 ）---> network 选项卡 ---> 刷新页面,获取请求 ---> 找到页面信息对应的请求 (通过请求的名称、后缀和 response 内容来判断)
2，右键，copy ---> copy as cURL (bash)，注意不是【copy as cURL (cmd)】
3，打开网站，https://curl.trillworks.com/，粘贴 cURL (bash) 到左边 curl command，右边会自动出 Python 代码
'''

headers = {
    'Origin': 'https://cn.camfuze.com',
    'Referer': 'https://cn.camfuze.com/xtriciafox',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'}

tools_headers = {
    ':authority': 'cn.camfuze.com',
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'x-requested-with': 'XMLHttpRequest',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://cn.camfuze.com',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'accept-language': 'zh-CN,zh;q=0.9',
}

tsUrls = queue.Queue()
downUrlEnd = False
test = 0


class downTsUrlThread(threading.Thread):

    def __init__(self, m3u8Url):
        threading.Thread.__init__(self)
        self.m3u8Url = m3u8Url
        self.tsUrlsPool = []
        self.down = True
        self.lastDownTime = time.time()

    def run(self):
        global downUrlEnd
        while self.down:
            try:
                if time.time() - self.lastDownTime > 120:
                    if self.offline():
                        self.down = False
                        downUrlEnd = True
                        print('---------------downTsUrlThread downUrlEnd-------------')
                        break
                    else:
                        self.lastDownTime = time.time()
                m3u8Str = requests.get(self.m3u8Url, headers=headers, timeout=10).text
                # print(m3u8Str)
                if m3u8Str.startswith('#EXTM3U'):
                    m3u8Lines = m3u8Str.split('\n')
                    for tsUrl in m3u8Lines:
                        if (tsUrl != ''and not tsUrl.startswith('#') and tsUrl.endswith('.ts') and tsUrl not in self.tsUrlsPool):
                            print(time.strftime("%H:%M:%S", time.localtime()) + " getM3u8: " + tsUrl)
                            tsUrls.put(tsUrl)
                            self.tsUrlsPool.append(tsUrl)
                            self.lastDownTime = time.time()
                time.sleep(3)
            except Exception as e:
                print("downTsUrlThread  Exception:" + str(e))

    def offline(self):
        name = re.findall(r'./hls/stream_(.*)/public/stream', self.m3u8Url)[0]
        url = 'https://cn.camfuze.com/profile/' + name
        try:
            response = requests.get(url, headers=headers)
            if '离线' in response.text and 'badge_offline' in response.text:
                print(url + "离线")
                return True
        except Exception as e:
            print('offline Exception:' + str(e))
        return False


class downTsThread(threading.Thread):

    def __init__(self, m3u8Url):
        threading.Thread.__init__(self)

        curTime = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        name = m3u8Url.split('/')[len(m3u8Url.split('/')) - 2]
        path = "E:/CamFuze/new/" + name + "/"

        if not os.path.exists(path):
            os.makedirs(path)

        self.filePath = path + curTime + ".mp4"
        self.baseUrl = m3u8Url.rstrip('chunks.m3u8')
        self.down = True
        self.lastDownTime = time.time()

        print("DownLoad file:" + self.filePath)

    def run(self) -> None:
        self.writeTs()
      
    def writeTs(self, reurl=None):
        print('writeTs')
        global downUrlEnd
        global test
        with open(self.filePath, 'wb+') as f:
            self.reopen = False
            while self.down and not self.reopen:
                if time.time() - self.lastDownTime > 120 and downUrlEnd:
                    self.down = False
                    break
                if not tsUrls.empty() or reurl is not None:
                    if reurl is not None:
                        tsUrl = reurl
                        reurl = None
                    else:
                        tsUrl = tsUrls.get()
                    ts = self.downLoadTs(self.baseUrl + tsUrl)
                    try:
                        if test == 1:
                            ts = 'd'
                        test = test + 1
                        f.write(ts)
                    except Exception as e:
                        self.reopen = True
                        print("downTsThread write Exception:" + str(e))
                else:
                    time.sleep(3)
        if self.reopen:
            self.writeTs(tsUrl)

    def downLoadTs(self, url):
        try:
            print(time.strftime("%H:%M:%S", time.localtime()) + " down ts : \n       " + url)
            ts = requests.get(url, headers=headers, timeout=10).content
            self.lastDownTime = time.time()
            return ts
        except Exception as e:
            print("downTsThread  Exception:" + str(e))
            return downTsThread(url)


def download(url):
    print('doanload m3u8url: %s' % (url))
    downTsUrl = downTsUrlThread(url)
    downTsUrl.start()

    downTs = downTsThread(url)
    downTs.start()


def getplaylist(playlist, videoServerUrl, name):
    print('playlist url ' + playlist)
    m3u8Str = requests.get(playlist, headers=headers, timeout=10).text
    print(m3u8Str)
    if m3u8Str.startswith('#EXTM3U'):
        m3u8Lines = m3u8Str.split('\n')
        m3u8List = []
        for url in m3u8Lines:
            if url != ''and not url.startswith('#') and url.endswith('.m3u8'):
                m3u8List.append(url)

        m3u8 = m3u8List[1] if len(m3u8List) > 1 else m3u8List[0]
        m3u8Url = 'https:%s/hls/stream_%s/%s' % (videoServerUrl, name, m3u8)
        download(m3u8Url)
    else:
        print('getplaylist none')


def init(url):
    print('start down ' + url)
    name = url.lstrip('https://cn.camfuze.com/')
    data = [
        ('method', 'getRoomData'),
        ('args[]', name),
        ('args[]', 'false'),
        ('_csrf_token', 'dfc58a923c64b819e4cdaba1656c195e')]

    params = (
        ('x-country', 'cn'),
        ('res', '763196?%d' % (round(time.time() * 1000))))

    sessions = requests.session()
    sessions.mount('https://cn.camfuze.com/', HTTP20Adapter())
    html = sessions.post(url='https://cn.camfuze.com/tools/amf.php', headers=tools_headers, data=data, params=params, timeout=30).text
    response = json.loads(html)
    status = response['status']
    if status == 'success':
        videoServerUrl = response['localData']['videoServerUrl']
        playlist = 'https:%s/hls/stream_%s/playlist.m3u8' % (videoServerUrl, name)
        getplaylist(playlist, videoServerUrl, name)
    else:
        print('amf error')


def main(argv):
    if (len(argv) < 2):
        url = 'https://cn.camfuze.com/perfectt33n'
        # 'https://cn.camfuze.com/Evocative1'
        # sys.exit(1)
    else:
        print("argv:" + argv[1])
        url = argv[1]
    init(url)


if __name__ == '__main__':
    main(sys.argv)
