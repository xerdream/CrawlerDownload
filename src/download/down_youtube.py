import re
import os
from threading import Thread
from pathlib import Path
from pytube import YouTube, StreamQuery
import yt_dlp
# import ffmpeg

# 初始化网页请求头文件
path = ""
url = ""
cookies = ""
name = None
progressbar = None
text_log = None
proxy = ""
proxies = {"http": "127.0.0.1:11452", "https": "127.0.0.1:11452"}
downloading = False


def creat_dir(dir_name):
    if not Path(dir_name).is_dir():
        os.makedirs(dir_name)


def download_audio(streams: StreamQuery):
    print_log("下载音频中...")
    filename = f"{name}.mp3"
    print_log(filename)
    streams.filter(progressive=False, type="audio").order_by("abr").last().download(
        output_path=path, filename=filename
    )

    print_log(f"音频下载成功\n保存地址:{path}/{filename}")


def download_video(streams: StreamQuery, progressive=True):
    print_log(f"下载视频中...   仅画面:{not progressive}")
    filename = f'{name}{"" if progressive else "_nosound"}.mp4'
    streams.filter(progressive=progressive, type="video").order_by(
        "resolution"
    ).last().download(output_path=path, filename=filename)

    print_log(f"视频下载成功\n保存地址:{path}/{filename}")


def print_log(args):
    text_log(args)


def on_progress(
    stream, chunk: bytes, bytes_remaining: int
) -> None:  # pylint: disable=W0613
    filesize = stream.filesize
    bytes_received = filesize - bytes_remaining
    display_progress_bar(bytes_received, filesize)


def display_progress_bar(bytes_received, filesize):
    progressbar.set(filesize, bytes_received)


#     rate = 100 * bytes_received // filesize
#     nr = '\r %5d/%5d \t%3d%%' % (bytes_received, filesize, rate)
#     sys.stdout.write(nr)
#     sys.stdout.flush


def main(save_audio: bool, save_mp4: bool, save_video: bool):
    """pytube下载"""
    try:
        if not save_audio and not save_video and not save_mp4:
            return
        yt = YouTube(url, on_progress_callback=on_progress, proxies=proxies)
        global name
        if name is None or name == "":
            name = re.sub(r'[\/:|?*"<>]', "", yt.title)
        print_log("获取下载地址...")
        streams = yt.streams
        creat_dir(f"{path}")
        print_log("开始下载")
        if save_mp4:
            download_video(streams)
        if save_audio:
            download_audio(streams)
        if save_video:
            download_video(streams, False)
    except Exception as e:
        print_log(e)
        pass
    finally:
        global downloading
        downloading = False
        name = None


# #########################################################################yt-dlp部分


def progress_hook(d):
    """进度条"""
    # print(d["downloaded_bytes"], d["total_bytes"])
    progressbar.set(d["total_bytes"], d["downloaded_bytes"])
    if d["status"] == "finished":
        progressbar.set(1, 0)
        print_log("下载完成。。。")


def postprocessor_hooks(d):
    """后处理"""
    if d["status"] == "started":
        file_name = d["filename"]
        out_name = re.sub(r"\[.*?\]", "", file_name)
        # ffmpeg.run(ffmpeg.output(ffmpeg.input(file_name), out_name))
        # os.remove(file_name)
        os.rename(file_name, out_name)


class MyLogger:
    def debug(self, msg):
        # For compatibility with youtube-dl, both debug and info are passed into debug
        # You can distinguish them by the prefix '[debug] '
        if msg.startswith("[debug] "):
            pass
        else:
            self.info(msg)

    def info(self, msg):
        print_log(msg)

    def warning(self, msg):
        print_log(msg)

    def error(self, msg):
        print_log(msg)


def format_selector(ctx):
    """Select the best video and the best audio that won't result in an mkv.
    NOTE: This is just an example and does not handle all cases"""

    # formats are already sorted worst to best
    formats = ctx.get("formats")[::-1]

    # acodec='none' means there is no audio
    best_video = next(
        f for f in formats if f["vcodec"] != "none" and f["acodec"] == "none"
    )

    # find compatible audio extension
    audio_ext = {"mp4": "m4a", "webm": "webm"}[best_video["ext"]]
    # vcodec='none' means there is no video
    best_audio = next(
        f
        for f in formats
        if ("acodec" in f and f["acodec"] != "none" and f["vcodec"] == "none" and f["ext"] == audio_ext)
    )

    # These are the minimum required fields for a merged format
    yield {
        "format_id": f'{best_video["format_id"]}+{best_audio["format_id"]}',
        "ext": best_video["ext"],
        "requested_formats": [best_video, best_audio],
        # Must be + separated list of protocols
        "protocol": f'{best_video["protocol"]}+{best_audio["protocol"]}',
    }


def main2(save_audio: bool, save_mp4: bool, save_video: bool):
    """yt_dlp下载"""
    blocksize = 1024 * 1024 * 2
    ydl_opts = {
        "proxy": proxy,
        "progress_hooks": [progress_hook],
        "logger": MyLogger(),
        "noprogress": True,
        "paths": {"home": path},
        # 'format': format,
        "buffersize": blocksize,
        "postprocessor_hooks": [postprocessor_hooks],
        # 'keepvideo': True,
        # 'noresizebuffer': True
    }
    if save_audio:
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["keepvideo"] = True
    if save_video:
        ydl_opts["format"] = "bestvideo/best"
        ydl_opts["keepvideo"] = True
    if (save_audio and save_video) or save_mp4:
        ydl_opts["format"] = format_selector

    try:
        ydl = yt_dlp.YoutubeDL(ydl_opts)
        ydl.download(url)
    except Exception as e:
        # print_log(e)
        print(e)
    finally:
        global downloading
        downloading = False


def main_invoked_by_ui(
    save_audio: bool, save_mp4: bool, save_video: bool, use_yt_dlp: bool = True
):
    global downloading
    if downloading:
        print_log("已经在下载了！")
    elif use_yt_dlp:
        downloading = True
        print_log("使用yt_dlp下载...")
        t = Thread(target=main2, args=(save_audio, save_mp4, save_video))
        t.start()
    else:
        downloading = True
        t = Thread(target=main, args=(save_audio, save_mp4, save_video))
        t.start()


if __name__ == "__main__":
    """yt_dlp下载"""
    blocksize = 1024 * 1024 * 2
    ydl_opts = {
        # "cookiefile": "D:\\cookies.txt",
        "proxy": "socks5://127.0.0.1:11451",
        # "progress_hooks": [progress_hook],
        # "logger": MyLogger(),
        "noprogress": True,
        "paths": {"home": path},
        # 'format': format,
        "buffersize": blocksize,
        # "postprocessor_hooks": [postprocessor_hooks],
        # 'keepvideo': True,
        # 'noresizebuffer': True
    }
    ydl_opts["format"] = "bestaudio/best"
    ydl_opts["keepvideo"] = True
    url = "https://www.youtube.com/watch?v=AOWnIiZVaSg"
    ydl = yt_dlp.YoutubeDL(ydl_opts)
    with open("a.py", "w+", encoding="utf-8") as f:
        formatss = ydl.extract_info(url, download=False).get("formats")[::-1]
        fs = [f for f in formatss if "acodec" in f and f["acodec"] != "none" and f["vcodec"] == "none"]
        f.write(str(fs))
    print("ok")
    # ydl.download(url)
