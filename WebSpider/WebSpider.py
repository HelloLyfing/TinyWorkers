# coding:utf-8

import os
import sys
import time
import Queue
import logging
from QiubaiReader import QiubaiReader
from PicDownloader import PicDownloader


#全局规定要保存的路径位置即文件名称
basePath = os.path.dirname(os.path.abspath(__file__))
dataPath = os.path.join(basePath, 'data')
picPath = os.path.join(basePath, 'pic')
xmlName = 'QiuBaiContent.xml'


class PageURL(object):
    """
    获取糗百某一类页面的所有URL
    """
    domain = 'http://www.qiushibaike.com/'
    pageNumSign = 'page/'                           #例如 www.foo.com/hot/page/3 ,page_sign 的形式也可能为"?page=3"
    page = 'hot'
    pageNum = 150                                   #某类页面下的内容，服务器可供访问的最多页数，如/hot页面下是150页，/late页面下是2000页(但几乎没有高质量内容)
    queue = Queue.Queue()

    def __init__(self):
        self.page_list = []
        self.page_list.extend(map(self.getPageURL, range(1, (self.pageNum+1))))
        for item in self.page_list:
            self.queue.put(item)

    def getQueue(self):
        return self.queue

    def getPageURL(self, page_num):
        URL = None
        if page_num > 1:
            URL = self.domain.strip('/') + '/' + self.page + '/' + self.pageNumSign + str(page_num)
        elif page_num == 1:
            URL = self.domain.strip('/') + '/' + self.page
        return URL

def initDir():
    for path in [dataPath, picPath]:
        if not os.path.exists(path):
            os.mkdir(path)

    path = os.path.join(dataPath, xmlName)
    if not os.path.exists(path):
        fo = open(path, 'w')
        fo.write('<?xml version="1.0" encoding="utf-8"?>\n<root></root>')
        fo.close()

def logConfig():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(filename)s | [line:%(lineno)d] | %(message)s',
        datefmt='%H:%M:%S',
    )

    logging.info('logging config done.')

def main(n=3, m=2):
    """
    main()函数要做的工作有：

    1.  初始化两个工作队列(线程安全队列)：pageURLQueue 和 picURLQueue
        pageURLQueue：其中存放的是所有待爬取页面的URL
        picURLQueue：其中存放的是所有待下载的糗百图片

    2.  初始化爬虫需要的工作路径和相关文件；初始化logging配置

    3.  启动n条QiubaiReader线程，并将pageURLQueue和picURLQueue这两个队列传入线程
        该线程的工作内容是：
        a.  从pageURLQueue队列取出一个页面的URL；
        b.  读取该页面html源码，解析出其中包含的若干条糗百文章
        c.  筛选这些文章，将符合条件的文章(如点赞超过2000)进行格式化，然后保存到xml文件中
        d.  如果某条糗百文章附带图片，将该图片的URL放入picURLQueue
        e.  重复a, b, c, d 步骤
        f.  当上述两个队列(queue)都为空后，通知所有PicDownloader线程退出，自己接着退出

    4.  启动m条PicDownloader线程，并将picURLQueue队列传入每条线程。该线程的工作内容是：
        从picURLQueue队列取出一个图片URL，然后将其指向的图片资源下载至指定文件夹

    main函数参数中的n代表QiubaiReader线程的个数；m代表PicDownloader线程的个数

    因为并不是每条糗百都附带图片，所以PicDownloader线程的个数理应比QiubaiReader线程的要少
    """

    pageURLQueue = PageURL().getQueue()
    picURLQueue = Queue.Queue()
    initDir()
    logConfig()
    pathDict = {'dataPath':dataPath, 'picPath':picPath, 'xmlName':xmlName}             #dataPath，存放xml数据文件的路径； picPath，存放下载图片的路径

    for i in range(n):
        QiubaiReader(pageURLQueue, picURLQueue, pathDict).start()
        logging.info('start a new "QiubaiReader" thread')
    for i in range(m):
        PicDownloader(picURLQueue, pathDict).start()
        logging.info('start a new "PicDownloader" thread')

if __name__ == '__main__':
    doc = main.__doc__.decode('utf-8')
    preDoc = u'main(n, m) 为函数入口，以下是它的文档内容：\n'
    print  preDoc + doc

    prompt = u"输入'yes'开始爬取 > "
    cmd = raw_input(prompt.encode(sys.stdout.encoding))
    
    if cmd in ['yes', 'y']:
        main()
