# -*- coding: utf-8 -*-

import sqlite3
import os
import ast
import chardet
import subprocess
import _tkinter
from xlwt import *
from xlrd import *
from collections import OrderedDict
from tkinter import messagebox, filedialog, END
from package import utils, application

sys.setrecursionlimit(10000)  # 设置较大递归深度, 防止对象组合使用时, 调用方法出错
pattern_zh = "[\u4e00-\u9fa5]"  # 中文匹配模板


class TempDB:
    """
    临时内存数据库, 在每次执行search时执行
    """
    def __init__(self, items):
        self.mem = sqlite3.connect(':memory:')  # 每次均把数据存储在内存中
        self.cur_mem = self.mem.cursor()
        self.cur_mem.execute('''CREATE TABLE IF NOT EXISTS DICT
                            (WORD text PRIMARY KEY NOT NULL,
                             PHONETIC text,
                             MEANING text,
                             EG text)''')
        self.record(items)

    def record(self, items):
        self.cur_mem.execute("INSERT INTO DICT VALUES (?, ?, ?, ?)", (items[0], items[1], items[2], items[3]))
        self.mem.commit()

    def get(self):
        # 将可迭代对象('sqlite3.Cursor')转为列表, 取首元素(仅有此一个), 元素为元组
        data = list(self.cur_mem.execute('SELECT WORD, PHONETIC, MEANING, EG FROM DICT'))[0]
        self.mem.close()
        return data  # 元组(WORD, PHONETIC, MEANING, EG)


class MasterDB:  # 主数据库
    def __init__(self):
        db_dict = sqlite3.connect('.\data\Dictionary.db')  # 建立并连接数据库文件,创建数据库链接对象
        cur_db = db_dict.cursor()  # 创建游标对象,用以执行数据库执行语句
        cur_db.execute('''CREATE TABLE IF NOT EXISTS DICT
                                       (WORD text PRIMARY KEY NOT NULL,
                                        PHONETIC text,
                                        MEANING text,
                                        EG text)''')
        # 创建自定义表, 用以指定自定义词义高亮和分类
        cur_db.execute('''CREATE TABLE IF NOT EXISTS CUSTOM
                                       (WORD text PRIMARY KEY NOT NULL,
                                        SPECIFY text DEFAULT '',
                                        CLASSIFY text DEFAULT '')''')

        # 初始化时即进行查询, 并存为列表[(WORD1, MEANING1, SPECIFY1, CLASSIFY1), (WORD2, MEANING2, SPECIFY2, CLASSIFY2),...]
        # 无数据存储时, 该列表为空, 未自定义时, 对应项不存在(即如下列表长度不定)
        datalist = list(cur_db.execute("""
                                      SELECT DICT.WORD, DICT.MEANING, CUSTOM.SPECIFY, CUSTOM.CLASSIFY from DICT, CUSTOM
                                            WHERE DICT.WORD=CUSTOM.WORD"""))
        self.words_meanings_customs = OrderedDict()  # 将数据存储于有序字典
        for item in datalist:
            self.words_meanings_customs[item[0]] = list(item)  # 元组元素值无法更改, 故用列表
        db_dict.close()


class DataBase(MasterDB):  # 数据库
    def __init__(self, app, tmp_db):
        super(DataBase, self).__init__()
        self.app = app
        self.tmp_db = tmp_db
        self.is_displayed = False

    @staticmethod
    def is_exist(self, *args):
        is_saved = False
        if args:
            entry = args[0]
        else:
            entry = self.app.cobbx_item.get()
        entry = entry if entry else self.app.txt_explain.get('1.0', '1.end')
        if entry:  # 获取得entry或已显示
            for item in self.words_meanings_customs:  # 遍历字典, 此处item为key, 即WORD
                if utils.compare_ignore_case(item, entry):  # 不规则形式进行自定义比较
                    is_saved = item  # 若已保存, 直接返回词词条的正确格式
                    self.app.word_statusBar['foreground'] = 'green'
                    self.app.word_statusBar['text'] = application.word_status_saved
                    break
            if not is_saved:
                self.app.word_statusBar['foreground'] = 'red'
                self.app.word_statusBar['text'] = application.word_status_unsaved
        else:  # 搜索框为空
            self.app.word_statusBar['foreground'] = 'black'
            self.app.word_statusBar['text'] = application.word_status_void
        return is_saved

    @staticmethod
    def is_exist_simple(self, word):
        is_saved = False
        for item in self.words_meanings_customs:  # 遍历字典, 此处item为key, 即WORD
            if utils.compare_ignore_case(item, word):  # 不规则形式进行自定义比较
                is_saved = True  # 若已保存, 直接返回词词条的正确格式
                break
        return is_saved

    def get_data(self, word):
        db_dict = sqlite3.connect('.\data\Dictionary.db')  # 建立并连接数据库文件,创建数据库链接对象
        group = []
        word = utils.trans_to_normal(word)  # 获取框内的词条(为字符串),转为正常形式
        self.app.cobbx_item.delete(0, END)
        self.app.cobbx_item.insert(0, word)

        for i in (word, word.lower(), word.upper(), word.capitalize()):  # 考虑大小写匹配问题
            try:
                # 将可迭代对象('sqlite3.Cursor')转为列表, [(word, phon, mean, eg)], 取首元素(仅有此一个)元组
                group = list(db_dict.execute("SELECT WORD, PHONETIC, MEANING, EG FROM DICT WHERE WORD=?", (i, )))[0]
            except IndexError:
                continue
            else:
                break                         # 对于MEANING和EG, 需从TEXT(str)转为list
        db_dict.close()
        return [group[0], 1], [group[1], 2], [eval(group[2]), 3], [eval(group[3]), 4]  # 返回一个元组, 条目与ID组成一元素

    def save(self):
        entry = utils.trans_to_normal(self.app.cobbx_item.get())  # 剔除特殊字符
        if not entry:
            return  # entry为空则直接结束函数

        application.MainWin.search(self.app, entry)
        entry = self.app.cobbx_item.get()  # 刷新为正确的词条格式

        if self.app.search_error:  # 若搜索出错, 结束
            return

        is_saved = DataBase.is_exist(self, entry)
        if is_saved:
            if self.app.win_Dict_exist:  # win_Dict须存在
                self.app.win_Dict.refresh_sel(entry)  # 刷新字典中条目选择
            messagebox.showerror(title="重复操作!", message="该词条已保存!")
            return

        correct, message = utils.validity_check(entry)
        if not correct and not is_saved:  # 若不合法且未保存
            if not messagebox.askyesno("保存警告", message):
                return  # 结束save函数

        if not is_saved:  # 若未保存且未执行搜索显示成功
            if not self.is_displayed:  # 若未成功执行search
                return  # 结束save方法
            if not self.tmp_db:  # 若因意外导致tmp_db不存在, 结束
                print("self.tmp_db==None: ", self.tmp_db is None)
                return
            db_dict = sqlite3.connect('.\data\Dictionary.db')  # 建立并连接数据库文件,创建数据库链接对象
            items = self.tmp_db.get()  # 从临时数据库获取数据, 即当前保存/搜索的词条
            db_dict.execute("INSERT INTO DICT VALUES (?, ?, ?, ?)", (items[0], items[1], items[2], items[3]))
            db_dict.execute("INSERT INTO CUSTOM VALUES (?, ?, ?)", (items[0], '', ''))
            db_dict.commit()
            db_dict.close()
            self.words_meanings_customs[items[0]] = [items[0], items[2], '', '']  # 将保存的词条, 词义, 指定, 分类加入字典中
            if self.app.win_Dict_exist:  # win_Dict须存在
                self.app.win_Dict.refresh([items[0], items[2], '', ''], 'add')  # 刷新字典中条目
                self.app.win_Dict.refresh_sel(entry)  # 刷新字典中条目选择
            word = items[0] if len(items[0]) <= 10 else items[0][:10] + '...'
            self.app.lbl_existinfo['foreground'] = "green"
            self.app.lbl_existinfo['text'] = "成功保存词条: {0}".format(word)  # 在信息标签上显示保存成功提示
            self.app.last_entry = entry
            self.app.word_statusBar['foreground'] = 'green'
            self.app.word_statusBar['text'] = application.word_status_saved
        else:
            if not self.is_displayed:  # 若已保存且未显示在窗口中
                self.app.explain_display(self.get_data(entry))
                if self.app.win_Dict_exist:  # win_Dict须存在
                    self.app.win_Dict.refresh_sel(entry)  # 刷新字典中条目选择
                self.app.lbl_existinfo['text'] = ""  # 重置信息标签, 不显示消息
            messagebox.showerror(title="重复操作!", message="该词条已保存!")

    # @staticmethod
    def save_simple(self, items):
        repeat_word = 0
        db_dict = sqlite3.connect('.\data\Dictionary.db')
        try:
            db_dict.execute("INSERT INTO DICT VALUES (?, ?, ?, ?)", (items[0], items[1], str(items[2]), str(items[3])))
        except sqlite3.IntegrityError:  # 分词形式搜索时被还原为原型, 导致重复保存
            repeat_word += 1
            print("分词型式-重复保存! --", items[0])
        except TypeError:
            print("NoneType!")
        else:
            db_dict.execute("INSERT INTO CUSTOM VALUES (?, ?, ?)", (items[0], '', ''))
            db_dict.commit()
        db_dict.close()
        # 将保存的词条, 词义, 指定, 分类加入字典中. 对于meanings, 需从list转换为str
        self.words_meanings_customs[items[0]] = [items[0], str(items[2]), '', '']
        if self.app.win_Dict_exist:  # win_Dict须存在
            try:
                self.app.win_Dict.refresh([items[0], items[2], '', ''], 'add')  # 刷新字典中条目
                self.app.win_Dict.refresh_sel(items[0])  # 刷新字典中条目选择
            except _tkinter.TclError:
                pass
        # word = items[0] if len(items[0]) <= 10 else items[0][:10] + '...'
        word = items[0]
        self.app.lbl_existinfo['foreground'] = "green"
        self.app.lbl_existinfo['text'] = "成功保存词条: {0}".format(word)  # 在信息标签上显示保存成功提示
        # self.app.last_entry = entry
        self.app.word_statusBar['foreground'] = 'green'
        self.app.word_statusBar['text'] = application.word_status_saved
        return repeat_word

    def remove(self):
        entry = self.app.cobbx_item.get()
        if not entry:
            self.app.lbl_existinfo['foreground'] = "red"
            self.app.lbl_existinfo['text'] = "未指定要移除的词条"  # 在信息标签上显示无法移除提示
            return
        is_saved = DataBase.is_exist(self, entry)
        if not is_saved:  # 若未保存
            self.app.lbl_existinfo['foreground'] = "red"
            self.app.lbl_existinfo['text'] = "未保存的词条 {0}".format(entry)
            return
        if is_saved:  # 若已保存
            db_dict = sqlite3.connect('.\data\Dictionary.db')  # 建立并连接数据库文件,创建数据库链接对象
            word = None
            for i in (entry, entry.lower(), entry.upper(), entry.capitalize()):  # 考虑大小写匹配问题
                group_words = list(db_dict.execute("SELECT WORD, PHONETIC, MEANING, EG FROM DICT WHERE WORD=?", (i, )))
                group_customs = list(db_dict.execute("SELECT SPECIFY, CLASSIFY FROM CUSTOM WHERE WORD=?", (i, )))
                if group_words and group_customs:
                    db_dict.execute("DELETE FROM DICT WHERE WORD=?", (i,))  # 从数据库字典表中删除
                    db_dict.execute("DELETE FROM CUSTOM WHERE WORD=?", (i,))  # 从数据库自定义表中删除
                    db_dict.commit()
                    del self.words_meanings_customs[group_words[0][0]]
                    word = i
                    break
                else:
                    continue
            db_dict.close()

            if self.app.win_Dict_exist:  # win_Dict须存在
                self.app.win_Dict.refresh(word, 'del')
            DataBase.is_exist(self, entry)  # 由于删除后entry未更改, 需再更新保存状态
            self.app.lbl_existinfo['foreground'] = "green"
            self.app.lbl_existinfo['text'] = "成功删除词条: {0}".format(word)

    def empty(self):
        count = len(self.words_meanings_customs)
        if count and messagebox.askyesno("清除全部词条", "是否清除全部{0}个词条?".format(count)):
            db_dict = sqlite3.connect('.\data\Dictionary.db')
            db_dict.execute("DELETE FROM DICT")
            db_dict.execute("DELETE FROM CUSTOM")
            db_dict.commit()
            db_dict.close()
            self.words_meanings_customs.clear()  # 清空列表内容
            self.is_exist(self)  # 刷新保存状态
            if self.app.win_Dict_exist:  # win_Dict须存在
                self.app.win_Dict.refresh(self.app.win_Dict.tree_words.get_children(), 'del')
            if count >= 1500:
                self.vacuum()

    def specify(self):
        """
        为词条高亮指定选定的词义
        """
        if self.app.word_statusBar['text'] == application.word_status_void:  # 无词条
            return
        if self.app.word_statusBar['text'] == application.word_status_unsaved:
            messagebox.showerror(title="错误操作!", message="该词条未保存, 无法指定词义!")
            return
        # 已保存的情况下
        word = self.app.cobbx_item.get()
        if not word:  # 搜索框为空
            word = self.app.get_text_display(1)  # 从文本显示区域获取
            self.app.cobbx_item.set(word)  # 将搜索框恢复显示
        items = utils.get_mean_items(ast.literal_eval(self.words_meanings_customs[word][1]))  # 慎用不安全的eval()
        self.app.create_custom_win(items, word)
        custom = self.app.win_Specify.custom
        db_dict = sqlite3.connect('.\data\Dictionary.db')
        # 删除词义指定
        if self.app.win_Specify.to_del_specify and db_dict.execute("SELECT WORD FROM CUSTOM WHERE WORD=?", (word,)):
            db_dict.execute("UPDATE CUSTOM set SPECIFY='' WHERE WORD=?", (word,))
            db_dict.commit()
            self.words_meanings_customs[word][2] = ''  # 更新字典对象
            self.app.customs_display(word)  # 更新显示
            if self.app.win_Dict_exist:  # win_Dict若存在
                self.app.win_Dict.refresh_sel(word)  # 刷新字典中条目选择
        elif custom and db_dict.execute("SELECT WORD FROM CUSTOM WHERE WORD=?", (word, )):
            db_dict.execute("UPDATE CUSTOM set SPECIFY=? WHERE WORD=?", (custom, word))
            db_dict.commit()
            self.words_meanings_customs[word][2] = custom  # 更新字典对象
            if self.app.get_text_display(1) == word:  # 若已经显示内容
                self.app.customs_display(word)  # 更新显示
            elif self.app.get_text_display(1) != word:  # 未显示内容则刷新显示
                self.app.explain_display(self.get_data(word))
            if self.app.win_Dict_exist:  # win_Dict须存在
                self.app.win_Dict.refresh_sel(word)  # 刷新字典中条目选择
        db_dict.close()

    def classify(self):
        if self.app.word_statusBar['text'] == application.word_status_void:  # 无词条
            return
        if self.app.word_statusBar['text'] == application.word_status_unsaved:
            messagebox.showerror(title="错误操作!", message="该词条未保存, 无法进行分类!")
            return
        # 已保存的情况下
        word = self.app.cobbx_item.get()
        if not word:
            word = self.app.get_text_display(1)  # 从文本显示区域获取
            self.app.cobbx_item.set(word)
        self.app.create_class_win(word)
        item = self.app.win_Classify.custom_class.get()
        db_dict = sqlite3.connect('.\data\Dictionary.db')
        # 删除分类
        if self.app.win_Classify.to_del_class and db_dict.execute("SELECT WORD FROM CUSTOM WHERE WORD=?", (word, )):
            db_dict.execute("UPDATE CUSTOM set CLASSIFY='' WHERE WORD=?", (word, ))
            db_dict.commit()
            self.words_meanings_customs[word][3] = ''  # 更新字典对象
            self.app.customs_display(word)  # 更新显示
            if self.app.win_Dict_exist:  # win_Dict须存在
                self.app.win_Dict.refresh_sel(word)  # 刷新字典中条目选择
        # 设置分类
        else:
            if item != 'None' and db_dict.execute("SELECT WORD FROM CUSTOM WHERE WORD=?", (word, )):
                db_dict.execute("UPDATE CUSTOM set CLASSIFY=? WHERE WORD=?", (item, word))
                db_dict.commit()
                self.words_meanings_customs[word][3] = item  # 更新字典
            if self.app.get_text_display(1) == word and item != 'None':  # 若已经显示内容
                self.app.customs_display(word)  # 更新显示
            elif self.app.get_text_display(1) != word and item != 'None':  # 未显示内容则刷新显示
                self.app.explain_display(self.get_data(word))
            if self.app.win_Dict_exist:  # win_Dict须存在
                self.app.win_Dict.refresh_sel(word)  # 刷新字典中条目选择
        db_dict.close()
        if self.app.win_Dict_exist:  # win_Dict须存在
            self.app.win_Dict.refresh(self.words_meanings_customs[word], 'classify')  # 刷新字典显示

    def impt(self):
        # print("导入: ", end=" ")
        f_import = filedialog.askopenfile(mode='rb', defaultextension=".txt", initialdir=os.getcwd() + '\data',
                                          filetypes=[('数据库文件', '.db'), ('文本文档', '.txt'), ('Excel表格文档', '.xls')],
                                          initialfile='Dictionary', title="导入字典文件")
        if f_import:  # 确保文件打开成功
            if os.path.splitext(f_import.name)[1] == '.txt':  # 导入的文本文件
                encoding = chardet.detect(f_import.read())['encoding']
                f_import.seek(0, 0)  # 重置指针位置
                items = [line.decode(encoding).split("|", 1)[0]
                         for line in f_import.readlines() if line]  # 忽略空行, 以"|"分隔
                items = [word for word in items if not DataBase.is_exist_simple(self, word)]  # 确保未保存
                if len(items) > 0:
                    if messagebox.askokcancel(title="导入词条", message="文件中共有{0}个未保存单词, 是否导入".format(len(items))):
                        self.app.create_impt_win(items, os.path.basename(f_import.name))
                else:
                    messagebox.showwarning(title="导入词条", message="该文件中不存在未保存单词!")

            if os.path.splitext(f_import.name)[1] == '.xls':  # 导入的Excel表格文件
                print("表格文件!")
                rb = open_workbook(f_import.name, encoding_override='utf-8')
                table = rb.sheet_by_name("Dictionary")
                for i in range(table.nrows):
                    print(table.cell_value(i, 0), table.cell_value(i, 1))

            if os.path.splitext(f_import.name)[1] == '.db':  # 导入的数据库文件
                print("数据库文件!")
            f_import.close()

    def expt(self):
        print("导出")
        # 另存为, 并返回打开的文件
        group = self.words_meanings_customs.values()
        f_export = filedialog.asksaveasfile(mode='w', defaultextension=".txt", initialdir=os.getcwd() + '\data',
                                            filetypes=[('文本文档', '.txt'), ('Excel表格文档', '.xls')],
                                            initialfile='Dictionary', title="导出字典文件")
        if f_export:  # 确保文件打开成功
            if os.path.splitext(f_export.name)[1] == '.txt':  # 导出为文本文件
                for item in group:
                    f_export.write("{0}|{1}\n".format(item[0], item[1]))
                    # f_export.write("{0:-<15}{1}\n".format(item[0], item[1]))

            if os.path.splitext(f_export.name)[1] == '.xls':  # 导出为Excel表格文件
                wb = Workbook(encoding='utf-8')
                ws = wb.add_sheet("Dictionary")
                for index, item in enumerate(group):
                    ws.write(index, 0, item[0])
                    # item[1]为字符串形式的列表, 通过misc简化得列表, 只能以字符串形式写入xls
                    ws.write(index, 1, str(utils.get_mean_items(ast.literal_eval(item[1]))))
                wb.save(f_export.name)
            f_export.close()

    # 清理数据库文件空闲空间
    def vacuum(self):
        msg = "删除词条后, 数据库文件中存在空闲空间, 可释放该磁盘空间, 但可能会降低一定的效率, 是否继续?"
        if messagebox.askyesno("清空数据库", message=msg):
            db_dict = sqlite3.connect('.\data\Dictionary.db')
            db_dict.execute("VACUUM;")
            db_dict.commit()
            db_dict.close()
            messagebox.showinfo(title="操作成功", message="空间清理完成!")
        print("清理数据库空闲空间")

    @staticmethod
    def open_in_explorer():
        subprocess.Popen('explorer.exe /select,"{}"'.format(os.getcwd() + '\data\Dictionary.db'))

