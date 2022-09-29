import json
import os
import csv
import datetime
from sys import platform
from tkinter import *
from tkinter import filedialog as fd
from tkinter import messagebox as mb

Path = os.path.join


class Bookmark:
    def __init__(self, path, save_file):
        self.path = path
        self.save_file = save_file
        self.data = self.get_data()
        self.list = []
        self.obj = {'1': '书签栏', '2': '其他文件夹', '3': '移动书签'}

    def get_data(self):
        with open(self.path, 'r', encoding="utf-8") as fp:
            return json.loads(fp.read())

    def main(self):
        data = self.data['roots']
        try:
            self.handle_data(data['bookmark_bar']['children'], data['bookmark_bar']['id'])
        except:
            pass
        try:
            self.handle_data(data['other']['children'], data['other']['id'])
        except:
            pass
        try:
            self.handle_data(data['synced']['children'], data['synced']['id'])
        except:
            pass

        try:
            with open(self.save_file, 'w', encoding="utf-8") as f:
                writer = csv.writer(f)
                for row in self.list:
                    writer.writerow(row)
                mb.showinfo('OK', '文件已成功导出')
        except Exception as e:
            mb.showerror('OK', e)

    def handle_data(self, data, parentId):
        for value in data:
            if value['type'] == 'url':
                group = self.obj[parentId]
                microseconds = int(value['date_added'])
                epoch = datetime.datetime(1601, 1, 1)
                date = epoch + datetime.timedelta(microseconds=microseconds)
                date = date.strftime('%Y-%m-%dT%H:%M:%SZ')
                self.list.append([group, str(value['name']), '', '', value['url'], '', '', 0, str(date), str(date)])
            elif value['type'] == 'folder':
                group = '%s/%s' % (self.obj[parentId], value['name'])
                self.obj[value['id']] = group

            try:
                self.handle_data(value['children'], value['id'])
            except:
                pass


class VerticalScroll(Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, **kwargs)

        self.parent = parent

        self.vscrollbar = Scrollbar(self, orient=VERTICAL)
        self.vscrollbar.pack(fill=Y, side=RIGHT, expand=0)

        self.canvas = Canvas(self, bd=0, highlightthickness=0, yscrollcommand=self.vscrollbar.set)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=1, padx=32)
        self.canvas.configure(background='white')

        self.vscrollbar.config(command=self.canvas.yview)

        # reset the view
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))

        self.interior = Frame(self.canvas)
        self.interior.configure(background='#fff')

        interior_id = self.canvas.create_window(0, 0, window=self.interior, anchor=NW)

        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (self.interior.winfo_reqwidth(), self.interior.winfo_reqheight())
            self.canvas.config(scrollregion="0 0 %s %s" % size)
            if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                self.canvas.config(width=self.interior.winfo_reqwidth())

        self.interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                self.canvas.itemconfigure(interior_id, width=self.canvas.winfo_width())

        self.canvas.bind('<Configure>', _configure_canvas)

        # Magic part to enable two finger / mouse wheel scroll on canvas
        def _on_mousewheel(event):
            self.canvas.yview_scroll(-1 * event.delta, "units")

        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # for i in range(100):
        #     Label(self.scroll_window, text='Tkinter 滾動條控制元件通常用於滾動控制元件 %s' % i).pack(pady=12)


class MainWindow(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.parent.geometry('600x700')
        self.parent.resizable(False, False)
        self.parent.title('备份浏览器书签')
        self.parent.configure(background='black')

        self.scrollbar = VerticalScroll(self)
        self.scrollbar.pack(side=LEFT, fill=BOTH, expand=1)

        self.browsers = list(self.get_browsers())
        self.show_display()

    def show_display(self):
        row = 0
        for browser in self.browsers:
            row += 1
            local_state = Path(browser['data_dir'], 'Local State')
            profile_count = 0
            title_label = Label(self.scrollbar.interior, text=browser['app_name'], font=("Airal", 28), bg='white',
                                fg='black')
            title_label.grid(row=row, column=1)

            with open(local_state, 'r', encoding='utf-8') as f:
                _state = json.loads(f.read())
                info = _state['profile']['info_cache']
            for (i, key) in enumerate(info.keys()):
                row += 1
                name = info[key]['name']
                bookmark_path = Path(browser['data_dir'], key, 'Bookmarks')
                if os.path.exists(bookmark_path) is False:
                    if profile_count == 0:
                        title_label.grid_forget()
                    continue
                profile_count += 1
                Label(self.scrollbar.interior, text=name, font=('Arial', 18), bg='white', fg='black').grid(row=row,
                                                                                                           column=0,
                                                                                                           padx=16,
                                                                                                           pady=16)
                Button(self.scrollbar.interior, text="导出为CSV文件", bg='white', fg='black',
                       command=lambda path=bookmark_path: self.file_export(path)).grid(row=row, column=1, padx=8,
                                                                                       pady=0, ipadx=8, ipady=0)

    def file_export(self, path):
        f = fd.asksaveasfile(mode='w', defaultextension='.csv', title='请选择需要保存的文件')
        if f is not None:
            Bookmark(path, f.name).main()
        else:
            mb.showinfo('OK', '请选择文件后重试')

    @staticmethod
    def get_browsers():
        browsers = {
            'darwin': {
                'chrome': {
                    'app_path': '/Applications/Google Chrome.app',
                    'app_name': 'Google Chrome',
                    'data_dir': os.path.expanduser('~') + '/Library/Application Support/Google/Chrome/'
                },
                'edge': {
                    'app_path': '/Applications/Microsoft Edge.app',
                    'app_name': 'Microsoft Edge',
                    'data_dir': os.path.expanduser('~') + '/Library/Application Support/Microsoft Edge/'
                },
                'brave': {
                    'app_path': '/Applications/Brave Browser.app',
                    'app_name': 'Brave',
                    'data_dir': os.path.expanduser('~') + '/Library/Application Support/BraveSoftware/Brave-Browser/'
                }
            },
            'win32': {
                'chrome': {
                    'app_path': [
                        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
                    ],
                    'app_name': 'Google Chrome',
                    'data_dir': os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Google', 'Chrome',
                                             'User Data')
                },
                'edge': {
                    'app_path': [
                        r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
                        r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
                    ],
                    'app_name': 'Microsoft Edge',
                    'data_dir': os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Microsoft', 'Edge',
                                             'User Data')
                },
                'brave': {
                    'app_path': [
                        r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe',
                        r'C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe',
                    ],
                    'app_name': 'Brave',
                    'data_dir': os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'BraveSoftware',
                                             'Brave-Browser',
                                             'User Data')
                }
            }
        }
        if platform == 'darwin':
            current = browsers[platform]
        elif platform == 'win32':
            current = browsers[platform]
        else:
            current = None
            exit(0)

        for key in current.keys():
            if platform == 'win32':
                has_path = False
                for path in current[key]['app_path']:
                    if os.path.exists(path):
                        has_path = True
                        break
                if has_path is True:
                    yield current[key]
            else:
                if os.path.exists(current[key]['app_path']):
                    yield current[key]


if __name__ == '__main__':
    root = Tk()
    MainWindow(root).pack(side=TOP, fill=BOTH, expand=True)
    # signal(SIGPIPE, SIG_DFL)
    root.mainloop()
