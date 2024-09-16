import re
import os
import sys
import tkinter
import tkinter.ttk as ttk

from typing import Dict, List
from download import (
    down_bilibili as bb,
    down_m3u8 as mm,
    down_youtube as yt,
    down_twitch as tt,
)

from config.download_config import DownloadConfig


class ProgressBar:
    def __init__(self, bar: ttk.Progressbar, total: int = 0, num: int = 0) -> None:
        self.bar = bar
        self.total = total
        self.num = num
        self.show()

    def clear(self):
        self.num = 0
        self.show()

    def update(self, size: int):
        self.num += size
        self.show()

    def set(self, total: int, num: int = 0):
        self.total = total
        self.num = num
        self.show()

    def show(self):
        self.bar["maximum"] = self.total
        self.bar["value"] = self.num
        self.bar.update()


class common_GUI:
    def __init__(self) -> None:
        # 大小
        self.size_heigh = 0.07  # 基础相对高度
        self.size_lable_width = 0.2  # 输入框描述相对宽度
        self.size_text_width = 1 - self.size_lable_width  # 输入框相对宽度
        self.size_space = 0.02  # 上下间隔
        self.rely_area = 0  # 初始y偏移

        self.lable_text: List[str] = []  # 输入框描述
        self.lable_: List[ttk.Label] = []  # 描述实例
        self.entry_: List[ttk.Entry] = []  # 输入框实例
        self.var_save: List[tkinter.BooleanVar] = []
        self.checkbutton_text: List[str] = []
        self.checkbutton_: List[ttk.Checkbutton] = []  # 选择框实例

    def _rely_next(self, heigh):
        """上下间隔设置"""
        self.rely_area += heigh

    def print_log(self, args):
        """日志打印"""
        if isinstance(args, Exception):
            args = args.__str__()
        self.text_log.insert(tkinter.END, args)
        self.text_log.insert(tkinter.END, "\n")
        self.text_log.see(tkinter.END)
        self.text_log.update()

    def _build_lable_text(self, init_window):
        """输入框默认构建方法"""
        for i in range(len(self.lable_text)):
            self.lable_.append(ttk.Label(init_window, text=self.lable_text[i]))
            self.lable_[i].place(
                relheight=self.size_heigh,
                relwidth=self.size_lable_width,
                rely=self.rely_area,
            )
            self.entry_.append(ttk.Entry(init_window))
            self.entry_[i].place(
                relheight=self.size_heigh,
                relwidth=self.size_text_width,
                relx=self.size_lable_width,
                rely=self.rely_area,
            )
            self._rely_next(self.size_heigh + self.size_space)

    def _build_checkbutton_text(self, init_window):
        """选择框默认构建方法"""
        temp_numb = len(self.checkbutton_text)  # 按钮个数
        temp_relx = 0
        temp_relwidth = 0.8 / temp_numb  # 所有按钮宽度占比0.8
        temp_blank = 0.2 / (temp_numb - 1)  # 所有按钮间距占比0.2

        for i in range(temp_numb):
            self.var_save.append(tkinter.BooleanVar())
            self.checkbutton_.append(
                ttk.Checkbutton(
                    init_window,
                    text=self.checkbutton_text[i],
                    variable=self.var_save[i],
                )
            )
            self.checkbutton_[i].place(
                relheight=self.size_heigh,
                relwidth=temp_relwidth,
                relx=temp_relx,
                rely=self.rely_area,
            )
            temp_relx += temp_blank + temp_relwidth

    def _build_text_log(self, init_window):
        """
        日志框默认构建方法

        height_rate : 日志高度比例size_heigh的倍数
        """
        self.text_log = tkinter.Text(init_window)
        # self.text_log.place(relheight=self.size_heigh * height_rate, relwidth=1, rely=self.rely_area)
        self.text_log.place(
            relheight=0.95 - self.rely_area, relwidth=1, rely=self.rely_area
        )

    def _build_progressbar(self, init_window):
        """进度条默认构建方法"""
        self.progressbar = ttk.Progressbar(init_window)
        self.progressbar.place(
            relheight=self.size_heigh / 2, relwidth=1, rely=1 - self.size_heigh / 2
        )


class CD_GUI:
    def __init__(self, init_window: tkinter.Tk):
        self.init_window = init_window
        self.init_window.protocol("WM_DELETE_WINDOW", self.before_exit)

        init_window.title("视频下载工具V1.0")
        # 位置设置
        self.place_frame_x = {"relx": 0.1, "relwidth": 0.8}  # 子窗口横向范围
        self.place_button_select_y = {"rely": 0.1, "relheight": 0.8}  # 按钮相对高度
        self.place_frame_button_rely = 0.02  # 按钮窗口相对位置y
        self.place_frame_button_relheight = 0.07  # 按钮窗口相对高度
        self.place_lable_rely = (
            self.place_frame_button_rely + self.place_frame_button_relheight
        )  # 子窗口描述y轴位置，根据按钮位置与高度计算得出
        self.place_lable_relheight = 0.1  # 子窗口描述高度
        self.place_frame_area_rely = (
            self.place_lable_rely + self.place_lable_relheight
        )  # 子窗口位置，根据其描述位置与高度计算得出
        # 按钮列表，可在此直接增加
        self.button_select_config = [
            {"text": "bilibili", "command": self.show_bilibili},
            {"text": "m3u8", "command": self.show_m3u8},
            {"text": "youtube", "command": self.show_youtube},
            {"text": "twitch", "command": self.show_twitch},
            {"text": "setting", "command": self.show_setting},
        ]
        # 实例字典
        self.button_select: Dict[str, ttk.Button] = {}  # 按钮
        self.ui = {}
        self.frame_area: Dict[str, ttk.Frame] = {}  # 子窗口

        # 风格
        # self.framestyle = ttk.Style()
        # self.framestyle.configure("1.TFrame", background='red')
        # 按钮frame
        self.frame_button_select = ttk.Frame(init_window)
        self.frame_button_select.place(
            self.place_frame_x,
            rely=self.place_frame_button_rely,
            relheight=self.place_frame_button_relheight,
        )
        # 当前显示的子窗口
        self.current_show: str = None
        # 设置当前子页面标题
        self.lable_area = ttk.Label(init_window, anchor="center")
        self.lable_area.place(
            self.place_frame_x,
            rely=self.place_lable_rely,
            relheight=self.place_lable_relheight,
        )
        # 设置切换按钮
        temp_numb = len(self.button_select_config)  # 按钮个数
        temp_relx = 0
        temp_relwidth = 0.8 / temp_numb  # 所有按钮宽度占比0.8
        temp_blank = 0.2 / (temp_numb - 1)  # 所有按钮间距占比0.2

        # 遍历按钮列表，设置按钮与frame
        for i in range(temp_numb):
            # 设置按钮布局
            item = self.button_select_config[i]
            self.button_select[item["text"]] = ttk.Button(
                self.frame_button_select, text=item["text"], command=item["command"]
            )
            self.button_select[item["text"]].place(
                self.place_button_select_y, relx=temp_relx, relwidth=temp_relwidth
            )
            temp_relx += temp_blank + temp_relwidth
            # 初始化frame
            self.frame_area[item["text"]] = ttk.Frame(init_window)

        # 加载配置，默认显示
        self.config = DownloadConfig()
        self.show_youtube()

    def show_bilibili(self):
        """显示bilibili子窗口"""
        name = "bilibili"
        ui_class = bilibili_GUI
        self.show_frame_area(name, ui_class)

    def show_youtube(self):
        """显示youtube子窗口"""
        name = "youtube"
        ui_class = youtube_GUI
        self.show_frame_area(name, ui_class)

    def show_twitch(self):
        """显示twitch子窗口"""
        name = "twitch"
        ui_class = twitch_GUI
        self.show_frame_area(name, ui_class)

    def show_m3u8(self):
        """显示m3u8子窗口"""
        name = "m3u8"
        ui_class = m3u8_GUI
        self.show_frame_area(name, ui_class)

    def show_setting(self):
        """显示设置子窗口"""
        name = "setting"
        ui_class = setting_GUI
        self.show_frame_area(name, ui_class)

    def show_frame_area(self, name: str, ui_class: common_GUI):
        if name not in self.ui:
            self.ui[name] = ui_class(self.frame_area[name], self.config)

        self.lable_area.config(text=name)

        if self.current_show is not None:
            self.frame_area[self.current_show].place_forget()
            self.button_select[self.current_show]["state"] = tkinter.NORMAL
        self.current_show = name
        self.frame_area[self.current_show].place(
            self.place_frame_x,
            rely=self.place_frame_area_rely,
            relheight=0.99 - self.place_frame_area_rely,
        )  # 0.99防止进度条贴地
        self.button_select[self.current_show]["state"] = tkinter.DISABLED

    def before_exit(self):
        # 销毁窗口前操作
        try:
            self.config.save_config()
        finally:
            self.init_window.destroy()
            sys.exit()


class setting_GUI(common_GUI):
    def __init__(self, init_window, config: DownloadConfig):
        super().__init__()
        self.config = config
        self.lable_text: List[str] = ["保存路径:", "代理(socks5://):"]  # 输入框描述
        # self.checkbutton_text: List[str] = ["保存音频", "保存视频", "保存无声视频"]
        # 设置输入框与描述
        self._build_lable_text(init_window)
        self._rely_next(self.size_space * 3)
        # 设置勾选框
        # self._build_checkbutton_text(init_window)
        # self.var_save[0].set(True)
        self._rely_next(self.size_heigh + self.size_space * 15)

        # 开始按钮
        self.button_conversion = ttk.Button(
            init_window, text="打开文件夹", command=self.opendir
        )
        self.button_conversion.place(
            relheight=self.size_heigh, relwidth=0.15, relx=0.85, rely=self.rely_area
        )

        self.button_start = ttk.Button(init_window, text="保存", command=self.save)
        self.button_start.place(
            relheight=self.size_heigh, relwidth=0.2, relx=0.4, rely=self.rely_area
        )
        # 日志输出 text_log
        self._rely_next(self.size_heigh + self.size_space * 2)
        self._build_text_log(init_window)

        # 载入配置信息
        self.entry_[0].insert(0, self.config.save_path)
        self.entry_[1].insert(0, self.config.proxy)

    def save(self):
        """保存配置"""
        self.config.save_path = self.entry_[0].get()
        self.config.proxy = self.entry_[1].get()
        self.config.save_config()
        self.print_log("保存成功")

    def opendir(self):
        open_path = os.getcwd() + '\\' + self.config.save_path
        if not os.path.exists(open_path):
            os.mkdir(open_path)
        os.startfile(open_path)


class bilibili_GUI(common_GUI):
    def __init__(self, init_window, config: DownloadConfig):
        super().__init__()
        self.config = config
        self.lable_text: List[str] = ["视频地址:", "Cookie:", "保存路径:"]  # 输入框描述
        self.checkbutton_text: List[str] = ["保存音频", "保存视频", "保存无声视频"]
        # 设置输入框与描述
        self._build_lable_text(init_window)
        self._rely_next(self.size_space * 3)
        # 设置勾选框
        self._build_checkbutton_text(init_window)
        self.var_save[0].set(True)
        self._rely_next(self.size_heigh + self.size_space * 2)

        self.button_start = ttk.Button(init_window, text="开始下载", command=self.start)
        self.button_start.place(
            relheight=self.size_heigh, relwidth=0.2, relx=0.4, rely=self.rely_area
        )
        # 日志输出 text_log
        self._rely_next(self.size_heigh + self.size_space * 2)
        self._build_text_log(init_window)
        # 进度条 progressbar
        self._build_progressbar(init_window)

        self.__init_bb()

    def __init_bb(self):
        """初始化参数，设置进度条和日志输出"""
        bb.progressbar = ProgressBar(self.progressbar)
        bb.print_log = self.print_log

        self.entry_[1].insert(0, self.config.bilibili_cookies)
        self.entry_[2].insert(0, self.config.save_path)

    def start(self):
        """开始"""
        bb.url = self.entry_[0].get()
        bb.cookies = self.entry_[1].get()
        bb.path = self.entry_[2].get()
        # 简单的输入合法性判断
        if bb.url == "":
            self.print_log("请输入网址！")
            return
        if bb.cookies == "":
            self.print_log("请输入Cookies!")
            return
        self.config.bilibili_cookies = bb.cookies
        self.config.save_path = bb.path
        self.button_start["state"] = tkinter.DISABLED
        # 根据勾选框下载
        bb.main_invoked_by_ui(
            self.var_save[0].get(), self.var_save[1].get(), self.var_save[2].get()
        )
        self.button_start["state"] = tkinter.NORMAL


class youtube_GUI(common_GUI):
    def __init__(self, init_window, config: DownloadConfig):
        super().__init__()
        self.config = config
        self.lable_text: list[str] = ["视频地址:", "视频名称(可选):", "保存路径:"]
        self.checkbutton_text: list[str] = [
            "保存音频",
            "保存视频",
            "保存无声视频",
            "使用yd-dlp下载",
        ]

        self._build_lable_text(init_window)
        self._rely_next(self.size_space * 3)
        # 设置勾选框
        self._build_checkbutton_text(init_window)
        self.var_save[0].set(True)
        self.var_save[3].set(True)
        self._rely_next(self.size_heigh + self.size_space * 2)
        
        self.button_start = ttk.Button(init_window, text="开始下载", command=self.start)
        self.button_start.place(
            relheight=self.size_heigh, relwidth=0.2, relx=0.4, rely=self.rely_area
        )
        # 日志输出 text_log
        self._rely_next(self.size_heigh + self.size_space * 2)
        self._build_text_log(init_window)
        # 进度条 progressbar
        self._build_progressbar(init_window)

        self.__init_yt()

    def __init_yt(self):
        yt.progressbar = ProgressBar(self.progressbar)
        yt.text_log = self.print_log
        yt.proxy = self.config.proxy

        self.entry_[2].insert(0, self.config.save_path)

    def start(self):
        yt.url = self.entry_[0].get()
        yt.name = self.entry_[1].get()
        yt.path = self.entry_[2].get()

        if yt.url == "":
            self.print_log("请输入网址！")
            return
        elif not isURL(yt.url):
            self.print_log("请输入正确网址！")
            return

        self.config.save_path = yt.path
        self.button_start["state"] = tkinter.DISABLED
        yt.main_invoked_by_ui(
            self.var_save[0].get(),
            self.var_save[1].get(),
            self.var_save[2].get(),
            self.var_save[3].get(),
        )
        self.button_start["state"] = tkinter.NORMAL


class m3u8_GUI(common_GUI):
    def __init__(self, init_window, config: DownloadConfig):
        super().__init__()
        self.config = config
        self.lable_text: list[str] = [
            "视频名称:",
            "m3u8地址:",
            "保存路径",
        ]
        self.checkbutton_text: list[str] = ["保存音频", "保存视频", "保存ts视频"]
        self._build_lable_text(init_window)
        self._rely_next(self.size_space * 2)
        # 设置勾选框
        self._build_checkbutton_text(init_window)
        self.var_save[1].set(True)
        # 额外的按钮设置
        self._rely_next(self.size_heigh + self.size_space * 2)
        self.button_conversion = ttk.Button(
            init_window, text="网址解密", command=self.urldecrypt
        )
        self.button_conversion.place(
            relheight=self.size_heigh, relwidth=0.1, relx=0.0, rely=self.rely_area
        )
        self.button_start = ttk.Button(init_window, text="开始下载", command=self.start)
        self.button_start.place(
            relheight=self.size_heigh, relwidth=0.2, relx=0.4, rely=self.rely_area
        )
        self.button_QRscan = ttk.Button(
            init_window, text="二维码识别", command=self.qrscan
        )
        self.button_QRscan.place(
            relheight=self.size_heigh, relwidth=0.15, relx=0.11, rely=self.rely_area
        )
        # 日志输出 text_log
        self._rely_next(self.size_heigh + self.size_space * 2)
        self._build_text_log(init_window)
        # 进度条 progressbar
        self._build_progressbar(init_window)

        self.__init_mm()

    def __init_mm(self):
        self.entry_[2].insert(0, self.config.save_path)

        mm.progressbar = ProgressBar(self.progressbar)
        mm.print_log = self.print_log

    def start(self):
        """开始"""
        mm.name = self.entry_[0].get()
        mm.url_m3u8 = self.entry_[1].get()
        mm.path = self.entry_[2].get()
        mm.path_m3u8 = mm.path + "m3u8"
        # 简单的合法性判断
        if mm.name == "":
            self.print_log("请输入文件名称！")
            return
        elif not isURL(mm.url_m3u8):
            self.print_log("请输入正确m3u8网址！")
            return
        if mm.url_ != "" and not isURL(mm.url_):
            self.print_log("请输入正确m3u8前缀网址！")
            return
        self.config.save_path = mm.path
        self.button_start["state"] = tkinter.DISABLED
        mm.main_invoked_by_ui(
            self.var_save[0].get(), self.var_save[1].get(), self.var_save[2].get()
        )
        self.button_start["state"] = tkinter.NORMAL

    def qrscan(self):
        """调用二维码扫描"""
        self.button_QRscan["state"] = tkinter.DISABLED
        try:
            url_m3u8 = mm.qrcode_invoked_by_ui()
            if url_m3u8 is not None:
                # 更新url
                self.entry_[1].delete(0, tkinter.END)
                self.entry_[1].insert(0, url_m3u8)
        finally:
            self.button_QRscan["state"] = tkinter.NORMAL

    def urldecrypt(self):
        """url的解密转换"""
        self.button_conversion["state"] = tkinter.DISABLED
        url = self.entry_[1].get()
        url_m3u8 = mm.url_conversion(url)
        # 更新url
        if url_m3u8 is not None:
            self.entry_[1].delete(0, tkinter.END)
            self.entry_[1].insert(0, url_m3u8)
        self.button_conversion["state"] = tkinter.NORMAL


class twitch_GUI(common_GUI):
    def __init__(self, init_window, config: DownloadConfig):
        super().__init__()
        self.config = config
        self.lable_text: list[str] = ["视频地址:", "视频名称:", "保存路径:"]
        self.checkbutton_text: list[str] = [
            "保存音频",
            "保存视频",
            "保存ts视频",
            "协程下载",
        ]
        # 输入框
        self._build_lable_text(init_window)
        self._rely_next(self.size_space * 3)
        # 设置勾选框
        self._build_checkbutton_text(init_window)
        self.var_save[1].set(True)
        self.var_save[3].set(True)
        # 额外的按钮设置
        self._rely_next(self.size_heigh + self.size_space * 2)
        self.button_start = ttk.Button(init_window, text="开始下载", command=self.start)
        self.button_start.place(
            relheight=self.size_heigh, relwidth=0.2, relx=0.4, rely=self.rely_area
        )
        # 日志输出 text_log
        self._rely_next(self.size_heigh + self.size_space * 2)
        self._build_text_log(init_window)
        # 进度条 progressbar
        self._build_progressbar(init_window)

        self.__init_mm()

    def __init_mm(self):
        self.entry_[2].insert(0, self.config.save_path)

        tt.progressbar = ProgressBar(self.progressbar)
        tt.proxy = self.config.proxy
        tt.print_log = self.print_log

    def start(self):
        """开始"""
        tt.url = self.entry_[0].get()
        tt.name = self.entry_[1].get()
        tt.path = self.entry_[2].get()
        tt.path_m3u8 = tt.path + "m3u8"
        # 简单的合法性判断
        if not isURL(tt.url):
            self.print_log("请输入正确网址！")
            return
        self.config.save_path = tt.path
        self.button_start["state"] = tkinter.DISABLED
        tt.main_invoked_by_ui(
            self.var_save[0].get(),
            self.var_save[1].get(),
            self.var_save[2].get(),
            self.var_save[3].get(),
        )
        self.button_start["state"] = tkinter.NORMAL


def isURL(string: str):
    """判断是否是网址"""
    temp = re.search(
        r"(https|http|ftp)://([\w-]+\.)+[\w-]+(/[./?%&=\w-]*)(:[0-9]{1,5})?(/[S]*)?",
        string,
    )
    return temp is not None
