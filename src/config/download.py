import os
import json

DEFAULT_CONFIG = {
    "save_path": "download/",
    "bilibili_cookies": "",
    "proxy": "",
}


class DownloadConfig():
    def __init__(self, print_log=print) -> None:
        self.print_log = print_log
        self.config_file_name = "config.json"
        self.config = DEFAULT_CONFIG
        self.load_config()

    @property
    def save_path(self):
        return self.config["save_path"] if "save_path" in self.config else ""

    @save_path.setter
    def save_path(self, save_path):
        self.config["save_path"] = save_path

    @property
    def proxy(self):
        return self.config["proxy"] if "proxy" in self.config else ""

    @proxy.setter
    def proxy(self, proxy):
        self.config["proxy"] = proxy

    @property
    def bilibili_cookies(self):
        return self.config["bilibili_cookies"] if "bilibili_cookies" in self.config else ""

    @bilibili_cookies.setter
    def bilibili_cookies(self, bilibili_cookies):
        self.config["bilibili_cookies"] = bilibili_cookies

    def load_config(self):
        try:
            if (os.path.exists(self.config_file_name)):
                with open(self.config_file_name, encoding='utf-8', mode='r') as f:
                    self.config = json.loads(f.read())
                self.print_log("读取配置成功")
        except Exception as e:
            self.print_log(f"[警告]读取配置失败：{e},使用默认参数")

    def save_config(self):
        try:
            json_str = json.dumps(self.config, indent=4)
            with open(self.config_file_name, encoding='utf-8', mode='w') as f:
                f.write(json_str)
            self.print_log("保存配置成功")
        except Exception as e:
            self.print_log(f"[警告]保存配置失败：{e}")

    def set_log(self, log):
        self.print_log = log


if __name__ == "__main__":
    print(DownloadConfig().save_path)
