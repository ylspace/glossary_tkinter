import os.path
import inspect
import requests
from bs4 import BeautifulSoup, SoupStrainer
from package import utils


url = "http://www.xicidaili.com/nn"
header = {
    'User-Agent':
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36"
         }

cur_proxy_list = []
proxy_list = []
proxies_file = r"\data\proxy_list.txt"


def _search_proxy():
    for page in range(1, 9):  # 从前8页中提取
        req = requests.get(url + "/{}".format(page), headers=header)
        html = req.text

        only_tr_tag = SoupStrainer("tr")
        soup = BeautifulSoup(html, 'lxml', parse_only=only_tr_tag)

        for tr in soup.contents[2:]:  # 忽略html和tr表头
            all_td = tr.find_all("td")
            proxy_list.append((all_td[5].string, all_td[1].string + ":" + all_td[2].string))


def get_proxy():
    global cur_proxy_list

    if __name__ == "__main__":
        proxy_file_path = proxies_file
    else:
        caller_path = os.path.normpath(inspect.stack()[1][1])
        if os.path.dirname(caller_path).endswith("package"):
            proxy_file_path = os.path.dirname(os.path.dirname(caller_path)) + proxies_file
        else:
            proxy_file_path = os.path.dirname(caller_path) + proxies_file

    if os.path.exists(proxy_file_path) and utils.is_valid_ipfile(proxy_file_path):  # 文件存在有效内容且上次更新时间小于3小时
        with open(proxy_file_path, "r") as proxy_file:
            cur_proxy_list = eval(proxy_file.read())

    elif not os.path.exists(proxy_file_path) or not utils.is_valid_ipfile(proxy_file_path):  # 文件不存在 或无有效内容/过期
        with open(proxy_file_path, "w") as proxy_file:
            try:
                _search_proxy()
            except requests.exceptions.ConnectionError:
                pass
            else:
                proxy_file.write(str(proxy_list))
            finally:
                cur_proxy_list = proxy_list
    return cur_proxy_list


