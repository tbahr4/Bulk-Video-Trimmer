
import tkinter as tk


class MainApp(tk.Frame):
    def init(self, parent):
        super().__init__(parent)
        
        newFrame = example(self)

class example(tk.Frame):
    def init(self, parent):
        super().__init__(parent)
        self.bFrame = tk.Frame(self)

        self.startEntry = tk.Entry(self.bFrame, width=5)
        self.startEntry.pack(side=tk.RIGHT)


root = tk.Tk()
root.title("wow")

app = MainApp(root)
app.pack(side="left")

root.mainloop()