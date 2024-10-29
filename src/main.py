
import tkinter
from CrawlerDownload import CD_GUI


def window_center(tk: tkinter.Tk, width: int, heigh: int):
    """窗口居中"""
    screenwidth = tk.winfo_screenwidth()
    screenheight = tk.winfo_screenheight()
    tk.geometry('%dx%d+%d+%d' % (width, heigh, (screenwidth - width) / 2, (screenheight - heigh) / 2))


def main():
    tk = tkinter.Tk()
    window_center(tk, 800, 600)
    CD_GUI(tk)
    tk.mainloop()


if __name__ == "__main__":
    main()
