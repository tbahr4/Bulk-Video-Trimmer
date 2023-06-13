import tkinter as tk
from tkinter import StringVar
from tkinter import filedialog
from enum import Enum
import video
from tkinter import filedialog
from PIL import Image, ImageTk
from pathvalidate import sanitize_filepath

bg = "#eeeeee"

class Scene(Enum):
    SCENE_INITIAL = 0
    SCENE_CLIPS = 1








class MainApp(tk.Frame):
    """
        The main gui application
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.root = parent
        self.parent = parent
        
        # init scenes
        self.scene = None
        self.setScene(Scene.SCENE_INITIAL)

        # data storage
        self.videoPaths = None
        self.destFolder = None


    def setScene(self, scene: Scene):
        if self.scene: self.scene.pack_forget()

        if scene == Scene.SCENE_INITIAL:
            self.scene = InitialScene(self)
        elif scene == Scene.SCENE_CLIPS:
            if __name__ == "__main__":
                self.videoPaths = (r'C:/Users/tbahr4/Desktop/Programming Projects/Video Trimmer/test-long.mp4', r'C:/Users/tbahr4/Desktop/Programming Projects/Video Trimmer/test.mp4')
                self.destFolder = r"C:/Users/tbahr4/Desktop/Programming Projects/Video Trimmer/TestOutput"
            self.scene = ClipScene(self, self.root, self.videoPaths, self.destFolder)
        self.scene.pack()
            


        
        

#
# Initial Scene Elements
#
class InitialScene(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        # instances
        self.srcSelection = FileSelection(self, "Select Videos")
        self.destSelection = FolderSelection(self, "Destination Directory")
        self.beginButton = BeginButton(self)

        # build
        self.srcSelection.grid(column=0, row=0)
        self.destSelection.grid(column=0, row=1)
        self.beginButton.grid(column=0, row=2, pady=5)

        # properties
        self.hasFolder1 = False
        self.hasFolder2 = False


    def signalFolderSelection(self, caller, items):
        """
            Called by the folder/file selection objects to signal an update on folder selection
        """
        if caller == self.srcSelection:
            self.hasFolder1 = True
            self.parent.videoPaths = items
        elif caller == self.destSelection:
            self.hasFolder2 = True
            self.parent.destFolder = items

        # update button
        self.beginButton.setEnabled(self.hasFolder1 and self.hasFolder2)
        
        

class FileSelection(tk.Frame):
    """
        A Frame that allows for multiple file selection
    """
    def __init__(self, parent, buttonText):
        super().__init__(parent) 
        self.parent = parent
        self.files = None

        # instances
        self.bFolder = tk.Button(self, text=buttonText, width=20, command=self.bFile_onClick)
        self.tFolder = tk.Text(self, height=1, width = 31, state="disabled", wrap="none")

        # build
        self.bFolder.grid(column=0, row=0)
        self.tFolder.grid(column=1, row=0)

    def bFile_onClick(self):
        filetypes = [("MP4 Files", "*.mp4")]
        files = filedialog.askopenfilenames(initialdir="~/Videos", title='Choose videos', filetypes=filetypes)
        if files != "": self.files = files
        else: return

        # update folder text display
        self.tFolder.configure(state="normal")
        self.tFolder.delete("1.0", "end")
        self.tFolder.insert("1.0", f"{len(self.files)} file{'s' if len(self.files) != 1 else ''} selected")
        self.tFolder.configure(state="disabled")

        # update scene if valid path
        self.parent.signalFolderSelection(self, files)     # Signal true if path is non-empty

class FolderSelection(tk.Frame):
    """
        A Frame that allows for folder selection
    """
    def __init__(self, parent, buttonText):
        super().__init__(parent) 
        self.parent = parent
        self.path = ""

        # instances
        self.bFolder = tk.Button(self, text=buttonText, width=20, command=self.bFolder_onClick)
        self.tFolder = tk.Text(self, height=1, width = 31, state="disabled", wrap="none")

        # build
        self.bFolder.grid(column=0, row=0)
        self.tFolder.grid(column=1, row=0)

    def bFolder_onClick(self):
        newPath = filedialog.askdirectory(initialdir="~/Videos")
        if newPath != "": self.path = newPath
        else: return

        # update folder text display
        self.tFolder.configure(state="normal")
        self.tFolder.delete("1.0", "end")
        self.tFolder.insert("1.0", self.path)
        self.tFolder.configure(state="disabled")

        # update scene if valid path
        self.parent.signalFolderSelection(self, newPath)     # Signal true if path is non-empty
        



class BeginButton(tk.Frame):
    """
        Used to transition to the next scene
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        self.bBegin = tk.Button(self, text="Gather Files", width=40, command=self.bBegin_onClick, state="disabled")
        self.bBegin.grid(column=0, row=0)

    def bBegin_onClick(self):
        self.parent.parent.setScene(Scene.SCENE_CLIPS)

    def setEnabled(self, value: bool):
        self.bBegin.config(state="active" if value else "disabled")
       
        

#
# Clip Trimming Scene Elements
#
class ClipScene(tk.Frame):
    def __init__(self, parent, root, videoPaths: list, destFolder: str):
        super().__init__(parent)
        self.parent = parent
        self.root = root
        self.currentVideo = 1

        # instances
        self.background = tk.Canvas(self, background=bg, width=video.WINDOW_WIDTH, height=video.WINDOW_HEIGHT, borderwidth=0, highlightthickness=0)
        self.tFilename = tk.Label(self, text="None")
        self.tFileCount = tk.Label(self, text="0 of 0")
        self.video = video.VideoPlayer(self.root, screenWidth=video.WINDOW_WIDTH, screenHeight=int(1080/2), playOnOpen=False, backgroundHeight=40)
        self.actionBar = ActionBar(self)
        self.footerBar = FooterBar(self, self.currentVideo, len(videoPaths))

        # add listeners
        root.bind('<Button-1>', self.onClick)
        root.bind('<KeyPress>', self.onKeyPress)

        # build     
        root.geometry(str(video.WINDOW_WIDTH) + "x" + str(video.WINDOW_HEIGHT-119))

        self.background.pack()
        self.tFilename.place(x=4, y=2)
        self.tFileCount.place(x=video.WINDOW_WIDTH-40, y=2)
        self.video.place(x=0,y=25, width=self.root.winfo_screenwidth()+10, height=int(self.root.winfo_screenheight()/2) + 40)

        buttonSize = 35
        actionBarWidth = buttonSize * 2 + 200
        self.actionBar.place(x=0, y=600, width=actionBarWidth, height=buttonSize + 20)

        self.footerBar.place(x=video.WINDOW_WIDTH-482, y=614, width=video.WINDOW_WIDTH, height=40)

        # setup video
        self.video.openVideo(videoPaths[self.currentVideo-1])
        self.video.scheduleUpdates()

        # update text files
        self.tFileCount.config(text=f"{self.currentVideo} of {len(videoPaths)}")
        filename = videoPaths[self.currentVideo-1].split("/")[-1][:100]
        self.tFilename.config(text=filename)
        # update times to default
        self.leftTime = 0
        self.rightTime = self.video.player.get_length()

    def onClick(self, event):
        """
            Detects all clicks on the window
        """
        if event.widget != self.footerBar.descBar.box:
            self.footerBar.descBar.isBoxFocused = False
            root.focus()

    def onKeyPress(self, event):
        """
            Bypasses video key presses on text box focus
        """
        if not self.footerBar.descBar.isBoxFocused:
            self.video.onKeyPress(event)


class ResetButton(tk.Frame):
    """
        Resets playback lock to original unrestricted position
    """
    def __init__(self, parent, isLeft: bool, buttonSize: int, clipScene: ClipScene):
        super().__init__(parent)
        self.isLeft = isLeft
        self.clipScene = clipScene

        image = Image.open("images/resetLeft.png" if isLeft else "images/resetRight.png")
        image.thumbnail((buttonSize, buttonSize))
        self.image = ImageTk.PhotoImage(image)

        self.button = tk.Button(self, width=buttonSize, command=self.onClick, image=self.image, borderwidth=0, highlightthickness=0, bg=bg, activebackground=bg)
        self.button.image = self.image

        self.button.pack()

    def onClick(self):
        if self.isLeft:
            self.clipScene.leftTime = 0
        else:
            self.clipScene.rightTime = self.clipScene.video.player.get_length()

        self.clipScene.video.restrictPlayback(self.clipScene.leftTime, self.clipScene.rightTime)

class SetButton(tk.Frame):
    """
        Sets playback lock to current position
    """
    def __init__(self, parent, isLeft: bool, buttonSize: int, clipScene: ClipScene):
        super().__init__(parent)
        self.isLeft = isLeft
        self.clipScene = clipScene

        self.button = tk.Button(self, command=self.onClick, text=f"Set {'Left' if isLeft else 'Right'}", width=10, height=1, bg="#bbbbbb")
        self.button.pack()

    def onClick(self):
        if self.isLeft:
            self.clipScene.leftTime = self.clipScene.video.player.get_time()
        else:
            self.clipScene.rightTime = self.clipScene.video.player.get_time()

        self.clipScene.video.restrictPlayback(self.clipScene.leftTime, self.clipScene.rightTime)
        

            

class ActionBar(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.clipScene = parent

        buttonSize = 35
        self.resetLeft = ResetButton(self, isLeft=True, buttonSize=buttonSize, clipScene=self.clipScene)
        self.resetRight = ResetButton(self, isLeft=False, buttonSize=buttonSize, clipScene=self.clipScene)

        self.setLeft = SetButton(self, isLeft=True, buttonSize=buttonSize, clipScene=self.clipScene)
        self.setRight = SetButton(self, isLeft=False, buttonSize=buttonSize, clipScene=self.clipScene)

        self.resetLeft.grid(column=0, row=0, pady=10)
        self.setLeft.grid(column=1, row=0)
        self.setRight.grid(column=2, row=0)
        self.resetRight.grid(column=3, row=0)

class NextButton(tk.Frame):
    def __init__(self, parent, currentVideo: int, totalVideos: int):
        super().__init__(parent)

        self.button = tk.Button(self, width=10, text="Next" if currentVideo != totalVideos else "Done", command=self.onClick, bg="#bbbbbb")
        self.button.config(state="disabled")
        self.button.pack()

    def onClick(self):
        pass

class DescriptionBar(tk.Frame):
    def __init__(self, parent, nextButton: NextButton):
        super().__init__(parent)
        self.isBoxFocused = False
        self.nextButton = nextButton
        
        self.text = tk.Label(self, text="Description")
        self.boxContents = StringVar()
        self.boxContents.trace_add("write", self.onTextChange)
        self.box = tk.Entry(self, width = 54, textvariable=self.boxContents)

        # add listeners
        self.box.bind('<FocusIn>', self.onFocus)
        self.box.bind('<Return>', self.ignore)

        self.text.grid(column=0, row=0)
        self.box.grid(column=1, row=0, pady=3)

    def onFocus(self, event):
        self.isBoxFocused = True

    def onTextChange(self, *args):
        """
            Called on key press in text box to enforce text rules and update values.
            Enforces text length after including video ordering and file character types
        """

        # enforce text rules here
        #
        maxLength = 10
        text = self.boxContents.get()

        # remove excess text
        if len(text) > maxLength: self.boxContents.set(text[:maxLength])       # do not register
        
        # remove invalid characters
        san_text = sanitize_filepath(text)
        if san_text != text: self.boxContents.set(san_text)

        # update values
        #

        self.nextButton.button.config(state="normal" if len(san_text) > 0 else "disabled")

    def ignore(self, event):
        """
            Used for ignoring keypresses
        """
        return "break"
        

class FooterBar(tk.Frame):
    def __init__(self, parent, currentVideo: int, totalVideos: int):
        super().__init__(parent)

        self.nextButton = NextButton(self, currentVideo=currentVideo, totalVideos=totalVideos)
        self.descBar = DescriptionBar(self, nextButton=self.nextButton)

        self.descBar.grid(column=0, row=0)
        self.nextButton.grid(column=1, row=0)


   





#
# Main
#
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Video Trimmer")
    root.geometry("400x100")
    root.resizable(width=False, height=False)
    root.iconbitmap("images/logo.ico")

    app = MainApp(root)
    app.pack(side="left")
    app.setScene(Scene.SCENE_CLIPS)

    root.mainloop()