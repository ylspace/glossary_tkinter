# -*- coding: utf-8 -*-

import threading
import copy
import queue
from collections import deque
from tkinter import *
from tkinter import font, _tkinter, messagebox, StringVar
# 使用ttk的组件,除Scrollbar(不会在不需要时自动隐藏slider), Frame
from tkinter.ttk import Button, Combobox, Entry, Label, Notebook, Radiobutton, Treeview, Progressbar
from idlelib import ToolTip
import weakref
import time
from package import widgets, parser, database, utils, proxy

# 全局变量
word_status_void = '词条状态: '
word_status_saved = '词条状态: 已保存'
word_status_unsaved = '词条状态: 未保存'
classification = ['数据结构', '算法公式', '电子通信', '底层硬件', '艺术绘画', '影视后期',
                  '软件操作', '科技理论', '网络技术', '软件工程', '编程概念', '数学应用']


# 主窗口
class MainWin(Frame):  # 继承自Frame类
    def __init__(self, master, my_crawler):  # 初始化方法, master: 应用宿主,此处为root根窗口
        super().__init__(master)  # 套用父类的初始化方法
        self.root = master
        self.pack(expand=1, fill=BOTH)  # 初始化应用布局
        self.my_crawler = my_crawler
        self.my_crawler_access = self.my_crawler.access  # 提前获取方法, 避免重复查找属性

        self.win_Pref = None      # 弹出的设置窗口
        self.win_Dict = None      # 弹出的字典窗口
        self.win_Specify = None   # 弹出的分配窗口
        self.win_Classify = None  # 弹出的分类窗口
        self.win_Import = None    # 弹出的导入对话框
        self.win_Export = None    # 弹出的导出对话框
        self.win_Dict_exist = False
        self.wryh10 = font.Font(family="微软雅黑", size=10)
        self.wryh12 = font.Font(family="微软雅黑", size=12)
        self.wryh16 = font.Font(family="微软雅黑", size=16)
        self.dic = None  # 字典对象, 在Glossary.py的main方法中进行对象创建
        self.tmp_db = None  # 临时数据库对象
        self.last_entry = ''  # 上一次搜索的词条
        self.last_time_items = deque(maxlen=7)  # 创建一个固定长度的双端队列,存储之前搜索过的几个词条
        self.search_error = False  # 搜索出错

        self.bottom_statusbar()
        self.example_field()  # 初始时执行组件创建的方法
        self.explain_field()
        self.button_tools()
        self.entry_tools()
        self.menubar_field()
        self.center_in_scr(self.root, 1200, 700)  # 调用静态方法,使宿主窗口居中显示

        # 配置快捷键
        self.bind_all("<Control-s>", lambda event: self.dict_handle("save"))
        self.bind_all("<Control-r>", lambda event: self.dict_handle("remove"))
        self.bind_all("<Control-f>", lambda event: self.dict_handle("specify"))
        self.bind_all("<Control-g>", lambda event: self.dict_handle("classify"))
        self.bind_all("<Control-q>", lambda event: self.dict_handle("impt"))
        self.bind_all("<Control-w>", lambda event: self.dict_handle("expt"))
        self.bind_all("<Control-d>", lambda event: self.create_dict_win())
        self.bind_all("<Control-e>", lambda event: self.create_pref_win())

    def bottom_statusbar(self):  # 底部状态栏
        self.count_statusbar = Label(self, borderwidth=5)
        self.count_statusbar.pack(expand=0, side=BOTTOM, fill=X)

    def example_field(self):  # 创建底部例句区域
        self.example_frame = Frame(self)
        self.example_frame.pack(expand=0, side=BOTTOM, fill=X)
        self.txt_example = Text(self.example_frame, height=20, font=self.wryh12, background='azure2')  # 高度行数,宽度字数
        # 将滚动条绑定到Text组件
        vbar = Scrollbar(self.example_frame, orient=VERTICAL, command=self.txt_example.yview)
        vbar.pack(side=RIGHT, fill=Y)
        self.txt_example['yscrollcommand'] = vbar.set

        self.txt_example.pack(expand=0, side=BOTTOM, fill=X)
        self.txt_example['state'] = 'disabled'  # 使例句文本区不可写

    def explain_field(self):  # 创建右侧释义区域
        self.explainFrame = Frame(self)
        vbar = Scrollbar(self.explainFrame, name='vbar')

        self.txt_explain = CustomText(self.explainFrame, width=50, font=self.wryh16, background='floral white')
        self.txt_explain['state'] = 'disabled'  # 使释义文本区不可写

        self.word_statusBar = Label(self.explainFrame, text=word_status_void, borderwidth=4)
        self.word_statusBar.pack(expand=0, side=BOTTOM, fill=X)

        vbar['command'] = self.txt_explain.yview
        vbar.pack(side=RIGHT, fill=Y)
        self.txt_explain['yscrollcommand'] = vbar.set
        self.explainFrame.pack(expand=1, side=RIGHT, fill=BOTH)
        self.txt_explain.pack(side=TOP, expand=1, fill=BOTH)

    def button_tools(self):  # 创建左侧按钮区域
        self.buttonFrame = Frame(self, relief='groove')  # 寄存于应用app自身中
        self.buttonFrame.pack(expand=0, side=BOTTOM, fill=X)

        self.btn_save = Button(self.buttonFrame, text='保存', width=25, command=lambda: self.dict_handle("save"))
        self.btn_save.grid(row=0, column=0)
        ToolTip.ToolTip(self.btn_save, ["将此词条保存至数据文件中"])

        self.btn_delete = Button(self.buttonFrame, text='移除', width=25, command=lambda: self.dict_handle("remove"))
        self.btn_delete.grid(row=0, column=1)  # 使用lambda表达式, 以便传入参数,否则会被自动执行
        ToolTip.ToolTip(self.btn_delete, ["将此词条从数据文件中删除"])

        self.btn_specify = Button(self.buttonFrame, text='指定', width=25, command=lambda: self.dict_handle("specify"))
        self.btn_specify.grid(row=1, column=0)
        ToolTip.ToolTip(self.btn_specify, ["为该词条指定自定义释义"])

        self.btn_classify = Button(self.buttonFrame, text='分类', width=25, command=lambda: self.dict_handle("classify"))
        self.btn_classify.grid(row=1, column=1)
        ToolTip.ToolTip(self.btn_classify, ["对该词条进行分类"])

        self.btn_import = Button(self.buttonFrame, text='导入', width=25, command=lambda: self.dict_handle("impt"))
        self.btn_import.grid(row=2, column=0)

        self.btn_export = Button(self.buttonFrame, text='导出', width=25, command=lambda: self.dict_handle("expt"))
        self.btn_export.grid(row=2, column=1)

        self.btn_openDict = Button(self.buttonFrame, text='词典', width=25, command=self.create_dict_win)
        self.btn_openDict.grid(row=3, column=0)
        ToolTip.ToolTip(self.btn_openDict, ["打开词典窗口"])

        self.btn_preference = Button(self.buttonFrame, text='设置', width=25, command=self.create_pref_win)
        self.btn_preference.grid(row=3, column=1)
        ToolTip.ToolTip(self.btn_preference, ["打开设置窗口"])

        wryh12 = font.Font(family="微软雅黑", size=12)
        self.lbl_networkinfo = Label(self.buttonFrame, anchor='center', font=wryh12)
        self.lbl_networkinfo['text'] = "网络状态: "
        self.lbl_networkinfo.grid(row=4, column=0, columnspan=3, sticky='nesw')

    def entry_tools(self):
        self.entryFrame = Frame(self)  # 创建词条输入区域
        self.entryFrame.pack(expand=1, fill=BOTH)

        self.lbl_check = Label(self.entryFrame, text='查询: ', font=self.wryh12)
        self.lbl_check.grid(row=0, column=0)

        def reset(entry):
            self.cobbx_item.delete(0, END)
            self.cobbx_item.insert(0, entry)
            self.cobbx_item.update()

        self.cobbx_item = Combobox(self.entryFrame, background='snow', font=self.wryh12)
        self.cobbx_item.bind('<Return>', self.keyevent_entry)  # 事件绑定, 按下回车键触发search方法
        self.cobbx_item.grid(row=0, column=1)
        self.cobbx_item.reset = reset

        # 寄存于EntryFrame组件中
        self.btn_search = Button(self.entryFrame, text='确认', command=lambda arg=self: MainWin.search(arg))
        self.btn_search.grid(row=0, column=2)

        self.lbl_existinfo = Label(self.entryFrame, font=self.wryh10)  # 创建词条操作信息标签
        self.lbl_existinfo.grid(row=1, column=0, columnspan=2)

    def menubar_field(self):
        self.menuBar = widgets.MainMenu(self)
        self.menuBar.set()
        self.root.config(menu=self.menuBar)

    def keyevent_entry(self, event):  # 键盘事件处理: 按下回车键
        # print("你按下了: " + str(event.keycode))
        MainWin.search(self)

    def dict_handle(self, operation):
        if self.dic:
            getattr(self.dic, "{0}".format(operation))()  # 根据传入的参数调用相应方法

    def explain_display(self, args):  # 在释义和例句文本区域显示相关条目
        self.txt_explain['state'] = 'normal'  # 清空操作前将其设置为常规的可写状态
        self.txt_explain.delete(0.0, END)  # 释义文本内容清空
        self.txt_example['state'] = 'normal'  # 清空操作前将其设置为常规的可写状态
        self.txt_example.delete(0.0, END)  # 例句文本内容清空
        for i in args:
            items = i[0]
            ID = i[1]
            if ID == 3:  # 义项
                means = ''
                for item in items:
                    means += '{0}\n'.format(item)
                self.txt_explain.insert(END, means)  # 将词性和释义插入文本区域
                self.txt_explain['state'] = 'disabled'  # 插入文本后将其设置为只读
            elif ID == 4:  # 例句
                egs = ''
                for item in range(len(items)):
                    if item % 2 == 0:  # 英文例句
                        egs += str(int(item / 2 + 1)) + '.' + items[item] + '\n'
                    else:  # 中文例句
                        egs += '{0}\n'.format(items[item])
                self.txt_example.insert(END, egs)  # 将中文例句插入例句区域
                self.txt_example['state'] = 'disabled'  # 插入文本后将其设置为只读
            elif ID == 1:  # 单词
                the_word = '{0}\n'.format(items)
                self.txt_explain.insert(END, the_word)  # 将单词,音标插入文本区域
            else:  # 音标/音标
                phonetics = '{0}\n'.format(items)
                self.txt_explain.insert(END, phonetics)
        self.customs_display(self.cobbx_item.get())  # 显示词条分类和自定义高亮的词义

    def customs_display(self, word):
        # 须考虑无数据时和未保存时
        self.txt_explain['state'] = 'normal'  # 插入前将其设置为常规的可写状态
        if len(self.dic.words_meanings_customs) != 0 and self.word_statusBar['text'] == word_status_saved:
            try:
                specify, classify = self.dic.words_meanings_customs[word][2], self.dic.words_meanings_customs[word][3]
            except KeyError:  # 存储与取值显示时间不一致
                pass
            else:
                endline_start = str(float(self.txt_explain.index(END)) - 1.0)
                if classify:
                    if '分类:' in self.txt_explain.get(endline_start, END):  # 若已经插入了分类
                        self.txt_explain.delete(endline_start, END)
                    self.txt_explain.insert(END, "\n分类: " + classify)
                else:
                    if '分类:' in self.txt_explain.get(endline_start, END):
                        self.txt_explain.delete(endline_start, END)
                    self.txt_explain.insert(END, "\n分类: 未分类")

                if specify.startswith('-_-'):  # 自定义的词义
                    self.txt_explain.insert(END, '\t\t指定词义: ' + specify[3:])
                    self.txt_explain.highlight_pattern(specify[3:], start=endline_start, end=END)
                elif specify:
                    self.txt_explain.highlight_pattern(specify)
                else:  # 用于清除指定后刷新显示
                    self.txt_explain.highlight_pattern('')

        self.txt_explain['state'] = 'disabled'  # 插入文本后将其设置为只读

    def create_dict_db(self):
        self.dic = database.DataBase(self, self.tmp_db)  # 创建一个DataBase的实例对象, 可从临时数据库(当前为空)对象中保存数据

    @staticmethod
    def search(self, keyword=None, *arg):  # 搜索关键词的方法, 参数keyword用以从字典窗口中加载, arg用于获取保存状态
        self.dic.tmp_db = None  # 重置临时数据库对象
        if keyword:
            entry = keyword
            self.cobbx_item.reset(entry)
        else:
            entry = utils.trans_to_normal(self.cobbx_item.get())  # 获取框内的词条(为字符串), 剔除非法字符
            self.cobbx_item.reset(entry)
        is_saved = arg[0] if arg else database.DataBase.is_exist(self.dic, entry)  # arg不为空时传入的is_saved均为False
        go_search = entry != self.last_entry if is_saved else True  # 决定是否进行搜索, 若未保存则一定需要搜索
        if 0 < len(entry) <= 64 and go_search:  # 检查是否为空,以及是否未改变,以及是否未保存
            self.lbl_existinfo['text'] = ""  # 重置信息标签, 不显示消息
            self.search_error = False  # 重置搜索情况, 未出错
            if not is_saved:  # 若数据库中不存在, 则执行网络搜索或显示区域返回(若一致)
                page = self.my_crawler_access(entry, pass_connect_error=False)  # 访问并获取页面
                if page:  # 检查是否获取到有效页面
                    my_parser = parser.Parser(page)  # 创建一个解析器, 并将页面传入解析器
                    word, id_1 = my_parser.get_word()  # 获取当前搜索的字词, 返回形式为网页中的
                    if not word:  # 检查所搜索的字词是否合法
                        self.lbl_existinfo['foreground'] = "red"
                        self.lbl_existinfo['text'] = "   查询出错! 请输入合法的字词!"  # 在信息标签上显示出错提示
                        self.search_error = True
                        return
                    self.search_error = False

                    if entry != word:
                        entry = word
                        self.cobbx_item.reset(word)
                    self.last_entry = entry

                    if entry not in self.last_time_items:
                        self.last_time_items.appendleft(entry)  # 添加最近搜索过的词条
                    self.cobbx_item['values'] = list(self.last_time_items)

                    self.lbl_existinfo['text'] = ''  # 字词合法则使信息标签文本置空
                    pronunciation, id_2 = my_parser.get_pronunciation()  # 获取当前单词的音标
                    meanings, id_3 = my_parser.get_meanings()  # 获取当前单词的释义
                    egSentence, id_4 = my_parser.get_egsentence()  # 获取当前单词的例句
                    self.explain_display(([word, id_1], [pronunciation, id_2], [meanings, id_3], [egSentence, id_4]))
                    # 对于meanings和egSentence, 需从list转换为str(TEXT)
                    data = (word, pronunciation, str(meanings), str(egSentence))  # word形式为网页中的
                    self.tmp_db = database.TempDB(data)  # 将数据存入内存中的临时数据库
                    self.dic.tmp_db = self.tmp_db

            else:  # 若已保存, 则从数据库载入并显示
                word = is_saved
                if entry != word:
                    entry = word
                    self.cobbx_item.reset(entry)
                self.explain_display(self.dic.get_data(word))

                if self.win_Dict_exist:  # win_Dict须存在
                    self.win_Dict.refresh_sel(entry)  # 刷新字典中条目选择
                if entry not in self.last_time_items:
                    self.last_time_items.appendleft(entry)  # 添加最近搜索过的词条
                self.cobbx_item['values'] = list(self.last_time_items)
                self.last_entry = entry
        elif len(entry) > 64:
            self.lbl_existinfo['foreground'] = "red"
            self.lbl_existinfo['text'] = "查询出错! 长度超限(64字符)!"  # 在信息标签上显示出错提示
            self.search_error = True  # 重置搜索情况, 未出错
        if self.dic.tmp_db:  # 若search执行完全成功
            self.dic.is_displayed = True  # 更新数据内容显示状态
        else:
            self.dic.is_displayed = False

    def search_simple(self, keyword):
        if not hasattr(self, 'search_None_count'):
            self.search_None_count = 0
        # print('called search_simple')
        for _ in range(2):  # 若访问失败再次尝试
            page = self.my_crawler_access(keyword, pass_connect_error=True)  # 访问并获取页面
            if page:  # 检查是否获取到有效页面
                my_parser = parser.Parser(page)  # 创建一个解析器, 并将页面传入解析器
                word, id_1 = my_parser.get_word()  # 获取当前搜索的字词, 返回形式为网页中的

                pronunciation, id_2 = my_parser.get_pronunciation()  # 获取当前单词的音标
                meanings, id_3 = my_parser.get_meanings()  # 获取当前单词的释义
                egSentence, id_4 = my_parser.get_egsentence()  # 获取当前单词的例句
                items = (word, pronunciation, meanings, egSentence)
                result = copy.deepcopy(items)  # 结果副本
                return result

        self.search_None_count += 1
        print('第{}次返回None结果'.format(self.search_None_count))
        return None

    def get_text_display(self, item_id):  # 获取文本区域的显示
        if item_id == 1:
            return self.txt_explain.get('1.0', '1.end')  # 返回第一行

    def update_network_status(self, status):
        self.lbl_networkinfo['text'] = "网络状态: " + status

    @staticmethod
    def center_in_scr(self, *args):  # 使窗口居中于屏幕
        self.update_idletasks()
        self.attributes("-alpha", 0)  # 将窗口透明度暂时设置为0,防止位置闪烁
        if args:
            width = args[0]
            height = args[1]
        else:
            width = self.winfo_width()
            height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        self.attributes("-alpha", 1)

    @staticmethod
    def center_in_main(self, parent):  # 使窗口居中于主窗口
        self.update_idletasks()  # 更新窗口的尺寸更改或重绘等任务
        parent.root.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (parent.root.winfo_width() // 2) - (width // 2) + parent.root.winfo_rootx()
        y = (parent.root.winfo_height() // 2) - (height // 2) + parent.root.winfo_rooty()
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def create_pref_win(self):
        self.win_Pref = PrefWin(self)

    def create_dict_win(self):
        if not self.win_Dict_exist:
            self.win_Dict = DictWin(self)
            self.win_Dict.wait_window()  # 等待窗口直至销毁
            self.win_Dict_exist = False
        else:
            self.win_Dict.lift()

    def create_custom_win(self, items, word):
        self.win_Specify = SpecifyWin(self, items, word)

    def create_class_win(self, word):
        self.win_Classify = ClassifyWin(self, word)

    def create_impt_win(self, lines, file_path):
        self.win_Import = ImportWin(self, lines, file_path)

    def create_expt_win(self):
        self.win_Export = ExportWin(self)

    @staticmethod
    def create_main_win(my_crawler):
        root = Tk()  # 根窗口
        root.title("术语本")
        root.iconbitmap('./src/icon.ico')
        # root.geometry("1200x700")
        root.minsize(width=1000, height=740)  # 设置窗口最小尺寸
        # root.resizable(False, False)
        root.lift()  # 使窗口提升为活动窗口
        root.attributes('-topmost', True)  # 使窗口位于屏幕最上层
        root.after_idle(root.attributes, '-topmost', False)  # 取消保持最上层(否则点击外部其始终在最外层,子级toplevel除外)
        app = MainWin(root, my_crawler)  # 新生成应用对象(组件集), 寄于根窗口中
        return app


# 自定义Text类, 支持特定文本颜色高亮
class CustomText(Text):
    def __init__(self, *args, **kwargs):
        Text.__init__(self, *args, **kwargs)
        self.tag_configure("red", foreground="red")

    def highlight_pattern(self, pattern, start="1.0", end="end", regexp=False):
        self.tag_remove("red", '1.0', 'end')  # 清除标签着色
        start = self.index(start)  # 根据参数索引设定自定索引
        end = self.index(end)
        self.mark_set("matchStart", start)
        self.mark_set("matchEnd", start)
        self.mark_set("searchLimit", end)

        count = IntVar()
        index = self.search(pattern, "matchEnd", "searchLimit",
                            count=count, regexp=regexp)  # count.get()为索引到的字符串长度
        if index and count.get() != 0:
            self.mark_set("matchStart", index)  # 索引头
            self.mark_set("matchEnd", "%s+%sc" % (index, count.get()))  # 索引尾
            self.tag_add("red", "matchStart", "matchEnd")  # 未索引到的字符添加标签


# 字典窗口
class DictWin(Toplevel):
    def __init__(self, parent):
        Toplevel.__init__(self, parent)
        self.parent = parent
        self.parent.win_Dict_exist = True
        self.title("词典")
        self.protocol("WM_DELETE_WINDOW", lambda: self.handle_close())
        self.grid_columnconfigure(0, weight=1)  # 使TreeView可expand
        self.grid_rowconfigure(0, weight=1)
        self.geometry("650x600")
        self.tree_words = None
        self.create_contents()

    def handle_close(self):  # 解决主窗口失焦,随toplevel关闭而最小化
        self.destroy()
        self.parent.root.focus_force()  # 使主窗口获得focus

    def create_contents(self):
        self.frm_btns = Frame(self, width=800, height=50)
        self.frm_btns.pack(side=TOP, fill=X)

        self.btn_delete = Button(self.frm_btns, text='移除', command=lambda: self.parent.dict_handle("remove"))
        self.btn_delete.pack(side=LEFT)
        self.btn_specify = Button(self.frm_btns, text='指定', command=lambda: self.parent.dict_handle("specify"))
        self.btn_specify.pack(side=LEFT)
        self.btn_classify = Button(self.frm_btns, text='分类', command=lambda: self.parent.dict_handle("classify"))
        self.btn_classify.pack(side=LEFT)

        self.frm_tree = Frame(self)
        self.frm_tree.pack(side=TOP, fill=BOTH, expand=1)
        # columns为第2列之后列
        self.tree_words = Treeview(self.frm_tree, columns=('class', 'meaning'), selectmode='browse')  # 无法多选的选择模式

        # 将垂直滚动条绑定到Treeview组件
        vbar = Scrollbar(self.frm_tree, orient=VERTICAL, command=self.tree_words.yview)
        vbar.pack(side=RIGHT, fill=Y)
        self.tree_words['yscrollcommand'] = vbar.set

        # 将水平滚动条绑定到Treeview组件
        hbar = Scrollbar(self.frm_tree, orient=HORIZONTAL, command=self.tree_words.xview)
        hbar.pack(side=BOTTOM, fill=X)
        self.tree_words['xscrollcommand'] = hbar.set

        self.tree_words.pack(side=LEFT, fill=Y)  # 需最后布局

        self.tree_words.heading('#0', text='词条', command=self.handle_sort)  # 列头部
        self.tree_words.heading('#1', text='分类', anchor='w')
        self.tree_words.heading('#2', text='释义', anchor='w')  # 文字靠左

        self.tree_words.column('#0', width=140, stretch=False, minwidth=70)  # 不随窗口伸缩, 最小宽度70
        self.tree_words.column('#1', width=75, stretch=False, minwidth=50)  # 不随窗口伸缩, 最小宽度50
        # 不随窗口伸缩, 设置较大宽度, 以使底部水平滚动条依据该column,而非treeview窗口
        self.tree_words.column('#2', width=self.winfo_screenwidth()-120, stretch=False)

        first = None
        for items in self.parent.dic.words_meanings_customs.items():  # 遍历字典键值对
            if first is None:
                first = items[0]
            self.tree_words.insert('', 'end', iid=items[0], text=items[0], values=(items[1][3], items[1][1], ))

        # self.tree_words.grid(row=0, column=0, sticky='nesw')
        if first:
            self.tree_words.selection_set(first)
            self.tree_words.focus_set()
            self.tree_words.focus()
        self.tree_words.bind('<<TreeviewSelect>>', self.handle_tree)

        entry = self.parent.cobbx_item.get()
        if self.parent.word_statusBar['text'] == word_status_saved and entry:
            self.refresh_sel(entry)

    def handle_sort(self):
        print("排序!")

    def handle_tree(self, event):  # Treeview的事件处理函数
        keyword = self.tree_words.item(self.tree_words.focus())['text']
        MainWin.search(self.parent, keyword)

    def refresh(self, items, operation):  # 刷新显示
        if operation in ('add', 'Add', 'ADD'):
            self.tree_words.insert('', 'end', iid=items[0], text=items[0], values=(items[3], items[1], ))
        elif operation in ('del', 'Del', 'DEL'):
            if isinstance(items, tuple):
                self.tree_words.delete(*items)  # 根据iid删除多个条目
            else:
                self.tree_words.delete(items)  # 根据iid删除一个条目
        elif operation in ('classify', 'Classify', 'CLASSIFY'):
            self.tree_words.item(items[0], values=(items[3], items[1]))

    def refresh_sel(self, item):  # 刷新选择
        self.tree_words.selection_set('"' + item + '"')  # 根据iid设置条目选择, 外加引号避免内部处理导致词组被截取空格前
        self.tree_words.focus(item)  # 同时设置条目focus


# 设置窗口
class PrefWin(Toplevel):
    def __init__(self, parent):
        Toplevel.__init__(self, parent)
        self.parent = parent
        self.title("设置")
        # self.resizable(False, False)
        MainWin.center_in_scr(self, 800, 500)  # 居中于屏幕
        self.transient(self.parent)  # 窗口保持在前(无最大最小化按钮);且随主窗口的最小化也最小化(以下禁用主窗口情况下不适用)
        parent.root.attributes("-disabled", 1)  # 子窗口存在时禁用主窗口
        self.create_contents()
        while self.winfo_exists():  # 等待子窗口变为不存在的状态
            self.wait_window()
        parent.root.attributes("-disabled", 0)  # 子窗口关闭时,解禁主窗口
        # parent.root.deiconify()  # 使主窗口退出最小化状态,即原始活动状态
        parent.root.lift()  # 使主窗口跳转到前面

    def create_contents(self):
        self.frame = Frame(self, width="800", height="500")
        self.frame.grid(row=0, column=0)
        # self.frame.pack()
        self.ntbk = Notebook(self.frame, width='800', height='500')
        self.frm1 = Frame(self.ntbk, width='800', height='500')
        self.frm2 = Frame(self.ntbk, width='800', height='500')
        self.ntbk.add(self.frm1)
        self.ntbk.tab(0, text='视图')
        self.ntbk.add(self.frm2)
        self.ntbk.tab(1, text='高级')
        self.ntbk.grid(row=0, column=0)


# 指定窗口
class SpecifyWin(Toplevel):
    def __init__(self, parent, items, word):
        Toplevel.__init__(self, parent)
        self.parent = parent
        self.items = items
        self.word = word  # 正在分类的词条
        self.custom = None
        self.tree_items = None
        self.to_del_specify = False
        self.title("自定义词义")
        self.resizable(False, False)
        MainWin.center_in_scr(self, 380, 280)
        self.transient(parent)  # 窗口保持在前(无最大最小化按钮);且随主窗口的最小化也最小化(以下禁用主窗口情况下不适用)
        parent.root.attributes("-disabled", 1)
        if parent.win_Dict_exist:
            parent.win_Dict.attributes("-disabled", 1)
        self.create_contents()
        self.wait_window()
        if parent.win_Dict_exist:
            parent.win_Dict.attributes("-disabled", 0)
            parent.win_Dict.lift()
        parent.root.attributes("-disabled", 0)
        parent.root.lift()  # 关闭时主窗口会被最小化, 需要使主窗口在最前

    def create_contents(self):
        # columns为第2列之后列
        self.tree_items = Treeview(self, height=12, selectmode='browse')  # 无法多选的选择模式

        # 将垂直滚动条绑定到Treeview组件
        vbar = Scrollbar(self, orient=VERTICAL, command=self.tree_items.yview)
        vbar.grid(row=0, column=0, rowspan=10, sticky='nse')
        self.tree_items['yscrollcommand'] = vbar.set

        self.tree_items.heading('#0', text='词义')  # 列头部

        self.tree_items.column('#0', width=200, stretch=False, minwidth=70)  # 不随窗口伸缩, 最小宽度70

        for item in self.items:
            self.tree_items.insert('', 'end', iid=item, text=item)

        self.tree_items.grid(row=0, rowspan=10, column=0)

        Label(self, text="词条: {0}\n\n在左侧列表中选择一项词义,\n"
                         "或在下框中输入自定义词义".format(self.word)).grid(row=0, column=1, columnspan=2)
        entry_text = StringVar()
        entry = Entry(self, textvariable=entry_text)
        entry.grid(row=3, column=1, columnspan=2)

        self.tree_items.bind("<<TreeviewSelect>>", lambda event, this=self:
                             entry_text.set(this.tree_items.item(this.tree_items.focus())['text']))

        def button_handle(button):
            if button == 'ok':
                ent = entry.get()
                item_of_tree = self.tree_items.item(self.tree_items.focus())['text']
                if ent and ent not in self.items:
                    self.custom = '-_-' + ent  # 自定义词义
                else:
                    self.custom = item_of_tree if item_of_tree else ent
                self.destroy()

            elif button == 'cancel':
                self.custom = None
                self.destroy()

        def del_specify(this):
            this.to_del_specify = True
            self.destroy()
            messagebox.showinfo(title='操作成功!', message='指定词义删除成功!')

        btn_del_specify = Button(self, text='删除指定', command=lambda: del_specify(self))
        btn_del_specify.grid(row=8, column=2)
        if not self.parent.dic.words_meanings_customs[self.parent.cobbx_item.get()][2]:  # 未指定自定义词义时禁用该按钮
            btn_del_specify['state'] = 'disabled'
        btn_ok = Button(self, text='确认', command=lambda: button_handle('ok'))
        btn_ok.grid(row=9, column=1, sticky='s')
        btn_cancel = Button(self, text='取消', command=lambda: button_handle('cancel'))
        btn_cancel.grid(row=9, column=2, sticky='s')


# 分类窗口
class ClassifyWin(Toplevel):
    def __init__(self, parent, word):
        Toplevel.__init__(self, parent)
        self.parent = parent
        self.word = word  # 正在分类的词条
        self.title("自定义分类")
        self.resizable(False, False)
        self.custom_class = StringVar()
        self.custom_class.set(None)
        self.to_del_class = False
        self.protocol("WM_DELETE_WINDOW", self.close)  # 使对话框关闭事件重定义到finish方法
        MainWin.center_in_scr(self, 340, 150)  # 居中于屏幕
        self.transient(parent)  # 窗口保持在前(无最大最小化按钮);且随主窗口的最小化也最小化(以下禁用主窗口情况下不适用)
        parent.root.attributes("-disabled", 1)  # 子窗口存在时禁用主窗口
        if parent.win_Dict_exist:
            parent.win_Dict.attributes("-disabled", 1)
        self.create_buttons()
        self.wait_window()  # 等待子窗口变为不存在的状态
        if parent.win_Dict_exist:
            parent.win_Dict.attributes("-disabled", 0)
            parent.win_Dict.lift()
        parent.root.attributes("-disabled", 0)  # 子窗口关闭时,解禁主窗口
        parent.root.lift()  # 使主窗口在最前

    def create_buttons(self):
        self.lbl_tip = Label(self, text='')
        self.lbl_tip.pack(side=BOTTOM)

        Label(self, text="词条: " + self.word + '\t').place(relx=0.9, rely=0, anchor=NE)

        self.btn_set_class = Button(self, text='选择分类...',
                                    command=lambda this=self: this.create_items())
        self.btn_set_class.place(relx=0.3, rely=0.5, anchor=CENTER)

        def del_class(this):
            this.to_del_class = True
            self.destroy()
            self.custom_class.set(None)
            messagebox.showinfo(title='操作成功!', message='分类删除成功!')

        self.btn_del_class = Button(self, text='移除分类',
                                    command=lambda: del_class(self))
        self.btn_del_class.place(relx=0.7, rely=0.5, anchor=CENTER)
        if not self.parent.dic.words_meanings_customs[self.parent.cobbx_item.get()][3]:  # 未设分类时该按钮禁用
            self.btn_del_class['state'] = 'disabled'

        self.btn_set_class.bind("<Enter>", lambda evt: self.lbl_tip.configure(text='为当前词条设置分类'))
        self.btn_set_class.bind("<Leave>", lambda evt: self.lbl_tip.configure(text=''))
        self.btn_del_class.bind("<Enter>", lambda evt: self.lbl_tip.configure(text='删除当前词条的分类'))
        self.btn_del_class.bind("<Leave>", lambda evt: self.lbl_tip.configure(text=''))

    def create_items(self):
        self.btn_set_class.place_forget()  # 使其不显示, 之后可重新place
        self.btn_del_class.place_forget()
        self.lbl_tip.pack_forget()
        Label(self, text='请在下面选择一项: ').grid(row=0, column=0)
        row, col = 1, 0
        for i, e in enumerate(classification):
            if i % 4 == 0 and i != 0:
                col = 0
                row += 1
            Radiobutton(self, text=e, variable=self.custom_class, value=e).grid(row=row, column=col)
            col += 1
        self.btn_ok = Button(self, text="确认", command=self.ok)
        self.btn_ok.place(relx=0.2, rely=0.8, anchor=CENTER)
        self.btn_cancel = Button(self, text="取消", command=self.close)
        self.btn_cancel.place(relx=0.8, rely=0.8, anchor=CENTER)

    def ok(self):
        self.destroy()

    def close(self):
        self.custom_class.set(None)
        self.destroy()


# 导入对话框
class ImportWin(Toplevel):
    def __init__(self, parent, lines, file):
        Toplevel.__init__(self, parent)
        self.parent = parent
        self.count = len(lines)
        self.lines = deque(lines)
        self.value = 0  # 进度条的值
        self.repeats = 0  # 因过去式等形式而重复保存单词的次数
        self.queue_size = self.count
        self.q = queue.Queue()
        self.failed_words = []
        self.to_stop = False
        self.title("正在从 [{0}] 导入词条".format(file))
        self.resizable(False, False)
        MainWin.center_in_scr(self, 500, 150)
        self.transient(parent)
        self.create_contents()
        self.protocol("WM_DELETE_WINDOW", self.stop)

    def portion(self, num):
        if not len(self.lines):
            return None
        data = []
        num = num if num <= len(self.lines) else len(self.lines)
        for _ in range(num):
            data.append(self.lines.popleft())
        return data

    def create_contents(self):
        self.lbl_progress = Label(self, font=self.parent.wryh12)
        self.lbl_progress.grid(row=0, column=0, columnspan=3, pady=15, sticky=W)

        self.pgsbar = Progressbar(self, length=500, mode='determinate')
        self.pgsbar.grid(row=1, column=0, columnspan=2, pady=20)

        self.btn_start = Button(self, text="开始", command=self.start)
        self.btn_start.grid(row=2, column=0, ipadx=8)
        self.btn_stop = Button(self, text="停止", command=self.stop)
        self.btn_stop.grid(row=2, column=1, ipadx=8)
        self.pgsbar["value"] = 0
        self.pgsbar["maximum"] = self.count

    class MyThread(threading.Thread):
        def __init__(self, outer, keyword, work_queue):
            super().__init__()
            self.outer = outer
            self.keyword = keyword
            self.q = work_queue
            self.name = "Thread-" + keyword[0]

        def run(self):
            if self.outer.to_stop:
                return
            result = self.outer.parent.search_simple(self.keyword)
            if result and result[0]:
                if self.outer.to_stop:
                    return
                self.q.put(result)  # 放入一条数据, 元组(WORD, PHONETIC, MEANING, EG)
            else:
                self.outer.failed_words.append(self.keyword)  # 存储搜索查询失败词条

    def start(self):
        self.deiconify()  # 恢复被withdraw()方法隐藏的窗口
        self.btn_start['state'] = "disabled"
        self.lbl_progress['text'] = "请稍候..."

        def search():  # 搜索并创建数据结果
            def get_data(words):
                print('starting get_data')
                threads = []
                for word in words:
                    t = self.MyThread(self, word, self.q)
                    t.daemon = True
                    threads.append(t)
                    t.start()
                for t in threads:
                    t.join()

            while True:
                # 按分块进行搜索
                data = self.portion(75)
                if not data or self.to_stop:
                    break
                get_data(data)

        def save():  # 保存并显示队列中的结果数据
            parent = self.parent
            save_func = parent.dic.save_simple  # 避免多次引用查找属性
            while self.value + len(self.failed_words) != self.count and not self.to_stop:
                print(self.q.qsize(), self.value + len(self.failed_words))
                try:
                    data = self.q.get(timeout=3)  # 取出一条数据, 元组(WORD, PHONETIC, MEANING, EG)
                except queue.Empty:
                    continue
                self.value += 1
                try:
                    self.pgsbar["value"] = self.value
                except _tkinter.TclError:  # 强制停止时因为相关属性丢失不同步的异常
                    print('catch a _tkinter.TclError exception')
                try:
                    self.lbl_progress["text"] = "正在导入: %d/%d  词条: %s" % (self.value, self.count, data[0])
                except _tkinter.TclError:
                    pass
                self.repeats += save_func(data)  # 统计因分词形式而重复保存单词的次数
                try:
                    self.parent.cobbx_item.reset(data[0])
                except _tkinter.TclError:
                    pass
                try:
                    parent.explain_display(([data[0], 1], [data[1], 2], [data[2], 3], [data[3], 4]))
                except _tkinter.TclError:
                    pass
                self.q.task_done()

            if self.value + len(self.failed_words) == self.count:
                print("完成!")
                self.withdraw()
                completed = not len(self.failed_words)  # 无导入失败词条
                self.finish(completed)

        thread_search = threading.Thread(target=search, name='Thread-search')
        thread_search.daemon = True
        thread_search.start()

        thread_save = threading.Thread(target=save, name='Thread-save')
        thread_save.daemon = True
        thread_save.start()  # 不采用join()堵塞主线程, 易造成无响应

    def finish(self, completed):
        print("调用finish()")
        if not completed:  # 存在导入失败的词条
            if messagebox.askokcancel("导入词条", "{0}个词条未成功导入\n{1}个单词被重复保存\n是否重新导入?".
                                      format(len(self.failed_words), self.repeats)):
                self.lines = deque(self.failed_words[:])  # (浅)拷贝列表
                del self.failed_words[:]  # 清空导入失败的词条列表
                self.start()
        else:
            messagebox.showinfo("导入词条", "已成功导入并保存\n全部{0}个非重复词条!".format(self.count-self.repeats))
            # self.destroy()

    def stop(self):
        # print(repr(self.btn_start['state']))
        if str(self.btn_start['state']) == "disabled":  # 须转为字符串
            if messagebox.askokcancel("停止导入", "是否停止导入并关闭此对话框?"):
                self.to_stop = True
                self.destroy()
                messagebox.showinfo("导入停止", "成功导入{0}个词条!".format(self.value))
        else:
            self.to_stop = True
            self.destroy()


class ExportWin(Toplevel):
    pass

