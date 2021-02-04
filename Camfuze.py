import threading
import time
import requests
import sys
import os
import queue
import re

headers = {
    'Origin': 'https://cn.camfuze.com',
    'Referer': 'https://cn.camfuze.com/xtriciafox',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'}

tsUrls = queue.Queue()
downUrlEnd = False


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
        global downUrlEnd
        with open(self.filePath, 'wb+') as f:
            while self.down:
                if time.time() - self.lastDownTime > 120 and downUrlEnd:
                    self.down = False
                    break
                if not tsUrls.empty():
                    tsUrl = tsUrls.get()
                    ts = self.downLoadTs(self.baseUrl + tsUrl)
                    f.write(ts)
                else:
                    time.sleep(3)

    def downLoadTs(self, url):
        try:
            print(time.strftime("%H:%M:%S", time.localtime()) + " down ts : \n       " + url)
            ts = requests.get(url, headers=headers, timeout=10).content
            self.lastDownTime = time.time()
            return ts
        except Exception as e:
            print("downTsThread  Exception:" + str(e))
            return downTsThread(url)


def init(url):
    downTsUrl = downTsUrlThread(url)
    downTsUrl.start()

    downTs = downTsThread(url)
    downTs.start()


def main(argv):
    if (len(argv) < 2):
        chunks_url = 'https://ded6477-edge62-rn.bcvcdn.com/hls/stream_Evocative1/public/stream_Evocative1_240/chunks.m3u8'
        # 'https://cn.camfuze.com/Evocative1'
        # sys.exit(1)
    else:
        print("argv:" + argv[1])
        chunks_url = argv[1]
    init(chunks_url)


if __name__ == '__main__':
    main(sys.argv)
