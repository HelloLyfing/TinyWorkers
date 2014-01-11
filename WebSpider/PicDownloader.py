# coding:utf-8

import threading
import urllib
import logging
import time
import os


class PicDownloader(threading.Thread):

    runFlag = 1

    def __init__(self, queue, pathDict):
        threading.Thread.__init__(self)
        self.queue = queue
        self.downloadPath = pathDict['picPath']

    def stop(self):
        pass

    def downloadPic(self, picDict):
        picURL = picDict['picURL']
        picPath = os.path.join(self.downloadPath, (picDict['id']+'.jpg'))
        if not os.path.exists(picPath):
            try:
                urllib.urlretrieve(picURL, picPath)
                logging.info('download pic [%s] successfully' %picPath)
            except:
                logging.warn('retrieving pic [%s] failed' %picPath)

    def run(self):
        while self.__class__.runFlag > 0:
            while not self.queue.empty():
                picDict = self.queue.get()
                self.downloadPic(picDict)
            time.sleep(1)
        logging.info('PicDownloader thread : %s quits' %threading.current_thread().getName())
