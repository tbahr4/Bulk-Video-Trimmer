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
        self.root = parent
        self.parent = parent
        
        # init scenes
        self.scene = None
        self.setScene(Scene.SCENE_INITIAL)

        # data storage
        self.videoPaths = None
        self.destFolder = None
        self.trimData = []


    def setScene(self, scene: Scene):
        self.root.config(menu="") # remove menu
        if self.scene: self.scene.pack_forget()

        if scene == Scene.SCENE_INITIAL:
            if type(self.scene) == ClipScene:
                self.scene.video.place_forget()
                self.root.unbind("<KeyPress>")
                self.root.unbind("<FocusIn>")
            self.root.unbind('<Button-1>')
            self.root.unbind('<KeyPress>')

            self.root.geometry(f"{400}x{100}")
            self.scene = InitialScene(self)
            self.scene.pack(pady=5, fill="both", expand=True)
            
        elif scene == Scene.SCENE_CLIPS:
            self.scene = ClipScene(self, self.root, self.videoPaths, self.destFolder)
            self.scene.pack(fill="both", expand=True)
        elif scene == Scene.SCENE_TRIM:
            if type(self.scene) == ClipScene:
                self.scene.video.place_forget()
                self.root.unbind("<KeyPress>")
                self.root.unbind("<FocusIn>")
            self.root.unbind('<Button-1>')
            self.root.unbind('<KeyPress>')

            self.scene = TrimScene(self, mainApp=self)
            self.scene.pack(fill="both", expand=True)
    
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
    def __init__(self, parent, root, videoPaths: list, destFolder: str):
        super().__init__(parent)
        self.parent = parent
        self.root = root
        self.currentVideo = 1
        self.totalVideos = len(videoPaths)

        # video and surrounding instances
        self.background = tk.Canvas(self, background=bg, width=video.WINDOW_WIDTH, height=video.WINDOW_HEIGHT, borderwidth=0, highlightthickness=0)
        self.tFilename = tk.Label(self, text="None")
        self.tFileCount = tk.Label(self, text="0 of 0")
        self.actionBar = ActionBar(self)
        self.footerBar = FooterBar(self, clipScene=self, mainApp=self.parent)
        self.framePerfectButton = FramePerfectButton(self)

        # instances
        self.menuBar = tk.Menu(self)
        self.controlMenu = tk.Menu(self.menuBar, tearoff=0)
        self.optionMenu = tk.Menu(self.menuBar, tearoff=0)
        self.controlMenu.add_command(label="Controls", command=self.displayVideoControls)
        self.controlMenu.add_separator()
        self.controlMenu.add_command(label="Skip", command=self.promptSkip)
        self.controlMenu.add_command(label="Skip all", command=self.promptSkipAll)
        self.controlMenu.add_command(label="Save clip", command=self.saveClip, state="disabled")
        self.controlMenu.add_command(label="Previous video", command=lambda: self.footerBar.nextButton.onClick(skipTrim=True, nextVideo=False, prevVideo=True), state="disabled")

        # options
        # alternate track
        cbox_AltTrack = tk.BooleanVar()
        def onClick_AltTrack():
            isEnabled = cbox_AltTrack.get()
            if self.video.player.audio_get_track_count() >= 3:
                    self.optionMenu.entryconfigure("Alternate audio track", state='normal')
                    self.video.player.audio_set_track(2 if isEnabled else 1) 
            else: 
                cbox_AltTrack.set(False)
                self.optionMenu.entryconfigure("Alternate audio track", state='disabled')
        self.optionMenu.add_checkbutton(label="Alternate audio track", variable=cbox_AltTrack, command=onClick_AltTrack)
        # autoplay
        cbox_Autoplay = tk.BooleanVar()
        def onClick_Autoplay():
            isEnabled = cbox_Autoplay.get()
            self.video.playOnOpen = isEnabled
        self.optionMenu.add_checkbutton(label="Autoplay", variable=cbox_Autoplay, command=onClick_Autoplay)
        # loop playback
        cbox_LoopPlayback = tk.BooleanVar()
        self.optionMenu.add_checkbutton(label="Loop Playback", variable=cbox_LoopPlayback)
        # change arrow key functionality
        self.optionMenu.add_separator()
        self.seekSpeedMenu = tk.Menu(self.optionMenu, tearoff=0)
        selectedSeekSpeed = tk.IntVar(None, 10000)
        self.seekSpeedMenu.add_radiobutton(label="1s", variable=selectedSeekSpeed, value=1000)
        self.seekSpeedMenu.add_radiobutton(label="5s", variable=selectedSeekSpeed, value=5000)
        self.seekSpeedMenu.add_radiobutton(label="10s (default)", variable=selectedSeekSpeed, value=10000)
        self.optionMenu.add_cascade(label="Set seek time", menu=self.seekSpeedMenu)


        # pack bools and option functions into list for later
        self.options = {"AltTrack": cbox_AltTrack, "Autoplay": cbox_Autoplay, "LoopPlayback": cbox_LoopPlayback, "SeekTime": selectedSeekSpeed}
        self.optionFunctions = [onClick_AltTrack, onClick_Autoplay]


        self.menuBar.add_cascade(label="Menu", menu=self.controlMenu)
        self.menuBar.add_cascade(label="Options", menu=self.optionMenu)
        self.parent.root.config(menu=self.menuBar)

        # create video player
        self.video = video.VideoPlayer(self.root, screenWidth=video.WINDOW_WIDTH, screenHeight=int(1080/2), playOnOpen=False, backgroundHeight=40, restrictLeftButton=self.actionBar.setLeft, restrictRightButton=self.actionBar.setRight, unrestrictLeftButton=self.actionBar.resetLeft, unrestrictRightButton=self.actionBar.resetRight, clipScene=self, menuBar=self.menuBar)

        # add listeners
        self.root.bind('<Button-1>', self.onClick)
        self.root.bind('<KeyPress>', self.onKeyPress)

        # build     
        self.root.geometry(str(video.WINDOW_WIDTH) + "x" + str(video.WINDOW_HEIGHT))

        self.background.pack()
        self.tFilename.place(x=4, y=2)
        self.tFileCount.place(x=video.WINDOW_WIDTH-40, y=2)
        self.video.place(x=0,y=25, width=self.video.screenWidth, height=self.video.screenHeight + 40)

        buttonSize = 35
        actionBarWidth = buttonSize * 2 + 200
        self.actionBar.place(x=0, y=600, width=actionBarWidth, height=buttonSize + 20)

        self.framePerfectButton.place(x=actionBarWidth, y=614, width=200, height=40)
        self.footerBar.place(x=video.WINDOW_WIDTH-482, y=614, width=video.WINDOW_WIDTH, height=40)


        # setup video
        self.video.openVideo(videoPaths[self.currentVideo-1])
        self.video.scheduleUpdates()

        # update text files
        self.tFileCount.config(text=f"{self.currentVideo} of {len(videoPaths)}")
        filename = videoPaths[self.currentVideo-1].split("/")[-1][:100]
        self.tFilename.config(text=filename)
        # replace file count to fit
        self.root.update()
        self.tFileCount.place(x=video.WINDOW_WIDTH-5-self.tFileCount.winfo_width(), y=2)
        # update times to default
        self.leftTime = 0
        self.rightTime = self.video.player.get_length()

    def updateOptions(self):
        """
            Updates the currently set options on the current video
        """
        for fcn in self.optionFunctions:
            fcn()


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
        if not self.footerBar.descBar.isBoxFocused:
            self.video.onKeyPress(event)

    def displayVideoControls(self):
        controls = {"Space": "Play/Pause", "\u2190": "Seek left", "\u2192": "Seek right", "\u2191": "Volume up", "\u2193": "Volume down", "F": "Fullscreen", "Esc": "Leave fullscreen", "Home": "Seek to start", "End": "Seek to last 20s", ",": "Rewind 1 frame", ".": "Seek 1 frame ahead", "M": "Toggle mute", "0-9": "Seek", "E/R": "Set trim position", "Ctrl+E/R": "Reset trim position", "Shift+E/R": "Shift current trim position"}
        maxLen = 20
        tab = '\t'
        messagebox.showinfo("Video Controls", "".join(f"{key:{6}}\t{tab if len(key) <= 8 else ''}{value}\n" for key, value in controls.items()))     

    def promptSkip(self):
        """
            Prompts the user to skip the current clip
        """
        result = messagebox.askokcancel("Skip", "Skip this clip?")
        if result == True:
            self.footerBar.nextButton.onClick(skipTrim=True, nextVideo=True, prevVideo=False)

    def promptSkipAll(self):
        """
            Prompts the user if they want to skip the rest of the clips and trim, also ignores current clip
        """  
        result = messagebox.askokcancel("Skip all", "Skip the rest of the videos and begin trimming?")
        if result == True:
            self.parent.setScene(Scene.SCENE_TRIM)

    def saveClip(self):
        """
            To be used to save the current clip without moving to the next video
        """
        self.footerBar.nextButton.onClick(skipTrim=False, nextVideo=False, prevVideo=False)
            

class FramePerfectButton(tk.Frame):
    """
        Toggleable button that specifies that the given clip should be frame perfect
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.isSet = tk.IntVar()

        self.button = tk.Checkbutton(self, text="Enable frame perfect trim (slow)", variable=self.isSet)
        self.button.pack()

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

        self.resetLeft.grid(column=0, row=0, pady=10)
        self.setLeft.grid(column=1, row=0)
        self.setRight.grid(column=2, row=0)
        self.resetRight.grid(column=3, row=0)

class NextButton(tk.Frame):
    def __init__(self, parent, clipScene: ClipScene, mainApp: MainApp):
        super().__init__(parent)
        self.parent = parent
        self.clipScene = clipScene
        self.mainApp = mainApp

        self.button = tk.Button(self, width=10, text="Next" if self.clipScene.currentVideo != self.clipScene.totalVideos else "Done", command=lambda: self.onClick(skipTrim=False, nextVideo=True, prevVideo=False), bg="#bbbbbb")
        self.button.config(state="disabled")
        self.button.pack()

    def onClick(self, skipTrim: bool, nextVideo: bool, prevVideo: bool):
        """
            skipTrim: Processes the click but ignores the current video for trimming
            nextVideo: Processes the click but does not move to the next video
        """

        # pause video
        if not self.parent.parent.video.actionBar.bPause.isPaused:
            self.parent.parent.video.actionBar.bPause.togglePause()

        # disable double press
        self.button.config(state="disabled")
        self.clipScene.footerBar.descBar.box.config(state="disabled")

        # sanitize input once more
        san_text = sanitize_filepath(self.clipScene.footerBar.descBar.boxContents.get())
        self.clipScene.footerBar.descBar.boxContents.set(san_text)


        # save picked times
        if not skipTrim:
            self.mainApp.trimData.append(dict([("description", self.clipScene.footerBar.descBar.boxContents.get()), ("startTime", self.clipScene.leftTime), ("endTime", self.clipScene.rightTime), ("fullVideoLength", self.clipScene.video.player.get_length()), ("isFramePerfect", self.clipScene.framePerfectButton.isSet.get() == 1), ("inputPath", self.mainApp.videoPaths[self.clipScene.currentVideo-1])]))

        if nextVideo or prevVideo:

            # update video
            self.clipScene.currentVideo += 1 if nextVideo else -1   # +1 if nextVideo / -1 if prevVideo

            # if prevVideo, remove previous clip as well
            if prevVideo:
                self.mainApp.trimData.pop()

            # update previous video button
            self.clipScene.controlMenu.entryconfigure("Previous video", state='normal' if self.clipScene.currentVideo > 1 else 'disabled')

            if self.clipScene.currentVideo > self.clipScene.totalVideos:  # done
                self.mainApp.setScene(Scene.SCENE_TRIM)
            else:

                # update text
                self.button.config(text="Next" if self.clipScene.currentVideo != self.clipScene.totalVideos else "Done")
                self.clipScene.tFileCount.config(text=f"{self.clipScene.currentVideo} of {self.clipScene.totalVideos}")
                filename = self.mainApp.videoPaths[self.clipScene.currentVideo-1].split("/")[-1][:100]
                self.clipScene.tFilename.config(text=filename)
                self.clipScene.footerBar.descBar.boxContents.set("")

                # reset frame perfect check
                self.clipScene.framePerfectButton.isSet.set(0)

                # replace file count to fit
                self.mainApp.root.update()
                self.clipScene.tFileCount.place(x=video.WINDOW_WIDTH-5-self.clipScene.tFileCount.winfo_width(), y=2)

                # update video
                self.clipScene.video.openVideo(self.mainApp.videoPaths[self.clipScene.currentVideo-1])

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
        maxLength = 100
        text = self.boxContents.get()
        if text == "":
            self.nextButton.button.config(state="disabled")
            self.parent.parent.controlMenu.entryconfigure("Save clip", state='disabled')
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
        self.parent.parent.controlMenu.entryconfigure("Save clip", state='normal' if len(san_text) > 0 and hasNonSpaceChar else "disabled")

    def ignore(self, event):
        """
            Used for ignoring keypresses
        """
        return "break"
        

class FooterBar(tk.Frame):
    def __init__(self, parent, clipScene: ClipScene, mainApp: MainApp):
        super().__init__(parent)
        self.parent = parent

        self.nextButton = NextButton(self, clipScene=clipScene, mainApp=mainApp)
        self.descBar = DescriptionBar(self, nextButton=self.nextButton)

        self.descBar.grid(column=0, row=0)
        self.nextButton.grid(column=1, row=0)

class TrimScene(tk.Frame):
    def __init__(self, parent, mainApp: MainApp):
        super().__init__(parent)
        self.parent = parent
        self.mainApp = mainApp
        self.parent.parent.geometry("400x260")
        self.root = parent.parent
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

        self.startButton = tk.Button(self.buttonFrame, command=self.startButtonOnClick, text="Start", width=9, height=1)
        self.startButton.grid(column=1, row=0)

        self.progressBar = ProgressBar(self)
        self.progressBar.pack(side="bottom", pady=0)

        # properties
        self.videoCount = 0
        self.a = False

    def skipButtonOnClick(self):
        self.skipButton.grid_forget()   # hide skip button

        # update progress bar
        self.videoCount += 1
        self.progressBar.bar["value"] = self.videoCount / len(self.mainApp.trimData) * 100
        self.progressBar.update()
        self.root.update_idletasks()

        # start next video
        self.startButtonOnClick()



    def startButtonOnClick(self):
        self.startButton.config(text="Start", state="disabled")
        self.skipButton.grid_forget()   # hide skip button

        # perform trim on all videos
        for trimData in self.mainApp.trimData[self.videoCount:]:
            inputPath = trimData["inputPath"]
            maxOrder = self.getFileOrder(self.mainApp.destFolder)
            outputPath = f"{self.mainApp.destFolder}/({maxOrder}) {trimData['description']}.mp4"
            startTime = trimData["startTime"] / 1000
            endTime = trimData["endTime"] / 1000
            isFramePerfect = trimData["isFramePerfect"]

            # update visual data
            stringWidth = font.Font().measure(trimData["description"])
            trimmedText = trimData["description"]
            trimWidth = 450
            while stringWidth > trimWidth:
                trimmedText = trimmedText[:-1]
                stringWidth = font.Font().measure(trimmedText)
            self.filename.config(text=f"Status: {trimmedText}{'...' if font.Font().measure(trimData['description']) > trimWidth else ''}")

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

        print(maxOrder+1)
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
    def __init__(self, parent):
        super().__init__(parent)

        # styling for the progress bar
        style = ttk.Style()
        style.theme_create("style", parent="default", settings={
            "TProgressbar": {
                "configure": {
                    "background": "lime",
                    "troughcolor": "grey",
                    "borderwidth": 1,
                    "thickness": 2
                }
            }
        })
        style.theme_use("style")

        self.bar = ttk.Progressbar(self, mode="determinate", maximum=100, length=400)
        self.bar.pack()

        




#
# Main
#
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Bulk Video Trimmer")
    root.geometry("400x100")
    root.resizable(width=False, height=False)
    root.iconbitmap(getResourcePath("images/logo.ico"))

    app = MainApp(root)
    app.pack(fill="both", expand=True)
    app.setScene(Scene.SCENE_CLIPS)

    root.mainloop()