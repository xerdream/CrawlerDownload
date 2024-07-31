# 自定义异常类 MyError ，继承普通异常基类 Exception
class URLError(Exception):
    def __init__(self, mod, strs):
        self.mod = mod
        self.strs = strs

    def __str__(self):
        return f"[{self.mod}]:URLError:{self.strs}"


class UrlCodeError(Exception):
    def __init__(self, code):
        self.code = code

    def __str__(self):
        return f"URL错误代码：{self.code}"


def main():
    raise URLError(__name__, "12344")


if __name__ == "__main__":
    main()
