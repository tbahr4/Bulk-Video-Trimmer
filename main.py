#
# main.py
#
# The main file for the trimmer application
#

import tkinter as tk
import gui


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Video Trimmer")
    root.geometry("400x100")
    root.resizable(width=False, height=False)
    root.iconbitmap("images/logo.ico")

    app = gui.MainApp(root)
    app.setScene(gui.Scene.SCENE_INITIAL)
    app.pack(side="left")

    root.mainloop()
