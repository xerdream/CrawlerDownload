import requests
import sys
import os
import re
from .mException import UrlCodeError


class cmdProgressBar():  # 进度条
    def __init__(self, total: int = 0, num: int = 0) -> None:
        self.total = total
        self.num = num

    def clear(self):
        self.num = 0
        self.show()

    def update(self, size: int):
        self.num += size
        self.show()

    def set(self, total: int, num: int = 0, style=1):
        self.total = total
        self.num = num
        self.show()

    def show(self):
        style = self.stytle1
        style()

    def stytle1(self):
        rate = 100 * self.num // self.total
        nr = '\r %5d/%5d \t%3d%%' % (self.num, self.total, rate)
        sys.stdout.write(nr)
        sys.stdout.flush


class wget:

    def __init__(self, config={}, progressbar=cmdProgressBar(), print_log=print):
        self.config = {
            'block': int(config['block'] if 'block' in config else 1024 * 1024)
        }
        self.total = 0
        self.size = 0
        self.filename = ''
        self.progressbar = progressbar
        self.print_log = print_log

    def set_progressbar(self, progressbar):
        self.progressbar = progressbar

    def touch(self, filename):
        """创建文件"""
        with open(filename, 'w'):
            pass

    def remove_nonchars(self, name):
        """过滤异常字符"""
        (name, _) = re.subn(r'[\:\*\?\"\<\>\|]', '', name)
        return name

    def support_continue(self, url, headers):
        """判断是否支持断点续传，并获得文件大小"""
        headers['Range'] = 'bytes=0-4'
        try:
            r = requests.get(url, headers=headers)
            crange = r.headers.get('content-range', 0)
            self.total = int(re.match(r'^bytes 0-4/(\d+)$', crange).group(1))
            r.close()
            return True
        except Exception:
            pass
        try:
            self.total = int(r.headers.get('content-length', 0))
            r.close()
        except Exception:
            self.total = 0
        return False

    def format_size(self, size=None):
        size = self.total if size is None else size

        result = {"value": None, "unit": "None"}
        if self.total > 1073741824:
            result["value"] = size / 1073741824
            result["unit"] = "GB"
        elif self.total > 1048576:
            result["value"] = size / 1048576
            result["unit"] = "MB"
        elif self.total > 1024:
            result["value"] = size / 1024
            result["unit"] = "KB"
        elif self.total > 0:
            result["value"] = size
            result["unit"] = "B"
        return result

    def download(self, url, filename, headers={}):
        finished = False
        block = self.config['block']
        local_filename = self.remove_nonchars(filename)
        tmp_filename = local_filename + '.downtmp'
        size = self.size
        if self.support_continue(url, headers=headers):  # 支持断点续传
            try:
                with open(tmp_filename, 'rb') as fin:
                    self.size = int(fin.read())
                    size = self.size + 1  # 上次中断的位置
            except Exception:
                self.touch(tmp_filename)  # 没有文件则创建
            finally:
                headers['Range'] = "bytes=%d-" % (self.size)  # 设置断点下载位置
        else:
            self.touch(tmp_filename)  # 不支持则创建文件
            self.touch(local_filename)
        r = requests.get(url, stream=True, headers=headers)
        if r.status_code != 200 and r.status_code != 206:
            self.print_log(f"[py_wget]无法访问网址{url}")
            raise UrlCodeError(r.status_code)
        format_size = self.format_size()
        self.print_log("Size: %.2lf %s" % (format_size["value"], format_size["unit"]))

        with open(local_filename, 'ab+') as f:
            f.seek(self.size)  # 定位到上次下载
            f.truncate()  # 截断，防止后面有脏数据
            try:
                if self.size != 0:
                    format_size = self.format_size(self.size)
                    self.print_log("Start from the last download: %d %s" % (format_size["value"], format_size["unit"]))
                self.progressbar.set(self.total, size)  # 设置进度条

                for chunk in r.iter_content(chunk_size=block):  # 分块下载
                    if chunk:
                        f.write(chunk)
                        size += len(chunk)
                        f.flush()
                    self.progressbar.update(block)  # 进度条滚动
                finished = True
                os.remove(tmp_filename)  # 下载完成，删除中间文件

            except Exception:
                # import traceback
                # print traceback.print_exc()
                self.print_log("\nDownload pause.\n")
            finally:
                r.close()
                if not finished:  # 没结束则写入下载的进度
                    with open(tmp_filename, 'w+') as ftmp:
                        ftmp.write(str(size))
