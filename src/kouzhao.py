#!/usr/bin/env python
# coding: utf-8
import datetime
import logging
import time

import environ
import os

logging.basicConfig(level=logging.INFO, filename='kouzhao.log', format='%(asctime)s %(message)s')

log = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
env = environ.Env()

env.read_env(os.path.join(BASE_DIR, '.env'))

notify_robot = env('NOTIFY_ROBOT', default='<请去企业微信创建一个机器人，这里放机器人的通知地址>')
# 请自己改下chromedriver的文件位置
chromedriver = os.path.join(BASE_DIR, 'driver/mac/chromedriver')


log.info('通知地址：%s', notify_robot)

class KouzhaoMonitor:
    def __init__(self, search_url, css_selector):
        self.is_headless = 1
        self.driver = self._get_driver(self.is_headless)
        self.driver.implicitly_wait(5)
        self.search_url = search_url
        self.notify_robot = notify_robot
        self.css_selector = css_selector
        self.invalid_goods_keywords = '非卖品 售罄 国际 无货'.split(' ')
        self.notify_history = {}
        self.duplicate_check_span_in_seconds = 60 * 5

    def _get_options(self, is_headless):
        from selenium.webdriver.chrome.options import Options
        chrome_options = Options()
        if self.is_headless:
            chrome_options.add_argument("--headless")
        return chrome_options

    def _get_driver(self, is_headless):
        from selenium import webdriver
        return webdriver.Chrome(chrome_options=self._get_options(is_headless),
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
        self.driver.get(self.search_url)
        time.sleep(5)
        items = self.driver.find_elements_by_css_selector(self.css_selector)
        log.info('检索到 %s 个商品', len(items))
        for i in items:
            text = i.text
            if '一次性' in text and '口罩' in text:
                is_notify = True
                for invalid_keyword in self.invalid_goods_keywords:
                    if invalid_keyword in text:
                        is_notify = False
                        break
                if is_notify:
                    href = i.find_element_by_css_selector('a').get_attribute('href')
                    msg = '有货：\n' + text + '\n链接：' + href
                    log.info(msg)
                    self._send_notice(msg)

    def close(self):
        self.driver.close()


class WangyiMonitor(KouzhaoMonitor):
    def __init__(self):
        search_url = 'https://you.163.com/search?keyword=口罩%20一次性'
        css_selector = '.j-product'
        super().__init__(search_url, css_selector)


class JdMonitor(KouzhaoMonitor):
    def __init__(self):
        search_url = 'https://search.jd.com/Search?keyword=%E5%8F%A3%E7%BD%A9%E4%B8%80%E6%AC%A1%E6%80%A7&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&suggest=1.def.0.V17--12s0%2C20s0%2C38s0%2C97s0&wq=%E5%8F%A3%E7%BD%A9&wtype=1&click=1'
        css_selector = '.gl-item'
        super().__init__(search_url, css_selector)


if __name__ == '__main__':
    wangyi = WangyiMonitor()
    jd = JdMonitor()
    while True:
        log.info('网易检索中...')
        wangyi.run()
        log.info('京东检索中...')
        jd.run()
