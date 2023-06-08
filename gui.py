import tkinter as tk
from tkinter import filedialog
from enum import Enum
import video

class Scene(Enum):
    SCENE_INITIAL = 0
    SCENE_CLIPS = 1








class MainApp(tk.Frame):
    """
        The main gui application
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        # init scenes
        self.scene = None
        self.setScene(Scene.SCENE_INITIAL)

        # data storage
        self.srcFolder = None
        self.destFolder = None


    def setScene(self, scene: Scene):
        if self.scene: self.scene.pack_forget()

        if scene == Scene.SCENE_INITIAL:
            self.scene = InitialScene(self)
        elif scene == Scene.SCENE_CLIPS:
            self.scene = ClipScene(self)

        self.scene.pack()
            


        
        

#
# Initial Scene Elements
#
class InitialScene(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        # instances
        self.srcSelection = FolderSelection(self, "Source Directory")
        self.destSelection = FolderSelection(self, "Destination Directory")
        self.beginButton = BeginButton(self)

        # build
        self.srcSelection.grid(column=0, row=0)
        self.destSelection.grid(column=0, row=1)
        self.beginButton.grid(column=0, row=2, pady=5)

        # properties
        self.hasFolder1 = False
        self.hasFolder2 = False


    def signalFolderSelection(self, caller, folderPath: str):
        """
            Called by the folder selection objects to signal an update on folder selection
        """
        if caller == self.srcSelection:
            self.hasFolder1 = True
            self.parent.srcFolder = folderPath
        elif caller == self.destSelection:
            self.hasFolder2 = True
            self.parent.destFolder = folderPath

        # update button
        self.beginButton.setEnabled(self.hasFolder1 and self.hasFolder2)
        
        


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
        newPath = filedialog.askdirectory()
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
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        # instances
        self.tFilename = tk.Label(self, text="None")
        self.tFileCount = tk.Label(self, text="0 of 0")
        self.video = video.VideoPlayer(root, screenWidth=video.WINDOW_WIDTH, screenHeight=int(1080/2), playOnOpen=False, backgroundHeight=40)

        # build
        self.tFilename.grid(column=0, row=0)
        self.tFileCount.grid(column=1, row=0)
        video.place(x=0,y=0, width=video.WINDOW_WIDTH, height=video.WINDOW_HEIGHT)

        video.openVideo("test-long.mp4")
        video.scheduleUpdates()



   


    

    
        





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