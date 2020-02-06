#!/usr/bin/env python
# coding: utf-8
import datetime
import logging
import os
import time
from abc import abstractmethod, ABC

import environ
from selenium.webdriver import ActionChains
from selenium.webdriver.remote.webelement import WebElement

logging.basicConfig(level=logging.INFO, filename='kouzhao.log', format='%(asctime)s %(message)s')

log = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
env = environ.Env()

env.read_env(os.path.join(BASE_DIR, '.env'))

notify_robot = env('NOTIFY_ROBOT', default='<请去企业微信创建一个机器人，这里放机器人的通知地址>')
# 请自己改下chromedriver的文件位置
chromedriver = os.path.join(BASE_DIR, 'driver/mac/chromedriver')

log.info('通知地址：%s', notify_robot)


class KouzhaoMonitor(ABC):
    _driver = None
    _is_headless = 0

    def __init__(self, search_url, css_selector, cookie_file):
        self.search_url = search_url
        self.notify_robot = notify_robot
        self.css_selector = css_selector
        self.invalid_goods_keywords = '非卖品 售罄 国际 无货 婴儿口罩 儿童口罩'.split(' ')
        self.notify_history = {}
        self.duplicate_check_span_in_seconds = 60 * 5
        self.login()

    @classmethod
    def _get_options(cls, is_headless):
        from selenium.webdriver.chrome.options import Options
        chrome_options = Options()
        if cls._is_headless:
            chrome_options.add_argument("--headless")
        return chrome_options

    @classmethod
    def _get_driver(cls, is_headless):
        from selenium import webdriver
        return webdriver.Chrome(chrome_options=cls._get_options(is_headless),
                                executable_path=chromedriver)

    def _check_duplicate(self, text):
        """两次同样通知的间隔时间控制"""
        now = datetime.datetime.now()
        if text in self.notify_history and (
            now - self.notify_history[text]).seconds < self.duplicate_check_span_in_seconds:
            return True
        else:
            self.notify_history[text] = now
        return False

    def _send_notice(self, text):
        if self._check_duplicate(text):
            return
        import requests
        requests.post(
            self.notify_robot,
            json={
                "msgtype": "text",
                "text": {
                    "content": text
                }})

    def run(self):
        time.sleep(1)
        self.driver.get(self.search_url)
        actions = ActionChains(self.driver)
        items = self.driver.find_elements_by_css_selector(self.css_selector)
        log.info('检索到 %s 个商品', len(items))
        to_buy = []
        for i in items:
            text = i.text
            if '一次性' in text and '口罩' in text:
                is_notify = True
                for invalid_keyword in self.invalid_goods_keywords:
                    if invalid_keyword in text:
                        is_notify = False
                        break
                if is_notify:
                    print('有货!')
                    href = i.find_element_by_css_selector('a').get_attribute('href')
                    msg = '有货：\n' + text + '\n链接：' + href
                    log.info(msg)
                    import random
                    actions.move_to_element(i).perform()
                    self.driver.get_screenshot_as_file(f'tmp-{random.randrange(1, 9999)}.png')
                    self._send_notice(msg)
                    to_buy.append(i)
        for i in to_buy:
            self.screenshot(i.find_elements_by_css_selector('a').get_attribute('href'))
            self.autobuy(i)

    @property
    def driver(self):
        if not KouzhaoMonitor._driver:
            KouzhaoMonitor._driver = KouzhaoMonitor._get_driver(KouzhaoMonitor._is_headless)
            KouzhaoMonitor._driver.implicitly_wait(5)
        return KouzhaoMonitor._driver

    @classmethod
    def quit(cls):
        try:
            cls._driver.quit()
        except:
            pass

    def screenshot(self, href):
        filename = "logs/" + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f.png')
        self.driver.get(href)
        self.driver.get_screenshot_as_file(filename)

    @abstractmethod
    def autobuy(self, element: WebElement):
        pass

    @abstractmethod
    def login(self):
        pass


class WangyiMonitor(KouzhaoMonitor):
    def login(self):
        self.driver.get('https://you.163.com/u/login')
        input('请登录 网易严选，以便有货的时候自动下订单')

    def autobuy(self, element):
        pass

    def __init__(self):
        search_url = 'https://you.163.com/search?keyword=口罩%20一次性'
        css_selector = '.j-product'
        cookie_file = 'wangyi.cookie'
        super().__init__(search_url, css_selector, cookie_file)


class JdMonitor(KouzhaoMonitor):
    def login(self):
        self.driver.get('https://passport.jd.com/new/login.aspx?ReturnUrl=https%3A%2F%2Fwww.jd.com%2F')
        input('请登录京东网站，以便有货的时候自动下订单')

    def autobuy(self, element):
        try:
            driver = self.driver
            element.find_element_by_link_text('加入购物车').click()
            # driver.find_element_by_link_text('加入购物车').click()
            driver.find_element_by_link_text('去购物车结算').click()
            driver.find_element_by_link_text('去结算').click()
            driver.find_element_by_id('order-submit').click()
        except Exception:
            log.exception('自动购买失败')

    def __init__(self):
        search_url = 'https://search.jd.com/Search?keyword=%E5%8F%A3%E7%BD%A9%E4%B8%80%E6%AC%A1%E6%80%A7&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&suggest=1.def.0.V17--12s0%2C20s0%2C38s0%2C97s0&wq=%E5%8F%A3%E7%BD%A9&wtype=1&click=1'
        css_selector = '.gl-item'
        cookie_file = 'jd.cookie'
        super().__init__(search_url, css_selector, cookie_file)


if __name__ == '__main__':

    try:
        wangyi = WangyiMonitor()
        jd = JdMonitor()
        while True:
            log.info('网易检索中...')
            wangyi.run()
            log.info('京东检索中...')
            jd.run()
    except Exception as e:
        log.exception(e)
        WangyiMonitor.quit()
        JdMonitor.quit()
