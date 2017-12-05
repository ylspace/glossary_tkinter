# -*- coding: utf-8 -*-

from package import application, crawler, database, proxy, translate
import time
import sys
import requests
import random
from PIL import Image, ImageTk
from tkinter import Tk, Label, font, StringVar
from threading import Thread


win_startup = Tk()  # 在外部创建Tk()对象, 使StringVar获得_root


def startup(progress):
    wryh12 = font.Font(family="微软雅黑", size=12)
    win_startup.overrideredirect(1)  # 创建一个无边框无按钮的窗口
    application.MainWin.center_in_scr(win_startup, 780, 540)  # 使其在屏幕居中,同时设定尺寸
    image = Image.open('.\src\startup_bg.jpg')  # 创建背景图像对象
    bg_image = ImageTk.PhotoImage(image)
    bg_image_label = Label(win_startup, width=780, height=510, image=bg_image)  # 创建带图像的背景标签
    bg_image_label.grid(row=0, column=0)
    info_label = Label(win_startup, width=78, font=wryh12, anchor='w', textvariable=progress)
    info_label.grid(row=1, column=0)

    progress.set('启动中: 创建网络爬虫...')
    win_startup.update_idletasks()
    spider = crawler.Crawler()  # 创建一个爬虫对象
    progress.set('启动中: 创建网页请求...')
    win_startup.update_idletasks()

    data = database.MasterDB().words_meanings_customs

    delay = 1
    num = len(data)
    if num >= 5:
        delay = 3 / num  # 总延迟时间4秒
    _ = time.time()
    for item in data:  # 遍历字典, item为key
        time.sleep(delay)
        if time.time() - _ >= 4.0:
            break
        progress.set('启动中: 从数据库导入词条 ' + item)
        win_startup.update_idletasks()

    progress.set('启动中...')
    win_startup.update_idletasks()
    time.sleep(1)  # 额外睡眠时间
    is_finished = True

    if is_finished:
        win_startup.destroy()
    win_startup.mainloop()
    return spider


sv = StringVar()
sv.set('启动中...')
my_crawler = startup(sv)


app = application.MainWin.create_main_win(my_crawler)  # 创建一个窗口对象, 并传入爬虫对象
app.update_network_status("检测中...")
app.dic = database.DataBase(app, app.tmp_db)  # 创建一个DataBase的实例对象, 从临时数据库(当前为空)对象中保存数据

check = StringVar()  # entry变化即检测存在信息
check.trace('w', lambda name, index, mode, chk=check: database.DataBase.is_exist(app.dic, chk.get()))
app.cobbx_item['textvariable'] = check

app.cobbx_item.focus_force()  # 使combobox获得焦点可输入


def network_check(obj):
    header = {
        "User-Agent":
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36"
             }
    while True:
        proxy_item = random.choice(proxy.get_proxy())
        proxies = {proxy_item[0]: proxy_item[1]}
        time.sleep(0.6)
        try:
            requests.get("http://cn.bing.com/dict/search/", headers=header, proxies=proxies)
            try:
                obj.update_network_status("已连接!")
            except RuntimeError:  # 用IDLE运行时, 结束GUI时报错
                sys.exit(0)
        except requests.exceptions.ConnectionError:
            try:
                obj.update_network_status("无法访问!")
            except RuntimeError:
                sys.exit(0)
        except requests.exceptions.ChunkedEncodingError:
            try:
                obj.update_network_status("无法访问!")
            except RuntimeError:
                sys.exit(0)
        except requests.exceptions.ReadTimeout:
            try:
                obj.update_network_status("访问超时!")
            except RuntimeError:
                sys.exit(0)


thread_net = Thread(target=network_check, args=(app,))
thread_net.daemon = True  # 设置为守护线程,主线程结束时也会结束
thread_net.start()


def count_check(obj):  # 检测词条总数
    while True:
        time.sleep(random.randrange(1.0, 3.0))
        try:
            obj.count_statusbar['text'] = "词条总数: " + str(len(obj.dic.words_meanings_customs))
        except RuntimeError:  # 用IDLE运行时, 结束GUI时报错
            sys.exit(0)


thread_count = Thread(target=count_check, args=(app,))
thread_count.daemon = True
thread_count.start()

translate.root_title(app)
app.root.mainloop()


