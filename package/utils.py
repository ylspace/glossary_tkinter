# -*- coding: utf-8 -*-

"""
杂项处理函数工具
"""

import re
import os
import datetime
import sqlite3


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


# 获取文件上次修改的小时间隔
def modified_days(file):
    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(file))  # 上次修改/创建的时间
    now = datetime.datetime.now()  # 现在时间
    hours = (now - mtime).seconds / 3600
    return round(hours)  # 返回修改小时数


# 检验代理IP文件是否有效(存在有效内容且未过期)
def is_valid_ipfile(file):
    if os.path.getsize(file) == 0:  # 空文件
        return False
    is_recent_modified = modified_days(file) < 3
    with open(file) as ip_file:
        is_ip_included = re.search(r"HTTP", ip_file.read())

    return is_ip_included and is_recent_modified


def dbs_merge(main_db_file, appd_db_file):
    """
    将数据库appd_db_file合并到数据库main_db_file
    :param main_db_file: 接受数据的数据库文件路径
    :param appd_db_file: 附加数据的数据库文件路径
    :return is_succeed: 是否成功进行合并
    """
    is_succeed = True
    if not os.path.exists(main_db_file) or not os.path.exists(appd_db_file) or main_db_file == appd_db_file:
        return False  # 若有无效数据库文件路径或两参数为同一个数据库文件
    main_db_con = sqlite3.connect(main_db_file)
    main_db_cur = main_db_con.cursor()
    main_db_cur.execute('''ATTACH DATABASE {!r} AS append_db;'''.format(appd_db_file))
    main_db_cur.execute("INSERT OR IGNORE INTO CUSTOM SELECT * FROM append_db.CUSTOM;")
    count_affected = main_db_cur.rowcount  # 受到更改的行数
    if not count_affected:  # 无更改, 表明附加数据库为空, 或与原数据库内容完全相同
        is_succeed = False
    else:
        main_db_cur.execute("INSERT OR IGNORE INTO DICT SELECT * FROM append_db.DICT;")
    main_db_con.commit()
    main_db_cur.execute("DETACH DATABASE append_db;")
    main_db_cur.close()
    return is_succeed


