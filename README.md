口罩到货监控机器人
==================

监控 京东、网易的一次性口罩 何里有货。有货则在企业微信发消息通知。

安装说明
----------

1. 安装 python3：https://www.python.org/downloads/
2. 如果不是mac，请自己下载 chromedriver，并调整 `kouzhao.py` 中的变量值
   chromedriver下载地址：https://chromedriver.chromium.org/ chromedriver与代码放在一个目录下。
3. 安装

```bash
pip install -r requirements.txt
```

运行
------

```
python src/kouzhao.py
```
