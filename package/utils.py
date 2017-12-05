# -*- coding: utf-8 -*-

import re
import os
import datetime

"""
杂项处理函数与对象
"""

pattern_zh = "[\u4e00-\u9fa5]"  # 中文匹配模板
pattern_ip = "(25[0-5]|2[0-4]\d|[0-1]\d{2}|[1-9]?\d)\.(25[0-5]|2[0-4]\d|[0-1]\d{2}|[1-9]?\d)\.\
              (25[0-5]|2[0-4]\d|[0-1]\d{2}|[1-9]?\d)\.(25[0-5]|2[0-4]\d|[0-1]\d{2}|[1-9]?\d)"


# 忽略大小写的字符串比较
def compare_ignore_case(item, entry):
    if len(item) != len(entry):
        return False
    a = item.lower()
    b = entry.lower()
    if a != b:
        return False
    return True


# 检验是否含有汉字
def han_chars_involved(word):
    if re.search(pattern_zh, word):
        return True
    else:
        return False


# 检验是否含有数字
def numbers_involved(word):
    if re.search("[0-9]", word):
        return True
    else:
        return False


# 检验是否含有特殊字符(除字母,汉字,数字,空格外的)
def unusual_chars_involved(word):
    if re.search("[^\u4e00-\u9fa5a-zA-Z0-9\s]", word):
        return True
    else:
        return False


# 词条有效性检验
def validity_check(word):
    if unusual_chars_involved(word):
        message = "该词条包含特殊字符, 是否保存?"
        return False, message
    if han_chars_involved(word):
        message = "该词条包含汉字字符, 是否保存?"
        return False, message
    if numbers_involved(word):
        message = "该词条包含数字字符, 是否保存?"
        return False, message
    return True, None


# 转为正常格式(字母, 数字, 汉字, 空格, -符之外的剔除)
def trans_to_normal(word):
    return re.sub("[^\u4e00-\u9fa5a-zA-Z0-9\s-]", "", word)


# 提取词条的释义
def get_mean_items(group):
    # print(type(group), group)
    items = []
    for item in group:
        splits = item.split('；')
        for i in splits:
            i = re.sub(r"(（.+）)?", "", i)  # 去除全角括号部分
            i = re.sub(r"(\(.+\))?", "", i)  # 去除半角括号部分
            i = re.sub(r"([a-zA-Z]+\.)?", "", i)  # 去除词性前缀
            i = re.sub(r"(网络:\s)?", "", i)  # 去除'网络: '前缀
            items.append(i)
    return set(items)  # 去重


# 获取文件上次修改的天数间隔
def modified_days(file):
    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(file))  # 上次修改/创建的时间
    now = datetime.datetime.now()  # 现在时间
    days = (now - mtime).days
    return days  # 返回修改时间天数


# 检验代理IP文件是否有效(存在有效内容且未过期)
def is_valid_ipfile(file):
    if os.path.getsize(file) == 0:  # 空文件
        return False
    is_recent_modified = modified_days(file) < 1
    with open(file) as ip_file:
        is_ip_included = re.search(r"HTTP", ip_file.read())

    return is_ip_included and is_recent_modified


# l = ['adj.习惯于；通常的；惯常的', 'v.“accustom”的过去分词和过去式', '网络: 习惯的；习惯了的；习惯于…的']
# print(get_mean_items(l))

