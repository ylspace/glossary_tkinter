from tkinter import *
from tkinter import messagebox
from package import database


class MainMenu(Menu):
    def __init__(self, master):  # master为app对象, self为app.menuBar
        super().__init__(master)
        self.master = master
        
    def set(self):
        master = self.master
        master.editMenu = Menu(master.menuBar, tearoff=0)  # 不可脱离
        master.dictMenu = Menu(master.menuBar, tearoff=0)
        master.prefMenu = Menu(master.menuBar, tearoff=0)
        master.helpMenu = Menu(master.menuBar, tearoff=0)

        self.add_cascade(label="编辑", menu=self.master.editMenu)
        master.editMenu.add_command(label="保存", command=lambda: master.dict_handle("save"))
        master.editMenu.add_command(label="移除", command=lambda: master.dict_handle("remove"))
        master.editMenu.add_command(label="指定...", command=lambda: master.dict_handle("specify"))
        master.editMenu.add_command(label="分类...", command=lambda: master.dict_handle("classify"))

        self.add_cascade(label="词典", menu=master.dictMenu)
        master.dictMenu.add_command(label="导入...", command=lambda: master.dict_handle("impt"))
        master.dictMenu.add_command(label="导出...", command=lambda: master.dict_handle("expt"))
        master.cleanMenu = Menu(master.dictMenu, tearoff=0)
        master.cleanMenu.add_command(label="全部已存词条", command=lambda: master.dict_handle("empty"))
        master.cleanMenu.add_command(label="数据库空闲空间", command=lambda: master.dict_handle("vacuum"))
        master.cleanMenu.add_command(label="字典数据库文件")
        master.dictMenu.add_cascade(label="清理", menu=master.cleanMenu)
        master.dictMenu.add_command(label="打开...", command=master.create_dict_win)
        master.dictMenu.add_command(label="在文件浏览器中打开...", command=database.DataBase.open_in_explorer)

        self.add_cascade(label="设置", menu=master.prefMenu)
        master.prefMenu.add_command(label="设置", command=lambda: print("设置二级菜单!"))
        master.languageMenu = Menu(master.prefMenu, tearoff=0)
        master.languageMenu.add_command(label="简体中文")
        master.languageMenu.add_command(label="繁体中文")
        master.languageMenu.add_command(label="English")
        master.prefMenu.add_cascade(label="语言", menu=master.languageMenu)
        master.prefMenu.add_checkbutton(label="选框")
        master.prefMenu.add_radiobutton(label="选项")

        master.prefMenu.add_command(label="快捷键", command=lambda: print("快捷键设置!"))

        self.add_cascade(label="帮助", menu=master.helpMenu)
        master.helpMenu.add_command(label="帮助...", command=lambda: print("帮助功能!"))
        master.helpMenu.add_command(label="关于...", command=MainMenu.about)

    @staticmethod
    def about():
        messagebox.showinfo("关于本程序", "本程序是一个英语单词查询应用, 支持本地保存, 自定义词义和分类等功能...")
