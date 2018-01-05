from tkinter import *
from tkinter import filedialog
from tkinter.ttk import *

from infomax import Infomax


class StdoutRedirector:
    def __init__(self, text_widget):
        self.text_space = text_widget
        self.text_space.bind("<Key>", lambda e: "break")
        self.text_space.bind("<1>", lambda event: text_widget.focus_set())

    def write(self, string, ):
        self.text_space.insert('end', string)
        self.text_space.see('end')
        self.text_space.update_idletasks()

    def flush(self):
        self.text_space.update_idletasks()


class Application(Frame):
    def __init__(self, master):
        super().__init__(master)

        self.filename = StringVar()
        self.sources = StringVar()
        self.sources.set('1')

        self.window = StringVar()
        self.window.set('10')

        self.infomax = None

        self.frame_file = Labelframe(self, text='Dataset')
        label_file = Label(self.frame_file, textvariable=self.filename)
        button_browse = Button(self.frame_file, text="Browse", command=self.open_file)
        self.frame_options = Labelframe(self, text='Options')
        label_source = Label(self.frame_options, text="Number of Sources")
        entry_source = Entry(self.frame_options, textvariable=self.sources)
        label_window = Label(self.frame_options, text="Time Window")
        entry_window = Entry(self.frame_options, textvariable=self.window)
        self.button_start = Button(self, text='START', command=self.start_task)
        self.button_stop = Button(self, text='STOP', command=self.stop_task, state=DISABLED)
        xscrollbar = Scrollbar(self, orient=HORIZONTAL)
        yscrollbar = Scrollbar(self, orient=VERTICAL)
        text_output = Text(self, wrap=NONE, xscrollcommand=xscrollbar.set, width='300', height='100',
                           yscrollcommand=yscrollbar.set, bg='black', fg='white', bd=0)

        self.pack(fill=BOTH, expand=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=0)
        self.columnconfigure(3, weight=0)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(4, weight=0)

        self.frame_file.grid(row=1, column=1, sticky='NW')
        label_file.grid(row=0, column=1)
        button_browse.grid(row=0, column=0)
        self.frame_options.grid(row=2, column=1, sticky='NW')
        label_source.grid(row=0, column=0)
        entry_source.grid(row=0, column=1)
        label_window.grid(row=0, column=2)
        entry_window.grid(row=0, column=3)
        self.button_start.grid(row=1, column=2, sticky='E')
        self.button_stop.grid(row=2, column=2, sticky='E')
        text_output.grid(row=3, column=1, columnspan=2, rowspan=1, padx=0)
        xscrollbar.grid(row=4, column=1, columnspan=2, sticky='EW')
        yscrollbar.grid(row=3, column=3, sticky='NS')

        self.redirector = StdoutRedirector(text_output)
        sys.stdout = self.redirector
        sys.stderr = self.redirector
        xscrollbar.config(command=text_output.xview)
        yscrollbar.config(command=text_output.yview)

    def open_file(self):
        filename = filedialog.askopenfilename()
        self.filename.set(filename)
        print(filename)

    def start_task(self):
        try:
            sources = int(self.sources.get())
            window = int(self.window.get())
            filename = self.filename.get()
            self.onStart()
            self.infomax = Infomax(filename, sources, window, self.redirector, self.onStop)
            self.infomax.start()
        except Exception as e:
            print(e)

    def stop_task(self):
        if self.infomax:
            self.infomax.stop()

    def onStart(self):
        self.button_stop['state'] = 'normal'
        self.button_start['state'] = 'disabled'
        for widget in self.frame_file.winfo_children():
            widget.configure(state='disabled')
        for widget in self.frame_options.winfo_children():
            widget.configure(state='disabled')

    def onStop(self):
        self.button_start['state'] = 'normal'
        self.button_stop['state'] = 'disabled'
        for widget in self.frame_file.winfo_children():
            widget.configure(state='normal')
        for widget in self.frame_options.winfo_children():
            widget.configure(state='normal')


if __name__ == '__main__':
    root = Tk()
    root.title('INFOMAX')
    root.iconbitmap('infomax.ico')
    root.geometry("650x400+300+300")
    app = Application(root)


    def exit():
        app.stop_task()
        root.destroy()


    root.protocol("WM_DELETE_WINDOW", exit)
    root.mainloop()
