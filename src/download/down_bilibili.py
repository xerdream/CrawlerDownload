import json
import requests
import os
import re
from pathlib import Path
from Util import wget
from Util import UrlCodeError, URLError

# 初始化网页请求头文件
path = ""
url = ""
cookies = ""
video_name = None
progressbar = None
print_log = print

user_agent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
header1 = {  # 获取下载地址的网页请求头
    'user-agent': user_agent,
    "cookie": cookies
}
header2 = {  # 下载视频和音频的网页请求头
    'user-agent': user_agent,
    "cookie": cookies,
    "referer": url
}


def rebuild_header():
    """重新构造请求头"""
    global header1
    header1 = {'user-agent': user_agent, "cookie": cookies}
    global header2
    header2 = {'user-agent': user_agent, "cookie": cookies, "referer": url}


def creat_dir(dir_name):
    if not Path(dir_name).is_dir():
        os.makedirs(dir_name)


def check_url():
    """检查并纠正url"""
    global url
    temp_url = re.search(r"(https|http|ftp)://([\w-]+\.)+[\w-]+(/[./?%&=\w-]*)(:[0-9]{1,5})?(/[S]*)?", url)
    if url is None:
        raise URLError("bl", url)
    else:
        url = temp_url[0]


def get_download_url():  # 处理html获得下载地址
    print_log("访问网页...")
    recv = requests.get(url, headers=header1)
    code = recv.status_code
    if (code != 200):
        recv.close()
        print_log("无法访问网站")
        raise UrlCodeError(code)
    html_text = recv.text
    recv.close()
    re_name = re.compile(r'class="video-title.*?>(.*?)</h1>', re.S)  # 视频标题
    re_script = re.compile(r'<script>window.__playinfo__=(.*?)</script>',
                           re.S)  # 包含各种清晰度下载地址的scrip
    print_log("解析下载地址...")
    try:
        global video_name
        if video_name is None:  # 未手动指定标题则获取网页标题
            video_name = re_name.findall(html_text)[0]
            print_log("自动获取的视频名称：" + video_name)
        video_name = re.sub(r'[\/:|?*"<> ]', '', video_name)
        if len(video_name) > 50:  # 限制为50个字符
            video_name = video_name[:50]
        print_log("视频名称：" + video_name)
    except Exception as e:
        print_log(f"[错误] 视频名称获取失败：{e}")
        print_log("使用bv号作为文件名称")
        video_name = url.split("/")[4]

    try:
        script = re_script.findall(html_text)[0]
        json_script = json.loads(script)

        global audio_url
        audio_url = json_script['data']['dash']['audio'][0]['baseUrl']  # 0是最高清晰度
        global video_url
        video_url = json_script['data']['dash']['video'][0]['baseUrl']  # 0是最高清晰度
    except Exception as e:
        print_log(f"[错误] 下载地址获取失败：{e}")


def download_audio():
    print_log("下载音频中...")
    download(audio_url, f'{path}/{video_name}.mp3')

    print_log("音频下载成功")
    print_log("保存地址:" + f'{path}/{video_name}.mp3')


def download_video():
    print_log("下载视频中...")

    download(video_url, f'{path}/{video_name}_temp.mp4')

    print_log("视频下载成功")
    print_log("保存地址" + f'{path}/{video_name}_temp.mp4')


def merge_audio_video():  # 调用ffmpeg
    print_log("开始合并")
    os.system(
        f'ffmpeg -i "{path}/{video_name}_temp.mp4" -i "{path}/{video_name}.mp3" -c copy "{path}/{video_name}.mp4"'
    )
    print_log("合并完成")


def delete_audio_temp():
    os.remove(f"{path}/{video_name}.mp3")
    print_log("audio_temp删除成功")


def delete_video_temp():
    os.remove(f"{path}/{video_name}_temp.mp4")
    print_log("video_temp删除成功")


def download(url: str, fname: str):
    wwget = wget(progressbar=progressbar, print_log=print_log)
    wwget.download(url, fname, header2)


def main_invoked_by_ui(save_audio: bool, save_mp4: bool, save_video: bool):
    try:
        check_url()
        rebuild_header()
        print_log("*" * 50)
        get_download_url()  # 处理html获得下载地址
        print_log("获取下载地址成功")
        creat_dir(f"{path}")
        if save_mp4 or save_audio:
            download_audio()
        if save_mp4 or save_video:
            download_video()
        progressbar.clear()
        if save_mp4:
            merge_audio_video()
        if save_mp4 and not save_audio:
            delete_audio_temp()  # 删除音频temp

        if save_mp4 and not save_video:
            delete_video_temp()  # 删除视频temp
    except UrlCodeError as e:
        print_log(e)


# https://www.bilibili.com/video/BV1Bk4y1x7gA/?spm_id_from=333.999.0.0&vd_source=6382367da098de8f5bf4115c8898df40
if __name__ == "__main__":
    print_log("正在获取下载地址")
    url = "https://www.bilibili.com/video/BV1sJ4m1M7AT/?spm_id_from=333.1007.tianma.1-2-2.click&vd_source=6382367da098de8f5bf4115c8898df40"
    recv = requests.get(url, headers=header1)
    code = recv.status_code
    if (code != 200):
        recv.close()
        print_log("无法访问网站")
        raise UrlCodeError(code)
    html_text = recv.text
    recv.close()
    re_name = re.compile(r'class="video-title".*?>(.*?)</h1>', re.S)  # 视频标题
    re_script = re.compile(r'<script>window.__playinfo__=(.*?)</script>',
                           re.S)  # 包含各种清晰度下载地址的scrip
    script = re_script.findall(html_text)[0]
    json_script = json.loads(script)
    audio_url = json_script['data']['dash']['audio'][0]['baseUrl']  # 0是最高清晰度
    audio_url2 = json_script['data']['dash']['audio'][2]['baseUrl']  # 0是最高清晰度
    video_url = json_script['data']['dash']['video'][0]['baseUrl']  # 0是最高清晰度
    # print(json_script['data']['dash']['audio'])
    # print(json_script['data']['dash']['video'])
    wget().download(audio_url, '123.mp3', header2)
