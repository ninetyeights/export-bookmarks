from tkinter import *
from app import MainWindow

if __name__ == '__main__':
    root = Tk()
    MainWindow(root).pack(side=TOP, fill=BOTH, expand=True)
    # signal(SIGPIPE, SIG_DFL)
    root.mainloop()
