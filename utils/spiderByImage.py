import time
from selenium import webdriver
from pyquery import PyQuery as pq
from selenium.webdriver.support.ui import WebDriverWait
class getImagByImage():

    def __init__(self, maxWaitTime):
        self.maxWaitTime = maxWaitTime
        self.chromedriver_path ="C:\\Users\\CK\\AppData\\Local\\Google\\Chrome\\Application\\chromedriver.exe"
        self.browser = webdriver.Chrome(executable_path=self.chromedriver_path)
        self.browser.set_window_size(1400,900)
        self.wait = WebDriverWait(self.browser, 30)
        self.url = 'https://www.baidu.com/'
        self.browser.get(self.url)

    def gundong(self):
        terminal = time.time() + float(self.maxWaitTime)
        js = 'return document.body.scrollHeight;'
        height = 0
        while True:
            if (time.time() <terminal):
                new_height = self.browser.execute_script(js)
                if new_height > height:
                    for i in range(height, new_height, 500):
                        self.browser.execute_script('window.scrollTo(0, {})'.format(i))
                        height = new_height
                        time.sleep(0.5)
                else:
                    print("滚动条已经处于页面最下方!")
                    self.browser.execute_script('window.scrollTo(0, 0)')  # 页面滚动到顶部
                    break
            else:
                print("时间已到")
                break

    def getData(self, imgUrl):
        # 点击搜索图片
        self.browser.find_element_by_xpath('//*[@id="form"]/span[1]/span[1]').click()
        upload  = self.browser.find_element_by_id('soutu-url-kw')
        upload.send_keys(imgUrl)
        # 点击百度
        self.browser.find_element_by_xpath('//*[@id="form"]/div/div[1]/span[3]').click()
        self.gundong()
        time.sleep(0.5)
        imgs = []
        html = self.browser.page_source
        doc = pq(html)
        items1 = list(doc('.graph-similar-list  .general-waterfall').items())
        for item1 in items1:
            for item2 in item1:
                doc1 = pq(item2)
                items2 = list(doc1('.general-imgcol  .general-imgcol-item').items())
                for item in items2:
                    img_url = item.find('img').attr('src')
                    print(img_url)
                    imgs.append(img_url)
        self.browser.close()
        return imgs