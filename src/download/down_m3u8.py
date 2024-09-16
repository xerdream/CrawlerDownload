import os
import re
import sys
import json
import base64
import urllib
import asyncio
import aiohttp
import aiofiles
import requests

from PIL import ImageGrab, Image
from pyzbar import pyzbar
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from threading import Thread

from aiohttp.client_reqrep import ClientResponse

from .Util import UrlCodeError, URLError
from .Util import DecryptM3u8Url

# os.environ["http_proxy"] = "http://127.0.0.1:11451"
# os.environ["https_proxy"] = "http://127.0.0.1:11451"
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
}
path = "download"
name = "default"
url_m3u8 = ""
url_ = ""
downloading = False

print_log = print


class ProgressBar:
    def __init__(self, total: int = 0, num: int = 0) -> None:
        self.total = total
        self.num = num

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

    def show(self):  # 进度条
        try:
            rate = self.num / self.total
            rate_num = int(rate * 100)
        except Exception:
            rate_num = 0

        nr = "\r %3d/%3d %3d%%" % (
            self.num,
            self.total,
            rate_num,
        )
        sys.stdout.write(nr)
        sys.stdout.flush


progressbar = ProgressBar()


def main_invoked_by_ui(save_audio, save_mp4, save_ts):
    global downloading
    if downloading:
        print_log("已经在下载了！")
    else:
        downloading = True
        t = Thread(target=main, args=(save_audio, save_mp4, save_ts))
        t.start()


def main(save_audio, save_mp4, save_ts):
    if not save_audio and not save_mp4 and not save_ts:
        print_log("请选择要保存的文件")
        return
    if os.path.exists(f"{path}/{name}.ts"):  # 判断是否需要开始下载
        print_log(f"ts文件已存在:{path}/{name}.ts")
        return
    print_log("*" * 50)
    if __name__ != "__main__":
        loop1 = asyncio.new_event_loop()
        asyncio.set_event_loop(loop1)
    global download
    download = M3u8Download(
        path,
        name,
        url_=url_,
        headers=headers,
        progressbar=progressbar,
        print_log=print_log,
    )
    processvideo = ProcessVideo(path, name)
    decrypt = Decrypt(path, name)

    download.get_m3u8(url_m3u8)
    # 获取ts文件数量
    # download.total_ts()
    download.download_ts()
    # 校验ts是否完整 + 补充下载
    download.solve_lost()
    # 检查是否需要解密
    descrypt_path = decrypt.decrypt_ts()

    # 合并文件
    # 合并方案a
    processvideo.merge_paln_a(descrypt_path)

    if save_mp4:
        print_log("转换MP4中...")
        processvideo.ts_to_mp4()
        print_log(f"MP4保存位置{path}{name}.mp4")
    if save_audio:
        print_log("生成音频中...")
        processvideo.mp4_to_m4a()
        if not save_mp4:
            os.remove(f"{path}/{name}.mp4")
        print_log(f"音频保存位置{path}{name}.m4a")

    if not save_ts:
        if os.path.exists(download.path_ts):
            processvideo.remove_ts(download.path_ts)
        if descrypt_path is not None and os.path.exists(descrypt_path):
            processvideo.remove_ts(descrypt_path)
        if os.path.exists(f"{path}/{name}.ts"):
            os.remove(f"{path}/{name}.ts")
        print_log("delete ts")
    global downloading
    downloading = False


# 下载模块
class M3u8Download:

    def __init__(
        self,
        path: str,
        name: str,
        url_: str = "",
        headers="",
        progressbar=progressbar,
        print_log=print_log,
    ) -> None:
        self.solve_count = 0
        self.path = path
        self.path_m3u8 = path + "/m3u8"
        self.name = name
        self.url_ = url_
        self.headers = headers
        self.progressbar = progressbar
        self.print_log = print_log

        self.path_ts = f"{path}/{name}/"
        self.filem3u8 = f"{self.path_m3u8}/{name}.m3u8"
        self.filem3u8_main = f"{self.path_m3u8}/main/{name}.m3u8"
        self.creat_dir(self.path_m3u8)
        self.creat_dir(f"{self.path_m3u8}/main")
        self.total = 0

    def total_ts(self):
        """查看一共有几个ts"""
        if self.total != 0:  # 防止重复计算
            return self.total
        sum = 0
        with open(self.filem3u8, "r") as f:
            for line in f:
                line = line.strip()  # 去掉空格
                if line.startswith("#") or line == "":
                    continue
                sum += 1
        self.total = sum
        self.print_log(f"total is {sum}")
        return sum

    def get_m3u8(self, url: str):
        """下载m3u8文件,返回最后一个m3u8文件url"""
        recv = requests.get(url=url, headers=self.headers)

        self.check_urlcode(recv, "m3u8")

        m3u8 = recv.text
        recv.close()

        if re.search(r"#EXT-X-STREAM-INF", m3u8) is None:
            self.print_log("get m3u8")
            with open(self.filem3u8, "w", encoding="utf-8") as f:
                f.write(m3u8)
            self.get_second_m3u8_url(m3u8, url)  # 这里调用只是为了设置下载时的前缀
            self.print_log(f"保存位置：{self.filem3u8}")
        else:  # 否则说明还有二层m3u8
            with open(self.filem3u8_main, "w", encoding="utf-8") as f:
                f.write(m3u8)
            self.print_log("get main_m3u8")

            url = self.get_second_m3u8_url(m3u8, url)
            self.print_log(f"保存位置：{self.filem3u8_main}")
            end_url = self.get_m3u8(url)
            # 返回最后一级的url
            return end_url if end_url is not None else url

    def get_second_m3u8_url(self, m3u8: str, url: str):
        """获取第一条m3u8网址"""
        for line in m3u8.splitlines():
            line = line.strip()  # 去掉空格
            if not line.startswith("#"):
                return self.set_url_(line, url)

    async def async_download_ts(self, url: str, i, session):  # 根据url下载ts文件
        filename = f"{self.path_ts}/{i}.ts"
        if not url.startswith("http"):
            self.print_log("url存在问题:" + url)
            raise URLError("m3u8", url)
        try:
            if not os.path.exists(filename) or (
                os.path.getsize(filename) == 0
            ):  # 如果存在或者大小为0就下载
                async with session.get(url=url, headers=headers) as recv:
                    self.check_urlcode(recv, f"{i}.ts")
                    async with aiofiles.open(filename, "wb") as f:
                        await f.write(await recv.content.read())
            self.progressbar.update(1)
        except UrlCodeError as e:
            self.print_log(e)
        except Exception:
            self.print_log(f"下载{i}失败。")

    async def async_download(self):  # 根据m3u8文件安排下载
        i = 1
        tasks = []
        async with aiohttp.ClientSession() as session:
            async with aiofiles.open(self.filem3u8, "r", encoding="utf-8") as f:
                async for line in f:
                    line = line.strip()  # 去掉空格
                    if line.startswith("#") or line == "":
                        continue
                    url = f"{self.url_}{line}"  # 获取m3u8时已经设置过url_
                    task = asyncio.create_task(self.async_download_ts(url, i, session))
                    tasks.append(task)
                    i += 1
                await asyncio.wait(tasks)

    def download_ts(self):
        self.total_ts()
        if not os.path.exists(self.path_ts):
            os.makedirs(self.path_ts)
        self.progressbar.set(self.total, 0)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_download())

    def solve_lost(self):  # 检查丢失
        f = True
        while f:
            self.solve_count += 1
            if self.solve_count > 3:
                self.print_log("部分文件无法下载")
                return
            for i in range(1, self.total + 1):
                if not Path(f"{self.path}/{self.name}/{i}.ts").is_file():
                    self.print_log("no " + str(i))
                    f = True
                    break
                else:
                    f = False
            if (
                i != self.total
            ):  # 不适合放在for循环中，因为每次下载完后，需要重头开始检查
                self.download_ts()
        self.print_log("文件数量正确")

    def creat_dir(self, path):
        if not os.path.isdir(path):
            os.makedirs(path)
            self.print_log(f"creat dir :{path}")

    def check_urlcode(self, recv, file):
        code = recv.status if isinstance(recv, ClientResponse) else recv.status_code
        if code != 200:
            recv.close()
            self.print_log(f"[m3u8]下载{file}失败")
            raise UrlCodeError(code)

    def set_url_(self, targetURL: str, baseURL: str):
        """设置URL前缀,返回合成网址"""
        if targetURL.startswith("http") or targetURL.startswith("https"):
            self.url_ = ""
            return targetURL
        elif targetURL.startswith("/"):
            domain = baseURL.split("/")
            self.url_ = f"{domain[0]}//{domain[2]}"
            return f"{self.url_}{targetURL}"
        else:
            self.url_ = f"{baseURL.rsplit('/', 1)[0]}/"
            return f"{self.url_}{targetURL}"


# 视频处理模块
class ProcessVideo:
    def __init__(
        self, path, name, progressbar=progressbar, print_log=print_log
    ) -> None:
        self.name = name
        self.path = path
        self.path_m3u8 = path + "/m3u8"
        self.progressbar = progressbar
        self.print_log = print_log

    def pngend_ts(self, ts_video_path):  # 更改png伪装
        with open(ts_video_path, "rb+") as f:
            f.write(b"\xff\xff\xff\xff")
        # print('resolve ' + ts_video_path + ' success')

    def merge_ts_endwithpng(self, ts_path, mp4_path):  # 有png伪装的合并
        all_ts = os.listdir(ts_path)  # 读取文件夹下的所有文件
        all_ts.sort(key=lambda x: int(x[:-3]))  # 按数字大小排序
        count = len(all_ts)
        self.progressbar.set(count, 0)
        with open(mp4_path, "wb+") as f:
            for i in range(count):
                ts_video_path = os.path.join(ts_path, all_ts[i])  # i.ts路径
                self.pngend_ts(ts_video_path)  # 更改png伪装
                f.write(open(ts_video_path, "rb").read())  # 向f中追加写入i.ts的内容
                self.progressbar.update(1)
        return 1

    def merge_ts(self, ts_path, mp4_path):
        all_ts = os.listdir(ts_path)  # 读取文件夹下的所有文件
        all_ts.sort(key=lambda x: int(x[:-3]))  # 按数字大小排序
        self.progressbar.set(len(all_ts), 0)
        with open(mp4_path, "wb+") as f:
            for ts in all_ts:
                ts_video_path = os.path.join(ts_path, ts)  # i.ts路径
                f.write(open(ts_video_path, "rb").read())  # 向f中追加写入i.ts的内容
                self.progressbar.update(1)
        return 1

    def merge_ts_video_useffmpeg(self, ts_path, mp4_path):
        all_ts = os.listdir(ts_path)  # 读取文件夹下的所有文件
        all_ts.sort(key=lambda x: int(x[:-3]))  # 按数字大小排序
        filename_all = "concat:"
        for i in range(len(all_ts)):
            ts_video_path = os.path.join(ts_path, all_ts[i])  # i.ts路径
            # if(if_png):
            #     pngend_ts(ts_video_path)  # 更改png伪装
            filename_all = filename_all + ts_video_path + "|"
        self.print_log(f'ffmpeg -i "{filename_all}" -c copy "{mp4_path}"')
        os.system(f'ffmpeg -i "{filename_all}" -c copy "{mp4_path}"')

    def remove_ts(self, ts_path):  # 删除ts临时文件
        all_ts = os.listdir(ts_path)  # 读取文件夹下的所有文件
        # all_ts.sort(key=lambda x: int(x[:-3]))  # 按数字大小排序
        for i in range(len(all_ts)):
            ts_video_path = os.path.join(ts_path, all_ts[i])  # i.ts路径
            os.remove(ts_video_path)
        os.rmdir(ts_path)

    # def check_have(path):  # 检查文件是否存在
    #     my_file = Path(path)
    #     if my_file.is_file():
    #         return True
    #     else:
    #         return False

    def ts_to_mp4(self):
        if os.path.exists(f"{self.path}/{self.name}.mp4"):
            self.print_log("MP4已存在")
            return
        os.system(
            f'ffmpeg -i "{self.path}/{self.name}.ts" -f mp4 -codec copy "{self.path}/{self.name}.mp4"'
        )
        # os.system(f'ffmpeg -i "video/{name}.mp4" -vcodec copy -acodec copy -f mpegts "video/{name}.ts"')
        # ffmpeg -i "%%a"   -vcodec copy -acodec copy -f mpegts "D:\转换后目录\%%~na.ts"
        # ffmpeg -i "%%a" -f mp4 -codec copy "%%~na.mp4"
        self.print_log("ts_to_mp4  finished")

    def mp4_to_m4a(self):
        if os.path.exists(f"{self.path}/{self.name}.m4a"):
            self.print_log("音频已存在")
            return
        if not os.path.exists(f"{path}{name}.mp4"):
            self.ts_to_mp4()
        # self.print_log(f'ffmpeg -i "{self.path}/{self.name}.mp4" -vn -codec copy "{self.path}/{self.name}.m4a"')
        os.system(
            f'ffmpeg -i "{self.path}/{self.name}.mp4" -vn -codec copy "{self.path}/{self.name}.m4a"'
        )
        self.print_log("mp4_to_m4a  finished")

    def check_withpngend(self):  # 检测是否是存在png伪装
        flag = False
        with open(f"{self.path_m3u8}/{self.name}.m3u8", "r") as f:
            for line in f:
                line = line.strip()  # 去掉空格
                if line.startswith("#") or line == "":
                    continue
                if line.split(".")[-1] == "png":
                    flag = True
                else:
                    flag = False
                break
        return flag

    def merge_paln_b(self, if_png):  # 暂时存在错误
        if input("\n是否需要转成mp4(y/n)") == "y":  # ts直接合并成mp4
            self.merge_ts_video_useffmpeg(
                f"{self.path}/{self.name}", f"{self.path}/{self.name}.mp4", if_png
            )
            if input("\n是否需要生成mp3(y/n)") == "y":
                self.mp4_to_m4a(self.name)
        else:  # ts合并
            self.merge_ts(
                f"{self.path}/{self.name}", f"{self.path}/{self.name}.ts", if_png
            )
        if input("\n是否删除ts文件(y/n)") == "y":
            self.remove_ts(f"{self.path}/{self.name}")

    def merge_paln_a(self, descrypt_path=None):  # 先合成一个ts，再转mp4
        if os.path.exists(f"{self.path}/{self.name}.ts"):
            print_log("ts已合并")
            return
        if descrypt_path is not None:
            name_t = descrypt_path.split("/")[-1]
        else:
            name_t = self.name

        if self.check_withpngend():
            self.print_log("开始去png伪装合并")
            self.merge_ts_endwithpng(
                f"{self.path}/{name_t}", f"{self.path}/{self.name}.ts"
            )
        else:
            self.print_log("开始合并")
            self.merge_ts(f"{self.path}/{name_t}", f"{self.path}/{self.name}.ts")
        self.print_log("合并完成")
        self.print_log(f"保存位置：{self.path}/{self.name}.ts")


# ts解密模块
class Decrypt:
    def __init__(self, path, name) -> None:
        self.path = path
        self.path_m3u8 = path + "/m3u8"
        self.name = name
        self.decrypt_path = f"{path}/{name}decrypted"

    def get_key(self):
        # 查看是否加密
        i = 0
        key_url = None
        result = None
        with open(f"{self.path_m3u8}/{name}.m3u8", "r") as f:
            for line in f:
                i += 1
                if i == 6:
                    line_s = line.split("=")
                    if line_s[0] == "#EXT-X-KEY:METHOD":
                        key_url = line_s[-1].split('"')[1]
                        key_url = self.merge_url(key_url, url_m3u8)
                        print_log("得到key_url:" + key_url)
                    break
        if key_url is not None:
            print_log("正在尝试获取key")
            res = requests.get(key_url)
            self.check_urlcode(self, res, "key")
            result = res.content
            # result = res.text.encode("utf-8")
            res.close()
            print_log(f"得到key:{result}")
        return result

    async def dec_ts(self, file):
        # 对key进行编码，不然会报错：Object type <class 'str'> cannot be passed to C code
        aes = AES.new(key=self.key, IV=b"0102030405060708", mode=AES.MODE_CBC)

        my_file = Path(f"{path}/{name}decrypted/{file}")  # 如果文件存在则跳过
        if not my_file.is_file():
            async with aiofiles.open(
                f"{path}/{name}/{file}", mode="rb"
            ) as f1, aiofiles.open(f"{path}/{name}decrypted/{file}", mode="wb") as f2:
                bs = await f1.read()  # 从源文件获取
                bs = pad(
                    bs, 16
                )  # 对加密数据padding到16byte的整数倍，不然会报错：Data must be padded to 16 byte boundary in CBC mode
                await f2.write(aes.decrypt(bs))  # 把解密好的内容写入文件
        progressbar.update(1)

    async def aio_dec(self):
        tasks = []
        all_ts = os.listdir(f"{path}/{name}")  # 读取文件夹下的所有文件
        # all_ts.sort(key=lambda x: int(x[:-3]))  # 按数字大小排序
        print_log("正在解密...")
        for ts in all_ts:
            task = asyncio.create_task(self.dec_ts(ts))
            tasks.append(task)
        progressbar.set(len(all_ts), 0)
        await asyncio.wait(tasks)  # 等待任务结束
        print_log("解密完成")

    def decrypt_ts(self):  # 多线程解密
        self.key = self.get_key()
        if self.key is not None:
            if not Path(self.decrypt_path).is_dir():
                os.mkdir(self.decrypt_path)

            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.aio_dec())
            return self.decrypt_path

    def check_urlcode(self, recv, file):
        code = recv.status if isinstance(recv, ClientResponse) else recv.status_code
        if code != 200:
            recv.close()
            self.print_log(f"[m3u8]下载{file}失败")
            raise UrlCodeError(code)

    def merge_url(self, targetURL: str, baseURL: str):
        """返回合成网址"""
        if targetURL.startswith("http") or targetURL.startswith("https"):
            self.url_ = ""
            return targetURL
        elif targetURL.startswith("/"):
            domain = baseURL.split("/")
            self.url_ = f"{domain[0]}//{domain[2]}"
            return f"{self.url_}{targetURL}"
        else:
            self.url_ = f"{baseURL.rsplit('/', 1)[0]}/"
            return f"{self.url_}{targetURL}"


# 粘贴板二维码扫描
class QRcode:
    def __init__(self) -> None:
        pass

    def get_url_by_qr(self):
        url = self.clip_QR_scan()
        if url is not None:
            print_log(f"二维码扫描结果：{url[:60]}...")
            return url

    def decoded_list_output(self, decoded_qr_dict: dict):
        if not decoded_qr_dict:
            return
        for file, qr_decodes in decoded_qr_dict.items():
            print("File:", file)
            for qr_decode in qr_decodes:
                print("Type:", qr_decode.type)
                print("Data:", qr_decode.data.decode())
            print("---")
        return list(decoded_qr_dict.values())[0][0].data.decode()

    def clip_QR_scan(self):
        # 粘贴板二维码输入
        clip = ImageGrab.grabclipboard()
        if isinstance(clip, Image.Image):
            print_log("Image: size : %s, mode: %s" % (clip.size, clip.mode))
            decoded_objects = pyzbar.decode(clip)
            if len(decoded_objects) > 0:
                data = self.decoded_list_output({"粘贴板": decoded_objects})
                return data
            else:
                print_log("未识别到内容")
        elif clip:
            for filename in clip:
                clip = Image.open(filename)
                decoded_objects = pyzbar.decode(clip)
                self.decoded_list_output({filename: decoded_objects})
            os.system("pause")
        else:
            print_log("clipboard is empty")


def creat_dir(dir_name):
    if not Path(dir_name).is_dir():
        os.makedirs(dir_name)


# https://87fupo3-1312801207.cos-website.ap-nanjing.myqcloud.com/
def url_conversion(url: str):
    try:
        if url.endswith(".com") or url.endswith(".com/"):
            response = requests.get(url)
            url = re.findall(r'<iframe src="(.*?)"', response.text, re.S)
            response.close()
            if len(url) > 0:
                return DecryptM3u8Url().de2023_6_29(url[0])
        elif "baidu.com" in url:
            response = requests.get(url)
            id = re.findall(r'replace\("(.*?)"\)', response.text, re.S)[0].rsplit(
                "/", 1
            )[-1]
            response = requests.get(
                f"https://a.5865865.xyz/api.php?act=geturl9&id={id}"
            )
            en_url = re.findall(r'url":"(.*?)"', response.text, re.S)[0]
            url = urllib.parse.unquote(base64.b64decode(en_url).decode("utf-8"))
            response = requests.get(url)
            print(response.text)
            response.close()
            return url
        elif url[-7:-4] == "?t=":
            t = url.rsplit("=", 1)[-1]
            url = "https://tz.9-u.cn/api.php?act=geturl2&t=" + t
            response = requests.get(url)
            url = json.loads(response.text)["url"]
            response.close()
            return DecryptM3u8Url().de2023_6_29(url)
        elif len(url.split("&")) > 2 and "key" in url:
            return DecryptM3u8Url().de2023_6_29(url)
        else:
            print_log(f"暂时无法识别{url}")

    except IndexError as e:
        print_log(e)


def qrcode_invoked_by_ui():
    url = QRcode().get_url_by_qr()
    if url is not None:
        return url_conversion(url)


if __name__ == "__main__":
    # url = "https://usher.ttvnw.net/vod/2210314109.m3u8?acmb=e30%3D&allow_source=true&browser_family=microsoft%20edge&browser_version=127.0&cdm=wv&os_name=Windows&os_version=NT%2010.0&p=7050009&platform=web&play_session_id=042e2ae62b1555296fd7e0270d3d16cd&player_backend=mediaplayer&player_version=1.31.0-sr.3&playlist_include_framerate=true&reassignments_supported=true&sig=fe5d75746d9c9905f0eb15932c355bb9d2af5a61&supported_codecs=av1,h265,h264&token=%7B%22authorization%22%3A%7B%22forbidden%22%3Afalse%2C%22reason%22%3A%22%22%7D%2C%22chansub%22%3A%7B%22restricted_bitrates%22%3A%5B%5D%7D%2C%22device_id%22%3A%223EX6QfnGQt4TVAB2R4iK7cSuJ0m8JU5d%22%2C%22expires%22%3A1722464593%2C%22https_required%22%3Atrue%2C%22privileged%22%3Afalse%2C%22user_id%22%3A891620891%2C%22version%22%3A2%2C%22vod_id%22%3A2210314109%7D&transcode_mode=cbr_v1"
    # dl = M3u8Download("D:\\FGX\\Downloads\\新建文件夹", "test")
    # dl.get_m3u8(url)
    for i in range(1, 5):
        print("a ")
    print(i)
