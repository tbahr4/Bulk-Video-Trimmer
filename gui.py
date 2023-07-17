#
# gui.py
#
# Contains the entire application GUI and each scene setup
#

import tkinter as tk
from tkinter import StringVar
from tkinter import filedialog
from enum import Enum
import video
from tkinter import filedialog
from PIL import Image, ImageTk
from pathvalidate import sanitize_filepath
from tkinter import ttk
import logic
from tkinter import font
import os
from tkinter import messagebox
import sys

bg = "#eeeeee"

class Scene(Enum):
    SCENE_INITIAL = 0
    SCENE_CLIPS = 1
    SCENE_TRIM = 2





def getResourcePath(relativePath: str):
    """ 
        Get path to the given resource, needed for temp paths to resources created by pyinstaller
    """
    try:
        basePath = sys._MEIPASS     # PyInstaller creates a temp folder and stores path in _MEIPASS
    except Exception:
        basePath = os.path.abspath(".")

    return os.path.join(basePath, relativePath)

class MainApp(tk.Frame):
    """
        The main gui application
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.root = parent
        self.parent = parent
        self.discordPresence = None
        self.currentScene = Scene.SCENE_INITIAL
        self.savedOptions = None
        
        # init scenes
        self.scene = None
        self.setScene(Scene.SCENE_INITIAL)

        # data storage
        self.videoPaths = None
        self.destFolder = None
        self.trimData = []

    def updateDiscordPresence(self, presence):
        self.discordPresence = presence

        scene = self.getSceneType()
        print(scene == Scene.SCENE_CLIPS)
        if scene == Scene.SCENE_INITIAL:
            self.discordPresence.updateStatus(details="Choosing videos")
        elif scene == Scene.SCENE_CLIPS:
            self.scene.video.discordPresence = presence     # handled by video
        elif scene == Scene.SCENE_TRIM:
            self.discordPresence.updateStatus(details="Trimming videos")

    def setScene(self, scene: Scene):
        self.root.config(menu="") # remove menu
        if self.scene: self.scene.pack_forget()
        self.currentScene = scene
        self.root.state("normal")    # un-maximize window
        

        if scene == Scene.SCENE_INITIAL:
            # if set to initial scene, reset data
            self.videoPaths = None
            self.destFolder = None
            self.trimData = []

            self.unbindAll()

            self.root.geometry("400x100")
            self.root.minsize(400,100)
            self.root.resizable(False, False)
            self.scene = InitialScene(self)
            self.scene.pack(pady=5, fill="both", expand=True)
            if self.discordPresence != None:
                self.discordPresence.updateStatus(details="Choosing videos")
            
        elif scene == Scene.SCENE_CLIPS:
            if __name__ == "__main__" and self.videoPaths == None:
                self.videoPaths = ('test.mp4','test2.mp4','test3.mp4','nosound.mp4','nosound2.mp4')
                self.destFolder = "TestOutput"

            self.scene = ClipScene(self, self.root, self.videoPaths, self.destFolder, discordPresence=self.discordPresence, mainApp=self, optionStates=self.savedOptions)
            self.root.minsize(495,387)
            self.root.resizable(True, True)
            self.scene.pack(fill="both", expand=True)
        elif scene == Scene.SCENE_TRIM:
            self.unbindAll()

            if type(self.scene) == ClipScene:
                self.savedOptions = self.scene.options 
                
            self.scene = TrimScene(self, mainApp=self, options=self.savedOptions)
            self.root.minsize(400,260)
            self.root.resizable(True, True)
            self.scene.pack(fill="both", expand=True)

            if self.discordPresence != None:
                self.after(1000, lambda: self.discordPresence.updateStatus(details="Trimming videos"))
                

    def getSceneType(self):
        if type(self.scene) == InitialScene:
            return Scene.SCENE_INITIAL
        elif type(self.scene) == ClipScene:
            return Scene.SCENE_CLIPS
        elif type(self.scene) == TrimScene:
            return Scene.SCENE_TRIM
        return None
    
    def unbindAll(self):
        """
            Unbinds all events
        """
        self.root.unbind("<KeyPress>")
        self.root.unbind("<FocusIn>")
        self.root.unbind("<FocusOut>")
        self.root.unbind("<Button-1>")
        self.root.unbind("<Button-2>")
        self.root.unbind("<Button-3>")
        self.root.unbind("<ButtonRelease-1>")
        self.root.unbind("<KeyPress>")
        self.root.unbind("<Return>")
        self.root.unbind("<Enter>")
        self.root.unbind("<Leave>")
        self.root.unbind("<B1-Motion>")
        self.root.unbind("<>")

    def closeApp(self):
        self.parent.destroy()
            


        
        

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
        self.srcSelection.pack()
        self.destSelection.pack()
        self.beginButton.pack(expand=True, fill="both", padx=55, pady=7)

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
        self.tFolder = tk.Text(self, height=1, state="disabled", wrap="none")

        # build
        self.bFolder.pack(side="left")
        self.tFolder.pack(side="right")

    def bFile_onClick(self):
        filetypes = [("MP4 Files", "*.mp4")]
        files = filedialog.askopenfilenames(title='Choose videos', filetypes=filetypes)
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
        self.tFolder = tk.Text(self, height=1, state="disabled", wrap="none")

        # build
        self.bFolder.pack(side="left")
        self.tFolder.pack(side="right")

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
        
        self.pixel = tk.PhotoImage(width=1, height=1)    # used to set height in terms of pixels
        self.bBegin = tk.Button(self, image=self.pixel, text="Gather Files", compound="top", command=self.bBegin_onClick, state="disabled") 
        self.bBegin.pack(fill="both", expand=True)

    def bBegin_onClick(self):
        self.parent.parent.setScene(Scene.SCENE_CLIPS)

    def setEnabled(self, value: bool):
        self.bBegin.config(state="active" if value else "disabled")
       
        

#
# Clip Trimming Scene Elements
#
class ClipScene(tk.Frame):
    def __init__(self, parent, root, videoPaths: list, destFolder: str, discordPresence = None, mainApp = None, optionStates: dict = None):
        super().__init__(parent)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.parent = parent
        self.root = root
        self.currentVideo = 1
        self.totalVideos = len(videoPaths)
        self.discordPresence = discordPresence

        # instances
        self.menuBar = tk.Menu(self)
        self.controlMenu = tk.Menu(self.menuBar, tearoff=0)
        self.optionMenu = tk.Menu(self.menuBar, tearoff=0)
        

        # options
        self.options = None
        if optionStates != None:
            self.options = optionStates
        else:
            self.options = dict()

        # alternate track
        cbox_AltTrack = self.options.get("AltTrack")
        if cbox_AltTrack == None:
            cbox_AltTrack = tk.BooleanVar()
            self.options["AltTrack"] = cbox_AltTrack
        def onClick_AltTrack():
            isEnabled = cbox_AltTrack.get()
            if self.video.player.audio_get_track_count() >= 3:
                self.video.player.audio_set_track(2 if isEnabled else 1) 
                
        self.optionMenu.add_checkbutton(label="Alternate audio track", variable=cbox_AltTrack, command=onClick_AltTrack)
        # autoplay
        cbox_Autoplay = self.options.get("Autoplay")
        if cbox_Autoplay == None:
            cbox_Autoplay = tk.BooleanVar()
            self.options["Autoplay"] = cbox_Autoplay
        def onClick_Autoplay():
            isEnabled = cbox_Autoplay.get()
            self.video.playOnOpen = isEnabled
        self.optionMenu.add_checkbutton(label="Autoplay", variable=cbox_Autoplay, command=onClick_Autoplay)
        # loop playback
        cbox_LoopPlayback = self.options.get("LoopPlayback")
        if cbox_LoopPlayback == None:
            cbox_LoopPlayback = tk.BooleanVar()
            self.options["LoopPlayback"] = cbox_LoopPlayback
        self.optionMenu.add_checkbutton(label="Loop playback", variable=cbox_LoopPlayback)
        # Allow unnamed files
        cbox_AllowUnnamedFiles = self.options.get("AllowUnnamedFiles")
        if cbox_AllowUnnamedFiles == None:
            cbox_AllowUnnamedFiles = tk.BooleanVar()
            self.options["AllowUnnamedFiles"] = cbox_AllowUnnamedFiles
        def onClick_AllowUnnamedFiles():
            isEnabled = cbox_AllowUnnamedFiles.get()
            currState = self.footerBar.nextButton.button["state"]
            if (isEnabled or len(self.footerBar.descBar.boxContents.get()) > 0) and currState != "normal":
                self.footerBar.nextButton.button.config(state="normal")
            elif not (isEnabled or len(self.footerBar.descBar.boxContents.get()) > 0) and currState != "disabled":
                self.footerBar.nextButton.button.config(state="disabled")

            currState = self.controlMenu.entrycget("Save clip", "state")

            if not (isEnabled or len(self.footerBar.descBar.boxContents.get()) > 0) and currState != "disabled":
                self.controlMenu.entryconfigure("Save clip", state='disabled')
            elif (isEnabled or len(self.footerBar.descBar.boxContents.get()) > 0) and currState != "normal":
                self.controlMenu.entryconfigure("Save clip", state='normal')
        self.optionMenu.add_checkbutton(label="Allow unnamed files", variable=cbox_AllowUnnamedFiles, command=onClick_AllowUnnamedFiles)
        # change arrow key functionality
        self.optionMenu.add_separator()
        self.seekSpeedMenu = tk.Menu(self.optionMenu, tearoff=0)
        selectedSeekSpeed = self.options.get("SeekTime")
        if selectedSeekSpeed == None:
            selectedSeekSpeed = tk.IntVar(None, 5000)
            self.options["SeekTime"] = selectedSeekSpeed
        self.seekSpeedMenu.add_radiobutton(label="1s", variable=selectedSeekSpeed, value=1000)
        self.seekSpeedMenu.add_radiobutton(label="5s (default)", variable=selectedSeekSpeed, value=5000)
        self.seekSpeedMenu.add_radiobutton(label="10s", variable=selectedSeekSpeed, value=10000)
        self.optionMenu.add_cascade(label="Set seek time", menu=self.seekSpeedMenu)
        # Label silent clips
        self.optionMenu.add_separator()
        cbox_LabelMutedClips = self.options.get("LabelSilentClips")
        if cbox_LabelMutedClips == None:
            cbox_LabelMutedClips = tk.BooleanVar()
            self.options["LabelSilentClips"] = cbox_LabelMutedClips
        def onClick_LabelSilentClips():
            isEnabled = cbox_LabelMutedClips.get()
            if isEnabled:
                messagebox.showinfo("Automatic Labeling", "Automatic labeling of clips requires some extra processing for each clip. This will take some time especially with clips of longer duration.")
        self.optionMenu.add_checkbutton(label="Label silent clips", variable=cbox_LabelMutedClips, command=onClick_LabelSilentClips)
        


        # pack bools and option functions into list for later, bools specify if the function will be auto-updated
        self.optionFunctions = {
            "onClick_AltTrack": {
                "Function": onClick_AltTrack, 
                "AutoUpdate": True
            },
            "onClick_Autoplay": {
                "Function": onClick_Autoplay,
                "AutoUpdate": True
            },
            "onClick_AllowUnnamedFiles": {
                "Function": onClick_AllowUnnamedFiles,
                "AutoUpdate": True
            },
            "onClick_LabelSilentClips": {
                "Function": onClick_LabelSilentClips,
                "AutoUpdate": False
            }
        }



        self.actionBar = ActionBar(self)
        self.footerBar = FooterBar(self, clipScene=self, mainApp=self.parent)
        self.framePerfectButton = FramePerfectButton(self)

        self.controlMenu.add_command(label="Controls", command=self.displayVideoControls)
        self.controlMenu.add_separator()
        self.controlMenu.add_command(label="Skip", command=self.promptSkip)
        self.controlMenu.add_command(label="Skip all", command=self.promptSkipAll)
        self.controlMenu.add_command(label="Save clip", command=self.saveClip, state="disabled" if not self.options["AllowUnnamedFiles"].get() else "normal")
        self.controlMenu.add_command(label="Previous video", command=lambda: self.footerBar.nextButton.onClick(skipTrim=True, nextVideo=False, prevVideo=True), state="disabled")

        self.menuBar.add_cascade(label="Menu", menu=self.controlMenu)
        self.menuBar.add_cascade(label="Options", menu=self.optionMenu)
        self.parent.root.config(menu=self.menuBar)

        # create video player
        self.video = video.VideoPlayer(self, root=root, playOnOpen=self.options["Autoplay"].get(), restrictLeftButton=self.actionBar.setLeft, restrictRightButton=self.actionBar.setRight, unrestrictLeftButton=self.actionBar.resetLeft, unrestrictRightButton=self.actionBar.resetRight, clipScene=self, menuBar=self.menuBar, discordPresence=self.discordPresence, mainApp=mainApp)


        



        # add listeners
        self.root.bind('<Button-1>', self.onClick)
        self.root.bind('<KeyPress>', self.onKeyPress)

        # build     
        self.root.geometry(str(video.WINDOW_WIDTH) + "x" + str(video.WINDOW_HEIGHT))


        self.video.grid(column=0, row=1, sticky='nesw', columnspan=3)

        # top bar
        self.topBar = tk.Frame(self, height=25)
        self.topBar.grid(column=0, row=0, sticky='nesw')
        self.tFilename = tk.Label(self, text="None")
        self.tFileCount = tk.Label(self, text="0 of 0")
        
        self.tFilename.place(x=4, y=2)
        self.root.update()

        self.actionBar.grid(column=0, row=2, sticky='nesw')
        self.framePerfectButton.grid(column=1, row=2, sticky='nesw')
        self.footerBar.grid(column=2, row=2, sticky="nesw")


        # setup video
        self.video.openVideo(videoPaths[self.currentVideo-1])
        self.video.scheduleUpdates()

        # update text files
        self.tFileCount.config(text=f"{self.currentVideo} of {len(videoPaths)}")
        filename = videoPaths[self.currentVideo-1].split("/")[-1][:100]
        self.tFilename.config(text=os.path.basename(filename))
        # replace file count to fit
        self.root.update()
        self.tFileCount.place(x=self.video.winfo_width()-5-self.tFileCount.winfo_width(), y=2)
        # update times to default
        self.leftTime = 0
        self.rightTime = self.video.player.get_length()

        # bindings
        self.bind("<Configure>", self.onResize)


    def onResize(self, event):
        """
            Called whenever the window is resized/configured
        """
        if self.video.bFullscreen.isFullscreen:
            return      # do not update

        self.root.update()

        defaultSize = video.WINDOW_WIDTH, video.WINDOW_HEIGHT
        newSize = (self.root.winfo_width(), self.root.winfo_height())
        scale = newSize[0]/defaultSize[0], newSize[1]/defaultSize[1]
        FRAME_PERFECT_THRESHOLD = 908
        ACTION_BAR_THRESHOLD = 715

        self.root.update()
        self.tFileCount.place(x=self.video.winfo_width()-5-self.tFileCount.winfo_width(), y=2)

        if newSize[0] < FRAME_PERFECT_THRESHOLD:
            self.framePerfectButton.place_forget()
            self.framePerfectButton.grid_forget()
        else:
            PADDING_THRESHOLD = 985
            difference = newSize[0] - PADDING_THRESHOLD

            if difference < 0:
                self.framePerfectButton.button.pack(padx=0)
                self.framePerfectButton.place(x=223, y=self.video.winfo_y() + self.video.winfo_height())
                self.root.update()
            else:
                self.framePerfectButton.grid(column=1, row=2, sticky='nesw')
                self.framePerfectButton.button.pack(padx=(0,74 + min(0, difference)))




        if newSize[0] < ACTION_BAR_THRESHOLD:
            self.actionBar.grid_forget()
        else:
            self.actionBar.grid(column=0, row=2, sticky='nesw')

    def updateOptions(self):
        """
            Updates the currently set options on the current video
        """
        for item in self.optionFunctions.keys():
            function = self.optionFunctions[item]["Function"]
            autoUpdate = self.optionFunctions[item]["AutoUpdate"]
            if autoUpdate:
                function()


    def onClick(self, event):
        """
            Detects all left clicks on the window
        """
        if event.widget != self.footerBar.descBar.box:
            self.footerBar.descBar.isBoxFocused = False
            self.root.focus()

        if event.widget == self.video.canvas:
            self.video.onClick(event=event)

    def onKeyPress(self, event):
        """
            Bypasses video key presses on text box focus
        """
        if event.keysym == "grave" and self.footerBar.descBar.isBoxFocused: 
            self.video.onKeyPress(event)
            return

        if not self.footerBar.descBar.isBoxFocused:
            self.video.onKeyPress(event)

    def displayVideoControls(self):
        controls = {"Space": "Play/Pause", "\u2190": "Seek left", "\u2192": "Seek right", "\u2191": "Volume up", "\u2193": "Volume down", "F": "Fullscreen", "Esc": "Leave fullscreen", "Home": "Seek to start", "End": "Seek to last 20s", ",": "Rewind 1 frame", ".": "Seek 1 frame ahead", "M": "Toggle mute", "0-9": "Seek", "E/R": "Set trim position", "Ctrl+E/R": "Reset trim position", "Shift+E/R": "Shift current trim position", "Enter": "Next video"}
        maxLen = 20
        tab = '\t'
        messagebox.showinfo("Video Controls", "".join(f"{key:{6}}\t{tab if len(key) <= 8 else ''}{value}\n" for key, value in controls.items()))     

    def promptSkip(self):
        """
            Skips the current clip
        """
        self.footerBar.nextButton.onClick(skipTrim=True, nextVideo=True, prevVideo=False, forceProcess=True)

    def promptSkipAll(self):
        """
            Prompts the user if they want to skip the rest of the clips and trim, also ignores current clip
        """  
        result = messagebox.askokcancel("Skip all", "Skip the rest of the videos and begin trimming?")
        if result == True:
            self.video.isVideoOpened = False
            self.video.player.stop()
            self.parent.setScene(Scene.SCENE_TRIM)

    def saveClip(self):
        """
            To be used to save the current clip without moving to the next video
        """
        self.footerBar.nextButton.onClick(skipTrim=False, nextVideo=False, prevVideo=False)
        
        # special case: remove cursor from description box
        self.footerBar.descBar.isBoxFocused = False
        self.root.focus()

            

class FramePerfectButton(tk.Frame):
    """
        Toggleable button that specifies that the given clip should be frame perfect
    """
    def __init__(self, parent):
        super().__init__(parent, bg=bg)
        self.isSet = tk.IntVar()

        self.button = tk.Checkbutton(self, text="Enable frame perfect trim (slow)", variable=self.isSet, pady=10)
        self.button.pack(padx=(0,74))

class ResetButton(tk.Frame):
    """
        Resets playback lock to original unrestricted position
    """
    def __init__(self, parent, isLeft: bool, buttonSize: int, clipScene: ClipScene):
        super().__init__(parent)
        self.isLeft = isLeft
        self.clipScene = clipScene

        image = Image.open(getResourcePath("images/resetLeft.png") if isLeft else getResourcePath("images/resetRight.png"))
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
        if self.clipScene.video.player.get_position() == 0 and not self.isLeft: return
        if self.clipScene.video.player.get_time() >= self.clipScene.video.player.get_length()-1000 and self.isLeft: return

        if self.isLeft:
            self.clipScene.leftTime = self.clipScene.video.player.get_time()
        else:
            self.clipScene.rightTime = self.clipScene.video.player.get_time()

        self.clipScene.video.restrictPlayback(self.clipScene.leftTime, self.clipScene.rightTime)

    def shiftLock(self, time):
        """
            Shifts the lock by the given time, if on a boundary, sets its to that boundary
            Does nothing if lock is not already set
        """
        if not self.clipScene.video.enableRestrictedPlayback: return

        if self.clipScene.video.player.get_position() == 0 and not self.isLeft: return
        if self.clipScene.video.player.get_time() >= self.clipScene.video.player.get_length()-1000 and self.isLeft: return

        duration = self.clipScene.video.player.get_length()

        if time > 0 and self.isLeft and self.clipScene.leftTime + time > duration:
            self.clipScene.leftTime = duration 
        elif time > 0 and not self.isLeft and self.clipScene.rightTime + time > duration:
            self.clipScene.rightTime = duration
        elif time < 0 and self.isLeft and self.clipScene.leftTime + time < 0:
            self.clipScene.leftTime = 0
        elif time < 0 and not self.isLeft and self.clipScene.rightTime + time < 0:
            self.clipScene.rightTime = 0
        else:
            if self.isLeft:
                self.clipScene.leftTime += time
            else:
                self.clipScene.rightTime += time

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

        self.resetLeft.grid(column=0, row=0)
        self.setLeft.grid(column=1, row=0, pady=9)
        self.setRight.grid(column=2, row=0)
        self.resetRight.grid(column=3, row=0)

class NextButton(tk.Frame):
    def __init__(self, parent, clipScene: ClipScene, mainApp: MainApp):
        super().__init__(parent)
        self.parent = parent
        self.clipScene = clipScene
        self.mainApp = mainApp
        self.allowClicks = True

        self.button = tk.Button(self, width=10, text="Next" if self.clipScene.currentVideo != self.clipScene.totalVideos else "Done", command=lambda: self.onClick(skipTrim=False, nextVideo=True, prevVideo=False, forceProcess=True), bg="#bbbbbb")
        self.button.config(state="disabled" if not self.clipScene.options["AllowUnnamedFiles"].get() else "normal")
        self.button.pack()

    def onClick(self, skipTrim: bool, nextVideo: bool, prevVideo: bool, forceProcess: bool = False):
        """
            skipTrim: Processes the click but ignores the current video for trimming
            nextVideo: Processes the click but does not move to the next video
        """
        if not self.allowClicks and not forceProcess: return
        self.allowClicks = False

        # pause video
        if not self.parent.parent.video.actionBar.bPause.isPaused:
            self.parent.parent.video.actionBar.bPause.togglePause()

        # disable double press
        self.button.config(state="disabled")
        self.clipScene.footerBar.descBar.box.config(state="disabled")

        # sanitize input once more
        san_text = sanitize_filepath(self.clipScene.footerBar.descBar.boxContents.get())
        self.clipScene.footerBar.descBar.boxContents.set(san_text)

        # if no name provided, default to previous name
        if len(san_text) == 0: 
            path = self.mainApp.videoPaths[self.clipScene.currentVideo-1]
            san_text = os.path.basename(path).rsplit(".", 1)[0]

        # save picked times
        if not skipTrim:
            self.mainApp.trimData.append(dict([("videoNumber", self.clipScene.currentVideo), ("description", san_text), ("startTime", self.clipScene.leftTime), ("endTime", self.clipScene.rightTime), ("fullVideoLength", self.clipScene.video.player.get_length()), ("isFramePerfect", self.clipScene.framePerfectButton.isSet.get() == 1), ("inputPath", self.mainApp.videoPaths[self.clipScene.currentVideo-1])]))

        if nextVideo or prevVideo:

            # update video
            self.clipScene.currentVideo += 1 if nextVideo else -1   # +1 if nextVideo / -1 if prevVideo

            # if prevVideo, remove previous clip as well
            previousData = None
            if prevVideo:
                # remove ALL clips from current video, and the first clip from the previous (if possible)
                while len(self.mainApp.trimData) > 0:
                    lastData = self.mainApp.trimData[-1]        # grab last video

                    if lastData["videoNumber"] > self.clipScene.currentVideo:
                        self.mainApp.trimData.pop()
                    elif lastData["videoNumber"] == self.clipScene.currentVideo:
                        previousData = self.mainApp.trimData.pop()
                        break
                    else:
                        # passed video, no clip of previous video
                        break
                        

            # update previous video button
            self.clipScene.controlMenu.entryconfigure("Previous video", state='normal' if self.clipScene.currentVideo > 1 else 'disabled')

            if self.clipScene.currentVideo > self.clipScene.totalVideos:  # done
                # leave fullscreen
                if self.parent.parent.video.bFullscreen.isFullscreen:
                    self.parent.parent.video.bFullscreen.toggleFullscreen(forceToggle=True)

                self.parent.parent.video.isVideoOpened = False
                self.parent.parent.video.player.stop()
                self.mainApp.setScene(Scene.SCENE_TRIM)
            else:

                # update text
                self.button.config(text="Next" if self.clipScene.currentVideo != self.clipScene.totalVideos else "Done")
                self.clipScene.tFileCount.config(text=f"{self.clipScene.currentVideo} of {self.clipScene.totalVideos}")
                filename = self.mainApp.videoPaths[self.clipScene.currentVideo-1].split("/")[-1][:100]
                self.clipScene.tFilename.config(text=os.path.basename(filename))
                self.clipScene.footerBar.descBar.boxContents.set("")

                # reset frame perfect check
                self.clipScene.framePerfectButton.isSet.set(0)

                # replace file count to fit
                self.mainApp.root.update()
                if not self.parent.parent.video.bFullscreen.isFullscreen:
                    self.clipScene.tFileCount.place(x=self.clipScene.video.winfo_width()-5-self.clipScene.tFileCount.winfo_width(), y=2)

                # update video
                self.clipScene.video.openVideo(self.mainApp.videoPaths[self.clipScene.currentVideo-1])

                # if returninto to prevVideo, load previous settings
                if prevVideo and previousData is not None:
                    self.parent.descBar.boxContents.set(previousData["description"])
                    self.parent.parent.video.restrictPlayback(previousData["startTime"], previousData["endTime"])
                    self.parent.parent.framePerfectButton.isSet.set(previousData["isFramePerfect"])
                    self.parent.parent.video._setPlayerPosition(0)

                # reenable text entry
                self.clipScene.footerBar.descBar.box.config(state="normal")
        else:
            # do not transition to the next video, just reset data
            self.clipScene.footerBar.descBar.boxContents.set("")    # reset description
            self.clipScene.framePerfectButton.isSet.set(0)          # reset frame perfect check
            self.clipScene.footerBar.descBar.box.config(state="normal")     # reenable text entry

            # reset restrictions
            self.clipScene.video.unrestrictPlayback()

            # re-pause if not already set
            if not self.parent.parent.video.actionBar.bPause.isPaused:
                self.parent.parent.video.actionBar.bPause.togglePause()

        # reenable clicks, or wait if empty inputs is enabled
        if self.parent.parent.options["AllowUnnamedFiles"].get():
            self.after(1000, lambda: setattr(self, "allowClicks", True))
        else:
            self.allowClicks = True
        
       


class DescriptionBar(tk.Frame):
    def __init__(self, parent, nextButton: NextButton):
        super().__init__(parent)
        self.parent = parent
        self.isBoxFocused = False
        self.nextButton = nextButton
        
        self.text = tk.Label(self, text="Description")
        self.boxContents = StringVar()
        self.boxContents.trace_add("write", self.onTextChange)
        self.box = tk.Entry(self, width = 54, textvariable=self.boxContents)

        # add listeners
        self.box.bind('<FocusIn>', self.onFocus)
        self.box.bind('<Return>', self.onReturnKey)

        self.text.grid(column=0, row=0)
        self.box.grid(column=1, row=0, pady=3)

    def onReturnKey(self, event):
        """
            Called when the enter key is detected by this widget
        """
        if self.nextButton.button["state"] == "normal":
            self.nextButton.onClick(skipTrim=False, nextVideo=True, prevVideo=False)     

        # return cursor
        self.isBoxFocused = False
        self.parent.parent.parent.parent.focus()

    def onFocus(self, event):
        self.isBoxFocused = True

    def onTextChange(self, *args):
        """
            Called on key press in text box to enforce text rules and update values.
            Enforces text length after including video ordering and file character types
        """

        # enforce text rules here
        #
        maxLength = 100
        text = self.boxContents.get()
        if text == "":
            self.nextButton.button.config(state="disabled" if not self.parent.clipScene.options["AllowUnnamedFiles"].get() else "normal")
            self.parent.parent.controlMenu.entryconfigure("Save clip", state='disabled' if not self.parent.clipScene.options["AllowUnnamedFiles"].get() else "normal")
            return

        # check if key should instead be handled by the key manager
        #
        if '`' in text:     # grave
            self.boxContents.set(text.replace('`', ''))
            return

        # remove excess text
        if len(text) > maxLength: 
            text = text[:maxLength]
            self.boxContents.set(text)       # do not register
        
        # remove invalid characters

        # remove slashes
        builtString = ""
        for char in text:
            if char not in ["/","\\"]: builtString += char
        if text != builtString:
            text = builtString
            cursor = self.box.index(tk.INSERT)
            self.box.icursor(max(0, cursor-1))


        textRetain = text + "Z"     # retains all spaces at end of string
        san_text = sanitize_filepath(textRetain)
        san_text = san_text[:-1]

        cursor = self.box.index(tk.INSERT) + (1 if len(san_text) == len(text) else 0)
        self.boxContents.set(san_text)
        self.box.icursor(min(max(0, cursor-1), len(san_text)))


        # update values
        #
        
        # enable if nonspace char exists in text field
        hasNonSpaceChar = False
        for char in san_text:
            if not char.isspace():
                hasNonSpaceChar = True
                break

        self.nextButton.button.config(state="normal" if len(san_text) > 0 and hasNonSpaceChar else "disabled")
        self.nextButton.allowClicks = True
        self.parent.parent.controlMenu.entryconfigure("Save clip", state='normal' if len(san_text) > 0 and hasNonSpaceChar else "disabled")
        

class FooterBar(tk.Frame):
    def __init__(self, parent, clipScene: ClipScene, mainApp: MainApp):
        super().__init__(parent)
        self.parent = parent
        self.clipScene = clipScene

        self.nextButton = NextButton(self, clipScene=clipScene, mainApp=mainApp)
        self.descBar = DescriptionBar(self, nextButton=self.nextButton)

        self.descBar.grid(column=0, row=0)
        self.nextButton.grid(column=1, row=0, padx=8, pady=9)

class TrimScene(tk.Frame):
    def __init__(self, parent, mainApp: MainApp, options: list = None):
        super().__init__(parent)
        self.parent = parent
        self.mainApp = mainApp
        self.parent.parent.geometry("400x260")
        self.root = parent.parent
        self.options = options
        font = ("Helvetica", 10)

        # instances
        self.filename = tk.Label(self, text="Status: Waiting", font=("Helvetica", 9))
        self.filename.pack(anchor="w")

        self.remainder = tk.Label(self, text=f"Remaining: {len(self.mainApp.trimData)}", font=("Helvetica", 9))
        self.remainder.pack(anchor="w")

        self.outputHeader = tk.Label(self, text="Output", font=font)
        self.outputHeader.pack(anchor="w")

        self.output = OutputConsole(self)
        self.output.pack(fill="both", expand=True)

        self.buttonFrame = tk.Frame(self)
        self.buttonFrame.pack(anchor="e")

        self.skipButton = tk.Button(self.buttonFrame, command=self.skipButtonOnClick, text="Skip", width=9, height=1)
        self.skipButton.grid(column=0, row=0)
        self.skipButton.grid_forget()       # hide until needed

        self.restartButton = tk.Button(self.buttonFrame, command=self.restartButtonOnClick, text="Restart", width=9, height=1)
        self.restartButton.grid(column=0, row=0)
        self.restartButton.grid_forget()       # hide until needed

        self.startButton = tk.Button(self.buttonFrame, command=self.startButtonOnClick, text="Start", width=9, height=1)
        self.startButton.grid(column=1, row=0)

        self.progressBar = ProgressBar(self)
        self.progressBar.pack(side="bottom", pady=0)

        # properties
        self.videoCount = 0
        self.a = False

        # add event bindings
        self.bind("<Configure>", self.onResize)

    def onResize(self, event):
        """
            Called whenever the window is resized/configured
        """
        self.root.update()
        self.progressBar.bar.config(length=self.root.winfo_width())         

    def skipButtonOnClick(self):
        self.skipButton.grid_forget()   # hide skip button

        # update progress bar
        self.videoCount += 1
        self.progressBar.bar["value"] = self.videoCount / len(self.mainApp.trimData) * 100
        self.progressBar.update()
        self.root.update_idletasks()

        # start next video
        self.startButtonOnClick()

    def restartButtonOnClick(self):
        self.mainApp.setScene(Scene.SCENE_INITIAL)



    def startButtonOnClick(self):
        self.startButton.config(text="Start", state="disabled")
        self.skipButton.grid_forget()   # hide skip button

        # perform trim on all videos
        for trimData in self.mainApp.trimData[self.videoCount:]:
            inputPath = trimData["inputPath"]
            maxOrder = self.getFileOrder(self.mainApp.destFolder)  
            startTime = trimData["startTime"] / 1000
            endTime = trimData["endTime"] / 1000
            

            # update visual data
            stringWidth = font.Font().measure(trimData["description"])
            trimmedText = trimData["description"]
            self.root.update()
            trimWidth = self.root.winfo_width()
            while stringWidth > trimWidth:
                trimmedText = trimmedText[:-1]
                stringWidth = font.Font().measure(trimmedText)
            self.filename.config(text=f"Status: {trimmedText}{'...' if font.Font().measure(trimData['description']) > trimWidth else ''}")

            isSilent = False
            if self.options != None:
                if self.options["LabelSilentClips"].get():
                    self.log(f"Checking for silence in \"{trimData['description']}\"")
                    isSilent = logic.checkIsSilent(inputPath, startTime, endTime, trimScene=self)     # check if clip is silent
            outputPath = f"{self.mainApp.destFolder}/({maxOrder}) {'(no sound) ' if isSilent else ''}{trimData['description']}.mp4"
            isFramePerfect = trimData["isFramePerfect"]

            self.remainder.config(text=f"Remaining: {len(self.mainApp.trimData) - self.videoCount}")
            self.log(f"Trimming ({maxOrder}) \"{trimData['description']}\" [{round(startTime)} - {round(endTime)}] {'and re-encoding' if isFramePerfect else ''}")
            self.filename.update()
            self.remainder.update()
            self.output.output.update()
            self.root.update_idletasks()

            isVideoProcessed = False
            
            try:
                logic.trimVideo(inputPath=inputPath, outputPath=outputPath, startTime=startTime, endTime=endTime, isFramePerfect=isFramePerfect, fullVideoLength=trimData['fullVideoLength'], trimScene=self)
                isVideoProcessed = True
            except Exception as e:
                self.log(f"[ERROR] Trimming failed: {e}")

                # delete unprocessed file if needed
                if os.path.exists(outputPath):
                    self.log(f"[WARNING] File remains in directory {outputPath}")

            # prompt to try again or skip if not completed
            if not isVideoProcessed:
                self.startButton.config(state="normal", text="Try Again")
                self.skipButton.grid(column=0, row=0)       # display skip button
                return


            # done, update progress bar
            self.videoCount += 1
            self.progressBar.bar["value"] = self.videoCount / len(self.mainApp.trimData) * 100
            self.progressBar.update()
            self.root.update_idletasks()

        # update visual data
        self.filename.config(text="Status: Done")
        self.remainder.config(text="Remaining: 0")
        self.log("Done.")

        # update button to close
        self.startButton.config(state="normal", text="Close", command=self.mainApp.closeApp)

        # add reset button
        self.restartButton.grid(column=0, row=0)

    def log(self, message: str):
        """
            Displays the log message to both the console and screen
        """
        print(message)      # print to console 

        # print to gui console
        self.output.output.configure(state="normal")
        self.output.output.insert(tk.END, f"{message}\n")        
        self.output.output.configure(state="disabled")
        self.output.output.see(tk.END)
            
    def getFileOrder(self, directoryPath: str):
        """
            Returns the highest file number within the directory path +1.
            The file number is given by (X) before the filenames
        """
        files = os.listdir(directoryPath)
        
        maxOrder = 0
        for file in files:
            if len(file) < 3: continue
            if file[0] != '(': continue

            split = file.split(')')[0]
            if len(split) == len(file): continue
            split = split[1:]

            if not split.isnumeric: continue
            split = float(split)
            if split != int(split): continue
            value = int(split)
            
            if value > maxOrder: maxOrder = value

        return maxOrder + 1 
        

        
        
class OutputConsole(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        font = ("Helvetica", 10)

        # instances
        self.scrollBar = tk.Scrollbar(self, orient="vertical")
        self.scrollBar.pack(side="right", fill="y")

        self.output = tk.Text(self, state="disabled", font=font, wrap="none", height=10)
        self.output.pack(side="left", fill="both", expand=True)

        self.output.config(yscrollcommand=self.scrollBar.set)
        self.scrollBar.configure(command=self.output.yview)

class ProgressBar(tk.Frame):
    style = None

    def __init__(self, parent):
        super().__init__(parent)

        # styling for the progress bar
        if ProgressBar.style == None:
            ProgressBar.style = ttk.Style()
            ProgressBar.style.theme_create("style", parent="default", settings={
                "TProgressbar": {
                    "configure": {
                        "background": "lime",
                        "troughcolor": "grey",
                        "borderwidth": 1,
                        "thickness": 2
                    }
                }
            })
            ProgressBar.style.theme_use("style")

        self.bar = ttk.Progressbar(self, mode="determinate", maximum=100, length=400)
        self.bar.pack()

        




#
# Main
#
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Bulk Video Trimmer")
    root.geometry("400x100")
    root.iconbitmap(getResourcePath("images/logo.ico"))
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    app = MainApp(root)
    app.grid(column=0, row=0, sticky="nesw")
    

    app.setScene(Scene.SCENE_CLIPS)

    root.mainloop()