# -*- coding: utf-8 -*-

import requests
import re
import random
from tkinter import messagebox
from package import proxy


api_url = "http://www.xicidaili.com/api"
header = {
    'User-Agent':
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36"
         }


# 网页爬取器
class Crawler:
    def __init__(self):
        self.response = None
        self.url = "http://cn.bing.com/dict/search/"
        self.status_code = 200
        self.header = {"User-Agent":
                       "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)\
                        Chrome/45.0.2454.101 Safari/537.36",
                       "Accept - Language": "zh - CN, zh;q = 0.8",
                       'Connection': "keep-alive",
                       'Referer': "https://www.bing.com/",
                       'Upgrade - Insecure - Requests': 1
                       }

    def access(self, word, pass_connect_error):  # 访问和搜索
        post = {'q': word, 'go': "搜索"}

        content = ""
        proxy_list = proxy.get_proxy()
        proxies = {'https': random.choice(proxy_list)} if proxy_list else None
        try:
            self.response = requests.get(self.url, params=post, headers=header, proxies=proxies, timeout=6)
        except requests.exceptions.ConnectionError:
            if not pass_connect_error:
                messagebox.showerror(title="网络错误!", message="网络连接出错!")
        except requests.exceptions.ReadTimeout as timeout:
            msg = "访问地址超时!"
            match = re.search("host='.*?'", str(timeout))
            if match and match == "host='127.0.0.1'":
                msg += "请检查代理设置!"
            if not pass_connect_error:
                messagebox.showerror(title="网络错误!", message=msg)
        else:
            self.status_code = self.response.status_code
            content = self.response.text
            if re.search("<div>No results found for ", content) and not pass_connect_error:
                content = ""
                messagebox.showerror(title="网络错误!", message="请检查网络代理设置!")
        finally:
            return content
