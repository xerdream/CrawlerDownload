import yt_dlp
import requests


def main():
    # url = "https://www.twitch.tv/videos/1887203872"
    # blocksize = 1024 * 1024 * 2
    # ydl_opts = {
    #     'proxy': 'socks5://127.0.0.1:11451',
    #     # 'progress_hooks': [my_hook],
    #     # 'logger': MyLogger(),
    #     'noprogress': True,
    #     # 'paths': {'home': path},
    #     # 'format': format,
    #     'buffersize': blocksize,
    #     # 'keepvideo': True,
    #     # 'noresizebuffer': True
    # }
    # ydl = yt_dlp.YoutubeDL(ydl_opts)
    # video_info = ydl.extract_info(url, ie_key='TwitchVod', download=False)
    # print(video_info['manifest_url'])
    # print(video_info['fulltitle'])
    url = "https://usher.ttvnw.net/vod/1887203872.m3u8?allow_source=true&allow_audio_only=true&allow_spectre=true&player=twitchweb&playlist_include_framerate=true&nauth=%7B%22authorization%22%3A%7B%22forbidden%22%3Afalse%2C%22reason%22%3A%22%22%7D%2C%22chansub%22%3A%7B%22restricted_bitrates%22%3A%5B%5D%7D%2C%22device_id%22%3Anull%2C%22expires%22%3A1691121875%2C%22https_required%22%3Atrue%2C%22privileged%22%3Afalse%2C%22user_id%22%3Anull%2C%22version%22%3A2%2C%22vod_id%22%3A1887203872%7D&nauthsig=53ae5077f8f5c01026130c68327066cb8c86c0b9"
    response = requests.get(url)
    text = response.text
    response.close()
    for line in text.split("\n"):
        line = line.strip()  # 去掉空格
        if line.startswith("http"):
            print(line)
            url_m3u8 = line
            break
    url_ = url_m3u8.rsplit("/", 1)[0] + "/"
    response = requests.get(url_ + "1.ts")
    # print(response.text)
    response.close()
    print(url_)


def merge_url(targetURL: str, baseURL: str):
    """合成URL"""
    if targetURL.startswith("http") or targetURL.startswith("https"):
        return targetURL
    elif targetURL.startswith("/"):
        domain = baseURL.split("/")
        return f"{domain[0]}//{domain[2]}{targetURL}"
    else:
        return f"{baseURL.rsplit('/',1)[0]}/{targetURL}"


if __name__ == "__main__":
    # for i in range(1, 5):
    #     print("a ")
    # print(i)
    print(merge_url("aaa", "https://cf2prra.contactflirt.one/wuyg33w/xd?m=1&t=Valentina_Petrovna"))
