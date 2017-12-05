# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup, SoupStrainer


# 内容解析器
class Parser:
    def __init__(self, page):
        only_div_tags = SoupStrainer("div")  # 只解析div标签
        self._soup = BeautifulSoup(page, 'lxml', parse_only=only_div_tags)  # 创建BeautifulSoup对象

    def get_word(self):  # 获取当前搜索的字词
        part_id = 1  # ID编号,由上至下
        tag_strong = self._soup.find('strong')  # 获取'strong'标签,即当前搜索单词所在处
        if tag_strong:
            return tag_strong.text, part_id  # 返回该字词和id
        else:
            return None, part_id  # 若搜索的字词不存在,则返回None

    def get_pronunciation(self):  # 获取当前字词的音标/拼音
        part_id = 2
        pronun = self._soup.find('div', {'class': 'hd_p1_1'})  # 获取该字词的音标/拼音
        if pronun:
            phonetic = pronun.text
            if '\xa0' in phonetic:  # 替换异类编码的空格符
                phonetic = phonetic.replace('\xa0', ' ')
            if '\xA0' in phonetic:
                phonetic = phonetic.replace('\xA0', ' ')
        else:
            phonetic = ""
        return phonetic, part_id  # 返回该字词的音标/拼音

    def get_meanings(self):  # 获取义项
        part_id = 3
        meaning = []  # 存放义项的列表
        tag_ul_prev = self._soup.find('div', class_="hd_area")  # 'ul'标签的前一个兄弟标签
        if tag_ul_prev:
            tag_ul = tag_ul_prev.next_sibling  # 获取'ul'标签
            if tag_ul:
                tag_li = tag_ul.find_all('li')
                for li in tag_li:
                    string = li.text
                    if u"网络" in string:
                        string = string.replace(u"网络", u"网络: ")
                    meaning.append(string)
        return meaning, part_id

    def get_egsentence(self):  # 获取例句
        part_id = 4
        tag_se_li1 = self._soup.find_all('div', class_='se_li')  # 查找例句
        eg = []  # 存放例句的列表
        for li1 in tag_se_li1:
            tag_sen_en = li1.find('div', class_='sen_en')
            eg.append(tag_sen_en.text)  # 将英文例句添加到列表
            tag_sen_cn = li1.find('div', class_='sen_cn')
            eg.append(tag_sen_cn.text)  # 将中文例句添加到列表
        return eg, part_id
