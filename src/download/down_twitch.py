import re
import os
import asyncio
from yt_dlp import YoutubeDL
from threading import Thread
from .down_m3u8 import M3u8Download, ProcessVideo

total = 0
headers = {'user-agent': "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"}
path = 'download'
path_m3u8 = 'download/m3u8'
name = 'default'
url_ = ""
url = ""
proxy = ""
downloading = False

progressbar = None
print_log = print


class MyLogger:
    def debug(self, msg):
        # For compatibility with youtube-dl, both debug and info are passed into debug
        # You can distinguish them by the prefix '[debug] '
        if msg.startswith('[debug] '):
            pass
        else:
            self.info(msg)

    def info(self, msg):
        print_log(msg)

    def warning(self, msg):
        print_log(msg)

    def error(self, msg):
        print_log(msg)


def my_hook(d):
    """进度条"""
    # print(d["downloaded_bytes"], d["total_bytes"])
    progressbar.set(d["total_bytes"], d["downloaded_bytes"])
    if d['status'] == 'finished':
        print_log('Done downloading, now post-processing ...')


def creat_dir(dir_name):
    if not os.path.isdir(dir_name):
        os.makedirs(dir_name)


def main2(save_audio: bool, save_mp4: bool, save_ts: bool):
    global url, name
    if (not save_audio and not save_mp4 and not save_ts):
        print_log("请选择要保存的文件")
        return
    if os.path.exists(f'{path}/{name}.ts'):  # 判断是否需要开始下载
        print_log(f"ts文件已存在:{path}/{name}.ts")
        return
    print_log("*" * 50)
    # 获取信息
    ydl_opts = {
        'proxy': proxy,
        # 'progress_hooks': [my_hook],
        'logger': MyLogger(),
        'noprogress': True,
        'paths': {'home': path},
        # 'format': format,
        # 'buffersize': blocksize,
        # 'keepvideo': True,
        # 'noresizebuffer': True
    }
    try:
        ydl = YoutubeDL(ydl_opts)
        video_info = ydl.extract_info(url, ie_key='TwitchVod', download=False)
        url_m3u8 = video_info['manifest_url']
        if name is None or name == "" or name == "default":
            name = re.sub(r'[\/:|?*"<>]', '_', video_info['fulltitle'])
        # 开始下载
        if __name__ != "__main__":
            loop1 = asyncio.new_event_loop()
            asyncio.set_event_loop(loop1)
        download = M3u8Download(path=path, name=name, headers=headers, progressbar=progressbar, print_log=print_log)
        # download = M3u8Download(path, path_m3u8, name, headers=headers)
        processvideo = ProcessVideo(path=path, name=name, progressbar=progressbar, print_log=print_log)
        # download.get_m3u8_twitch(url_m3u8)
        download.get_m3u8_twitch(url_m3u8)
        download.download_ts()
        download.solve_lost()
        processvideo.merge_paln_a()
        if save_mp4:
            processvideo.ts_to_mp4()
        if save_audio:
            processvideo.mp4_to_m4a()
            if not save_mp4:
                os.remove(f'{path}/{name}.mp4')

        if not save_ts:
            if os.path.exists(download.path_ts):
                processvideo.remove_ts(download.path_ts)

            if os.path.exists(f'{path}/{name}.ts').is_file():
                os.remove(f'{path}/{name}.ts')
            print_log("delete ts")
    # except Exception as e:
    #     print_log(str(e))
    finally:
        global downloading
        downloading = False
        name = None


def main():
    blocksize = 1024 * 1024 * 2
    ydl_opts = {
        'proxy': proxy,
        # 'progress_hooks': [my_hook],
        'logger': MyLogger(),
        'noprogress': True,
        'paths': {'home': path},
        # 'format': format,
        'buffersize': blocksize,
        # 'keepvideo': True,
        # 'noresizebuffer': True
    }
    try:
        ydl = YoutubeDL(ydl_opts)
        ydl.extract_info(url, ie_key='TwitchVod')
    except Exception as e:
        print_log(e)
    finally:
        global downloading
        downloading = False


def main_invoked_by_ui(save_audio: bool, save_mp4: bool, save_video: bool, use_async: bool = False):
    global downloading
    if downloading:
        print_log("已经在下载了！")
    elif use_async:
        downloading = True
        print_log("使用协程下载...无ts")
        # main2(save_audio, save_mp4, save_video)
        t = Thread(target=main2, args=(save_audio, save_mp4, save_video))
        t.start()
    else:
        downloading = True
        print_log("使用yt_dlp下载...无ts")
        t = Thread(target=main, args=())
        t.start()


if __name__ == '__main__':
    url = "https://www.twitch.tv/videos/1887203872"
    main2(True, True, True)
