
import tkinter as tk
import vlc
import threading
import time
from PIL import Image, ImageTk





class VideoPlayer(tk.Frame):
    def __init__(self, parent):
        """
            Params:
            screenWidth: the width of the video screen
            screenHeight: the height of the video screen
            playOnOpen: autoplay automatically upon opening a video using openVideo()
        """
        super().__init__(parent)
        #self.parent = parent

        #self.actionBar = ActionBar(self)
        #self.actionBar.place(x=0,y=0)
        
        self.a = tk.Button(self)
        self.a.pack()



class ActionBar(tk.Frame):
    """
        A frame of buttons used to control the video player
    """
    def __init__(self, parent):
        super().__init__(parent)

        self.button = tk.Button(self, text="button", width=50, height=50)
        self.button.pack()





if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("400x400")

    video = VideoPlayer(root)
    #video.pack()
    video.place(x=0,y=0)

    #frame = tk.Frame(root, width=600, height=400)
    #frame.pack()
    #frame.place(anchor='center', relx=0.5, rely=0.5)



    # Create a Label Widget to display the text or Image
    #button = tk.Button(frame)
    #button.pack()


    root.mainloop()
