# coding:utf-8

import os
import re
import time
import urllib2
import logging
import threading
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup as bsoup

lock = threading.Lock()


def replaceHellWord(text):

    m = re.compile(r'[\x0c\x00\x000a\x000d\x0020\xD7FF\xE000\xFFFD]')
    text = m.sub('', text)
    return text

class QiubaiReader(threading.Thread):
    """
    糗事百科内容的消费者，也是糗事百科文章图片的生产者
    消费者：从 pageQueue 里读取一个页面URL，解析该页面所有糗百文章，并将这些文章存储到xml文件中；
    生产者：在解析页面时，如果某篇文章附带图片，则把该图片的URL放入 picQueue ,等待图片类的消费者来处理.
    """
    argsDict = {
        'pageEncoding'  : 'utf-8',                                 #糗百html的编码格式
        'dadClassAttr'  : 'block untagged mb15 bs2',               #某条糗百整个大<div />块的class属性
        'contClassAttr' : 'content',                               #某条糗百的正文所在<div />块的class属性
        'picClassAttr'  : 'thumb',                                 #包含图片的<div />块的class属性
        'voteClassAttr' : 'bar',                                   #包含投票数的<div />块的class属性
        'idLinePreStr'  : 'qiushi_tag_',                           #包含糗百ID的那一行的id号前的前缀，例如：'qiushi_tag_55611097'
        'validCountNum' : 2000,
    }

    runFlag = 1

    def __init__(self, pageQueue, picQueue, pathDict):
        threading.Thread.__init__(self)
        self.pageQueue = pageQueue
        self.picQueue = picQueue
        self.dataPath = pathDict['dataPath']
        self.xmlName = pathDict['xmlName']

    def stop(self):
        pass

    def fetchContent(self, pageUrl):
        """
        每一条糗百，我们需要取出其中的三条信息：
        1. 该条糗百的ID
        2. 该条糗百的正文
        3. 该条糗百的图片链接(可能为空，非空则等待下载)

        爬取糗百的步骤是：
        1. 获得该条糗百的整个大<div />块，我们声明 div_dad 变量代表这个大<div />块
        2. 通过查找当前投票数的<div />相关值来判断是否继续，如果投票数大于5000，则继续
        3. 在大<div />块的首行，截取该条糗百的文章ID号（每条糗百都是一篇文章，通过文章ID可以获取文章和图片的链接）
        4. 在大div块中，找出带有糗百正文的<div />块
        5. 将上面提到的三条信息写入xml文件
        """
        pageCont = urllib2.urlopen(pageUrl).read().decode(self.argsDict['pageEncoding'])
        soup = bsoup(pageCont)
        divDadList = soup.find_all('div', attrs={'class': self.argsDict['dadClassAttr']})
        qiuBaiList = []
        picDictList = []
        upCount = 0                                         #upCount, 点赞的人数
        qiuID = ''
        picURL = ''

        for divDad in divDadList:
            #get 点赞数
            divVote = divDad.find('div', attrs={'class':self.argsDict['voteClassAttr']})
            upCount = divVote.a.get_text()
            try:
                upCount = int(upCount)
                if upCount < self.argsDict['validCountNum']: continue
            except ValueError:
                logging.warning('get upCount failed, upCount:%s' %upCount)

            #get qiuBai ID
            idLine = divDad.attrs['id']
            qiuID = idLine.replace(self.argsDict['idLinePreStr'], '')   #qiuID is a str, considering that xml file attribute cannot be int type

            #get qiuBai Text
            divContent = divDad.find('div', attrs={'class':self.argsDict['contClassAttr']})
            qiuBaiText = divContent.get_text()

            #get qiuBai Pic
            divPic = divDad.find('div', attrs={'class':self.argsDict['picClassAttr']})
            if divPic:
                picURL = divPic.a.img['src']
                picDictList.append({'id':qiuID, 'picURL':picURL})
            if qiuID != '':
                qiuBai = {
                    'id':       qiuID,
                    'content':  replaceHellWord(qiuBaiText),
                    'picURL':   picURL,
                }
                logging.info('get new qiuBai, id:%s' %qiuBai['id'])
                qiuBaiList.append(qiuBai)

        return qiuBaiList, picDictList
    
    def writeContent(self, list):
        """
        将list中包含的糗百文章格式化并一次性插入到xml文件中
        list中包含有某个页面的所有糗百文章（一般是20条）
        list结构为：
        [
            {   'id':       qiuID1,
                'content':  qiuBaiText,
                'picURL':   picURL },
            {   'id':       qiuID2,
                'content':  qiuBaiText,
                'picURL':   picURL },
            ...
        ]
        """
        xmlPath = os.path.join(self.dataPath, self.xmlName)
        if lock.acquire():
            tree = None
            root = None
            logging.info('ready to append new thing in %s' %threading.current_thread().getName())
            tree = ET.parse(xmlPath)
            root = tree.getroot()
            for dict in list:
                qiubai = ET.SubElement(root, 'qiubai')
                qiubai.set('id', dict['id'])
                qiubai.set('picURL', dict['picURL'])
                qiubai.text = dict['content']
            tree = ET.ElementTree(root)
            tree.write(xmlPath, encoding='utf-8', xml_declaration=True)
            lock.release()

    def run(self):
        while not self.pageQueue.empty() and self.__class__.runFlag > 0:
            #糗百页面消费者
            pageUrl = self.pageQueue.get()
            logging.info('get a new page URL:%s' %pageUrl)
            qiuBaiList, picDictList = self.fetchContent(pageUrl)
            if len(qiuBaiList) >= 1:
                self.writeContent(qiuBaiList)

            #糗百图片生产者
            if len(picDictList) >= 1:
                for item in picDictList:
                    self.picQueue.put(item)
                    logging.info('add a new picURL : %s' %item['picURL'])

        #如果两个队列都为空，则线程退出，并通知图片下载线程也退出
        if self.pageQueue.empty() and self.picQueue.empty():
            from PicDownloader import PicDownloader
            self.runFlag = 0
            PicDownloader.runFlag = 0
            logging.info('QiubaiReader thread : %s quits' %threading.current_thread().getName())


if __name__ == '__main__':
    import Queue
    pageQueue = Queue.Queue()
    picQueue = Queue.Queue()
    pageQueue.put('http://www.qiushibaike.com/hot/page/2?s=4628056')
    dataPath = 'D:\\Developer\\temp\\data'
    picPath = 'D:\\Developer\\temp\\pic'
    xmlName = 'QiuBai.xml'
    pathDict = {'dataPath':dataPath, 'picPath':picPath, 'xmlName':xmlName}
    q = QiubaiReader(pageQueue, picQueue, pathDict)
    q.start()
