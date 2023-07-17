#
# video.py
#
# Contains a VideoPlayer class to encapsulate everything needed to create a video player
#

# add vlc libs to path
import os
os.add_dll_directory(os.getcwd())
import sys
try:
    os.add_dll_directory(sys._MEIPASS)  # try using temp folder for pyinstaller
except:pass

import tkinter as tk
import vlc
import threading
import time
from PIL import Image, ImageTk
import gui

WINDOW_HEIGHT = 649
WINDOW_WIDTH = 1024




class VideoPlayer(tk.Frame):
    def __init__(self, parent, root, playOnOpen: bool, restrictLeftButton = None, restrictRightButton = None, unrestrictLeftButton = None, unrestrictRightButton = None, clipScene = None, menuBar = None, discordPresence = None, mainApp = None):
        """
            Params:
            playOnOpen: autoplay automatically upon opening a video using openVideo()
        """
        super().__init__(parent, bg="#000000")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.root = root
        self.parent = parent
        self.lastVolumeChange = 0  
        self.isVolumeBarVisible = False
        self.lastEndStateTime = 0
        self.timeToUpdateEndState = 1
        self.duration = 0
        self.isVideoOpened = False
        self.enableRestrictedPlayback = False
        self.restrictLeft = None
        self.restrictRight = None
        self.restrictLeftButton = restrictLeftButton
        self.restrictRightButton = restrictRightButton
        self.unrestrictLeftButton = unrestrictLeftButton
        self.unrestrictRightButton = unrestrictRightButton
        self.clipScene = clipScene
        self.menuBar = menuBar
        self.isWindowFocused = True
        self.discordPresence = discordPresence
        self.mainApp = mainApp

        # properties
        self.playOnOpen = playOnOpen
        self.volume = 50

        # init vlc instance
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.player.video_set_mouse_input(False)
        self.player.video_set_key_input(False)
        
        # init properties
        self.player.audio_set_volume(self.volume)
        
        # video interaction (clicks)
        self.lastVideoClick = 0
        self.videoDoubleClickDetected = False

        # init canvas
        self.canvas = tk.Canvas(self, bg='black', borderwidth=0, highlightthickness=0)

        # display elements
        self.canvas.grid(column=0, row=0, sticky='nswe', columnspan=2)  

        # progress bar
        self.progressBarHeight = 5
        root.update()
        self.progressBar = ProgressBar(self, self.player, width=self.canvas.winfo_width(), height=self.progressBarHeight, bg='#383838', fg='#4287f5')

        # progress bar spacer (since place is used for progress bar)
        self.progressBarSpacer = tk.Frame(self, height=self.progressBarHeight, bg="#000000")
        self.progressBarSpacer.grid(column=0, row=1, sticky='nswe', columnspan=2)   

        self.progressBar.place(x=0, y=self.canvas.winfo_height())      

        # buttons
        padX = 5
        self.volumeBar = VolumeBar(self, player=self.player, defaultVolume=50, width=19, height=50)
        self.buttonSize = 25
        self.actionBar = ActionBar(self, self.player, buttonSize=self.buttonSize, progressBar=self.progressBar, volumeBar=self.volumeBar, progressBarHeight=self.progressBarHeight, padX=padX)
        self.bPause = self.actionBar.bPause
        
        
        # fullscreen button, initialized with a list of all widgets to be resized
        self.bFullscreen = FullscreenButton(self, root=root, size=self.buttonSize)

        self.actionBar.grid(column=0, row=2, sticky="nesw")

        root.update()  # update to get positions of button widgets 
        self.volumeBar.place(x=self.actionBar.bVolume.winfo_x() + (self.actionBar.bVolume.winfo_width()/2) - (self.volumeBar.width/2), y=self.canvas.winfo_height() - self.volumeBar.height - 5, width=self.volumeBar.width, height=self.volumeBar.height)
        self.bFullscreen.grid(column=1, row=2, sticky="nesw")
        self.progressBar.lift()
        self.volumeBar.lift()
        

        # add listener for events
        root.bind("<KeyPress>", self.onKeyPress)
        self.progressBar.bind("<Enter>", self.onHover_ProgressBar)
        self.progressBar.bind("<Leave>", self.onLeave_ProgressBar)
        root.bind("<FocusIn>", self.onWindowFocus)
        root.bind("<Button-1>", self.onClick)
        root.bind("<FocusOut>", self.onWindowUnfocus)
        self.bind("<Configure>", self.onResize)

    def onResize(self, event):
        """
            Called whenever the window is resized/configured
        """
        self.root.update()

        # progress bar
        self.progressBar.width = self.canvas.winfo_width()
        self.progressBar.canvas.config(width=self.progressBar.width)
        self.progressBar.place(x=0, y=self.canvas.winfo_height() - (self.progressBarHeight if self.bFullscreen.isFullscreen else 0))      

    def onClick(self, event):
        """
            On click anywhere in the window
        """
        if event.widget != self.canvas: return
        self.parent.update_idletasks()  # update focus
        def _afterFocus():
            if not self.isWindowFocused: return       # only check when the window is focused
            
            # check for left click on canvas
            videoX1, videoY1 = self.canvas.winfo_rootx(), self.canvas.winfo_rooty()
            videoX2, videoY2 = videoX1 + self.canvas.winfo_width(), videoY1 + self.canvas.winfo_height() - (self.progressBarHeight * 2 if self.progressBar.isHovering else 1)
            
            # reset focus
            if self.clipScene != None:
                self.clipScene.footerBar.descBar.isBoxFocused = False
                self.parent.focus()

            
            def checkForDoubleClick():
                timeSinceLastClick = time.time() - self.lastVideoClick
                if timeSinceLastClick >= .24 and not self.videoDoubleClickDetected:
                    self.bPause.onClick()
                self.videoDoubleClickDetected = False

            timeSinceLastClick = time.time() - self.lastVideoClick
            if timeSinceLastClick >= .24: 
                self.after(250, checkForDoubleClick)

            if timeSinceLastClick < .24:
                self.videoDoubleClickDetected = True      # if this is set to true, then don't allow pause to toggle
                self.bFullscreen.toggleFullscreen()                             
            
            self.lastVideoClick = time.time()

        # exec after focus catches up
        self.after(100, _afterFocus)
            


    def onWindowFocus(self, event):
        """
            Used to avoid 0 size window on Win+D keypress
        """
        if self.parent.focus_displayof() != None:
            self.isWindowFocused = True

    def onWindowUnfocus(self, event):
        if self.parent.focus_displayof() == None:
            self.isWindowFocused = False

    def onHover_ProgressBar(self, event):
        self.progressBar.place(x=0, y=(self.canvas.winfo_height() if not self.bFullscreen.isFullscreen else self.canvas.winfo_height()-self.progressBarHeight) - self.progressBar.height)
        
    
    def onLeave_ProgressBar(self, event):
        self.root.update()
        if not self.progressBar.isClicking and not self.progressBar.isHovering:
            self.progressBar.place(x=0, y=self.canvas.winfo_height() if not self.bFullscreen.isFullscreen else self.canvas.winfo_height()-self.progressBarHeight)
            
    def _setPlayerPosition(self, percent):
        """
            Provided a percentage of 0-1, mimics player.set_position
            Uses restricted playback to lock the position to its bounds
        """
        if self.enableRestrictedPlayback and self.player.get_state() not in [vlc.State.Ended, vlc.State.Opening]:
            if self.player.get_length() == 0: return
            leftPercent = self.restrictLeft / self.player.get_length()
            rightPercent = self.restrictRight / self.player.get_length()
            self.player.set_position(leftPercent if percent < leftPercent else (rightPercent if percent > rightPercent else percent))
        else:
            self.player.set_position(percent)

    def onKeyPress(self, event):
        key = event.keysym
        if key == "space":
            self.bPause.onClick()
        elif key == "Left":
            seekTime = 10000
            if self.clipScene != None: seekTime = self.clipScene.options["SeekTime"].get()
            self.seek(-seekTime)
        elif key == "Right":
            seekTime = 10000
            if self.clipScene != None: seekTime = self.clipScene.options["SeekTime"].get()
            self.seek(seekTime)
        elif key == "Up":
            self.volume = min(100, self.volume + 5)
            self.player.audio_set_volume(self.volume)
            self.actionBar.bVolume.setVolume(self.volume)
            self.actionBar.bVolume.unmute()
            self.volumeBar.setValue(self.volume)
            self.lastVolumeChange = time.time()
        elif key == "Down":
            self.volume = max(0, self.volume - 5)
            self.player.audio_set_volume(self.volume)
            self.actionBar.bVolume.setVolume(self.volume)
            self.actionBar.bVolume.unmute()
            self.volumeBar.setValue(self.volume)
            self.lastVolumeChange = time.time()
        elif key == "period":
            if self.bPause.isPaused and self.player.get_state() != vlc.State.Ended:
                fps = self.player.get_fps()
                duration = int(1000 / fps)       # number of ms per frame
                self.seek(duration)
        elif key == "comma":
            if self.bPause.isPaused and self.player.get_state() != vlc.State.Ended:
                fps = self.player.get_fps()
                duration = int(1000 / fps)       # number of ms per frame
                self.seek(-duration)
        elif key in ["m","M"]:
            self.actionBar.bVolume.toggleMute()
        elif key in ["f","F"]:
            self.bFullscreen.toggleFullscreen()
        elif key == "Escape":
            if self.bFullscreen.isFullscreen: 
                self.bFullscreen.toggleFullscreen()
        elif key == "Home":
            if self.player.get_state() == vlc.State.Ended:
                self.player.stop()
                self.player.play()
                self.bPause.setUnpaused()   
                self.progressBar.setValue(0) # update bar

                while self.player.get_state() == vlc.State.Opening: pass
                self.player.pause()
                self.bPause.setPaused()

            self._setPlayerPosition(0)
        elif key == "End":
            if self.player.get_length() - 20000 < 0: return

            if self.player.get_state() == vlc.State.Ended:
                self.player.stop()
                self.player.play()
                self.bPause.setUnpaused()   

                while self.player.get_state() == vlc.State.Opening: pass
                self.player.pause()
                self.bPause.setPaused()

            if self.enableRestrictedPlayback:
                new_time = self.restrictRight - 20000
                if new_time < self.restrictLeft: return
                self._setPlayerPosition(max(0, new_time/self.duration))
            else:
                self._setPlayerPosition(max(0, (self.duration - 20000) / self.duration))        
        elif key in [str(val) for val in range(0,10)]:
            # reset player if video is completed
            percent = int(key) / 10

            if self.player.get_state() == vlc.State.Ended:
                self.player.stop()
                self.player.play()
                self.bPause.setUnpaused()   
                self.progressBar.setValue(int(self.duration * percent)) # update bar

                while self.player.get_state() == vlc.State.Opening: pass
                self.player.pause()
                self.bPause.setPaused()

            if self.enableRestrictedPlayback:
                if self.player.get_length() == 0: return
                leftPercent = self.restrictLeft / self.player.get_length()
                rightPercent = self.restrictRight / self.player.get_length()
                diff = rightPercent - leftPercent
                percent = (percent * diff) + leftPercent

                self._setPlayerPosition(percent)
            else:
                self.player.set_time(int(self.duration * percent))
        elif key in ["e","E"] and event.state == 8:
            self.restrictLeftButton.onClick()
        elif key in ["r","R"] and event.state == 8:
            self.restrictRightButton.onClick()
        elif key in ["e","E"] and event.state in [12,14]:   # Ctrl-e
            self.unrestrictLeftButton.onClick()
        elif key in ["r","R"] and event.state in [12,14]:   # Ctrl-r
            self.unrestrictRightButton.onClick()   
        elif key in ["e","E"] and event.state == 9:         # Shift-e
            self.restrictLeftButton.shiftLock(-5000)
        elif key in ["r","R"] and event.state == 9:         # Shift-r
            self.restrictRightButton.shiftLock(5000)
        elif key == "Return":
            if self.clipScene == None: return
            if event.widget != self.clipScene.footerBar.descBar.box:        # already handled by gui
                self.clipScene.footerBar.descBar.onReturnKey(event=None)
        elif key == "grave":
            if self.clipScene == None: return
            if self.clipScene.footerBar.descBar.isBoxFocused:
                self.clipScene.footerBar.descBar.isBoxFocused = False
                self.root.focus()       # unfocus description box
            else:
                self.clipScene.footerBar.descBar.isBoxFocused = True
                self.clipScene.footerBar.descBar.box.focus()       # focus on description box
        

    def seek(self, time):
        """
            Seeks the video forward by the given time in milliseconds. 
            Specify a negative value for reverse seek
        """
        if time == 0: return
        newTime = self.player.get_time() + time
        duration = self.player.get_length()

        # do nothing if skipping on bounds
        boundary = duration/1000
        if time < 0 and self.player.get_position() == 0: return
        if time > 0 and self.player.get_position() >= duration-boundary/duration: return
        
        # reset player if video is completed
        if self.player.get_state() == vlc.State.Ended:
            if time > 0: return
            else:
                self.player.stop()
                self.player.play()
                self.bPause.setUnpaused()  
                self._setPlayerPosition(max(0, duration-time))
                self.progressBar.setValue(max(0, duration-time)) # update bar

            while self.player.get_state() == vlc.State.Opening: pass
            self.player.pause()
            self.bPause.setPaused()

        if newTime < 0: 
            self._setPlayerPosition(0)
        elif newTime > duration-250: 
            self._setPlayerPosition(max(0, (duration-boundary) / duration)) # skip to right before end of stream
        else:
            self._setPlayerPosition(newTime/duration)

    def openVideo(self, filepath: str):
        # stop video
        self.player.stop()
        self.isVideoOpened = False

        # check if video exists
        if not os.path.exists(filepath):
            print(f"Could not open video [{filepath}]")
            return

        # reset values
        self.lastEndStateTime = 0
        self.duration = 0

        media = self.instance.media_new(filepath)
        self.player.set_media(media)
        self.player.set_hwnd(self.canvas.winfo_id())
        
        # Load thumbnail
        self.play()
        while not self.player.is_playing(): pass
        self.pause() 
        
        # update position and duration
        self.player.set_position(0)
        self.actionBar.playbackTimer.setDuration(self.player.get_length() / 1000)
        self.duration = self.player.get_length()
        
        # play if set to autoplay on open
        if self.playOnOpen: self.play()

        self.isVideoOpened = True
        self.unrestrictPlayback()

        # update options
        if self.clipScene != None:
            self.clipScene.updateOptions()


    def play(self):
        self.bPause.setUnpaused()
    
    def pause(self):
        self.bPause.setPaused()

    def scheduleUpdates(self):
        updater = threading.Thread(target=self._update, daemon=True)
        updater.start()

    def _update(self):
        """
            Initializes constant updates to elements over an interval
        """
        # Get the VLC player position and duration
        position = self.player.get_position()
        duration = self.player.get_length()

        # update last ended video time
        if self.player.get_state() == vlc.State.Ended:
            self.lastEndStateTime = time.time()
        timeSinceLastEndState = time.time() - self.lastEndStateTime

        # pause/loop if at end of video
        framesToEnd = duration - self.player.get_time()
        if self.player.get_state() == vlc.State.Playing and framesToEnd < 250:
            if self.clipScene != None:
                if self.clipScene.options["LoopPlayback"].get():
                    self._setPlayerPosition(0)
                else:
                    self.player.pause()
            else:
                self.player.pause()

        # update pause button
        playState = self.player.get_state()
        if playState == vlc.State.Ended:
            self.bPause.setPaused()
        elif playState == vlc.State.Playing:
            self.bPause.bPause.config(image=self.bPause.pauseImage)
        elif playState == vlc.State.Paused:
            self.bPause.bPause.config(image=self.bPause.playImage)

        # update progress bar
        if timeSinceLastEndState > self.timeToUpdateEndState or position != 0:       # do not update on restart video
            self.progressBar.setValue(1 if playState == vlc.State.Ended else position)

        # update last hover time if currently hovering
        if self.volumeBar.isHovering:
            self.volumeBar.lastVolumeHover = time.time()
        if self.actionBar.bVolume.isHovering:
            self.actionBar.bVolume.lastVolumeHover = time.time()

        # update volume bar visibility
        isHovering = self.volumeBar.isHovering or self.actionBar.bVolume.isHovering
        timeSinceLastVolChange = time.time() - self.lastVolumeChange
        timeSinceLastVolHover = time.time() - max(self.volumeBar.lastVolumeHover, self.actionBar.bVolume.lastVolumeHover)

        if (timeSinceLastVolHover < 1 or timeSinceLastVolChange < 1) and not self.bFullscreen.isFullscreen:
            self.isVolumeBarVisible = True
            self.volumeBar.place(x=self.actionBar.bVolume.winfo_x() + (self.actionBar.bVolume.winfo_width()/2) - (self.volumeBar.width/2), y=self.canvas.winfo_height() - self.volumeBar.height - 5, width=self.volumeBar.width, height=self.volumeBar.height)
        else:   # hide
            self.isVolumeBarVisible = False
            self.volumeBar.place(x=self.actionBar.bVolume.winfo_x() + (self.actionBar.bVolume.winfo_width()/2) - (self.volumeBar.width/2), y=self.canvas.winfo_height() - self.volumeBar.height - 5, width=0, height=0)
        

        # update playback timer
        if self.isVideoOpened and self.player.get_state() != vlc.State.Stopped:
            if self.player.get_state() == vlc.State.Ended:
                self.actionBar.playbackTimer.setTime(self.player.get_length() / 1000)
            elif timeSinceLastEndState > self.timeToUpdateEndState or self.player.get_time() != 0:
                self.actionBar.playbackTimer.setTime(self.player.get_time() / 1000)
        else:
            self.actionBar.playbackTimer.setTime(0)
            self.actionBar.playbackTimer.setDuration(0)

        # pause if in restricted mode and past boundary
        # or replay in autoplay mode
        if duration != 0:
            if self.enableRestrictedPlayback and round(self.player.get_time(), 6) > round(self.restrictRight, 6): 
                if self.clipScene.options["LoopPlayback"].get():
                    if not self.progressBar.isClicking and not self.bPause.isPaused:
                        self._setPlayerPosition(0)
                else:
                    if not self.bPause.isPaused: 
                        self.bPause.togglePause() 
                    
                    
                    if self.clipScene.framePerfectButton.isSet.get() == 1:
                        # delay needed to process recent pause
                        self.parent.after(50, lambda: self._setPlayerPosition(self.restrictRight / duration))    
                    else:
                        self._setPlayerPosition(self.restrictRight / duration)     

        # update discord presence
        if self.discordPresence is not None:
            try:
                self.discordPresence.updateStatus(details="Clipping videos", state=f"{min(self.clipScene.currentVideo, self.clipScene.totalVideos)} of {self.clipScene.totalVideos}") 
            except:
                self.discordPresence = None     # discord was likely closed

        # update options
        if self.clipScene != None:
            self.clipScene.updateOptions()
                   
        # Schedule the next update
        if self.mainApp == None: 
            self.after(10, self._update)
        elif str(self.mainApp.getSceneType()) == str(gui.Scene.SCENE_CLIPS):
            self.after(10, self._update)

    def restrictPlayback(self, time1: int, time2: int):
        """
            Restricts playback to fall between the two time values
        """
        if time1 < 0 or time2 < 0 or time1 > self.player.get_length() or time2 > self.player.get_length() or time1 > time2: return
        if self.clipScene is not None:
            self.clipScene.leftTime = time1
            self.clipScene.rightTime = time2
        self.restrictLeft = time1
        self.restrictRight = time2
        self.enableRestrictedPlayback = True

        # update restriction bar visibility
        leftPercent = time1 / self.player.get_length()
        rightPercent = time2 / self.player.get_length()
        self.progressBar.canvas.coords(self.progressBar.restrictBar, int(leftPercent * self.progressBar.width), 0, int(rightPercent * self.progressBar.width), self.progressBar.height * (2 if self.progressBar.isHovering or self.progressBar.isClicking else 1))
        self.progressBar.canvas.itemconfig(self.progressBar.restrictBar, state="normal")

    def unrestrictPlayback(self):
        """
            Disables playback restriction
        """
        self.enableRestrictedPlayback = False
        self.restrictLeft = 0
        self.restrictRight = self.player.get_length()
        if self.clipScene != None:
            self.clipScene.leftTime = self.restrictLeft
            self.clipScene.rightTime = self.restrictRight
        self.progressBar.canvas.itemconfig(self.progressBar.restrictBar, state="hidden")
        


class ActionBar(tk.Frame):
    """
        A frame of buttons used to control the video player
    """
    def __init__(self, parent, player, buttonSize: int, progressBar, volumeBar, progressBarHeight: int, padX: int):
        super().__init__(parent, bg="black")
        self.parent = parent
        self.player = player
        self.buttonSize = buttonSize
        self.progressBar = progressBar
        self.volumeBar = volumeBar

        # init elements
        self.bPause = PauseButton(self, self.player, progressBar=self.progressBar, size=buttonSize)
        self.bSkipBackward = SkipButton(self, self.player, self.progressBar, pauseButton=self.bPause, isForwardSkip=False, size=buttonSize)
        self.bSkipForward = SkipButton(self, self.player, self.progressBar, pauseButton=self.bPause, isForwardSkip=True, size=buttonSize)
        self.bVolume = VolumeButton(self, player=self.player, volumeBar=self.volumeBar, defaultVolume=50, size=buttonSize)
        self.playbackTimer = PlaybackTimer(self, player=self.player)

        # display
        self.bPause.grid(column=0, row=0, padx=padX, pady=5)
        self.bSkipBackward.grid(column=1, row=0, padx=padX)
        self.bSkipForward.grid(column=2, row=0, padx=padX)
        self.bVolume.grid(column=3, row=0, padx=padX)
        self.playbackTimer.grid(column=4, row=0, padx=padX)


class PlaybackTimer(tk.Frame):
    """
        A test display of the current time
    """
    def __init__(self, parent, player):
        super().__init__(parent)
        self.player = player
        self.time = 0,0,0
        self.duration = 0,0,0

        self.text = tk.Label(self, text="0:00 / 0:00", fg="white", bg="black", font=("Roboto", 9))
        self.text.pack()
        

    def setTime(self, seconds: int):
        self.time = self._convertTime(seconds)
        self.text.config(text=self._getTimeText())

    def setDuration(self, seconds: int):
        self.duration = self._convertTime(seconds)
        self.text.config(text=self._getTimeText())

    def _convertTime(self, seconds: int):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return h,m,s
    
    def _getTimeText(self):
        """
            Returns the text that represents the playback time based on current values
        """
        # time
        hTime = f"{self.time[0]}:" if self.time[0] != 0 else ""
        mTime = f"{self.time[1]}:" if len(str(self.time[1])) == 2 or (len(str(self.time[1])) == 1 and self.time[0] == 0) else f"0{self.time[1]}:"
        sTime = f"{self.time[2]}" if len(str(self.time[2])) == 2 else f"0{self.time[2]}"
        time = f"{hTime}{mTime}{sTime}"

        # duration
        hDuration = f"{self.duration[0]}:" if self.duration[0] != 0 else ""
        mDuration = f"{self.duration[1]}:" if len(str(self.duration[1])) == 2 or (len(str(self.duration[1])) == 1 and self.duration[0] == 0) else f"0{self.duration[1]}:"
        sDuration = f"{self.duration[2]}" if len(str(self.duration[2])) == 2 else f"0{self.duration[2]}"
        duration = f"{hDuration}{mDuration}{sDuration}"

        return f"{time} / {duration}"


class FullscreenButton(tk.Frame):
    """
        A button for setting and exiting window fullscreen
    """
    def __init__(self, parent, root, size: int):
        super().__init__(parent, background="#000000")
        self.root = root
        self.parent = parent
        self.isFullscreen = False
        self.lastFullscreenToggle = 0
        self.timeBetweenToggles = .2
        self.widgetData = {}

        image = Image.open(gui.getResourcePath("images/fullscreen.png"))
        image.thumbnail((size, size))
        self.image = ImageTk.PhotoImage(image)
        self.button = tk.Button(self, width=size, command=self.toggleFullscreen, image=self.image, borderwidth=0, highlightthickness=0, bg="black", activebackground="black")

        self.button.pack(padx=5, pady=5)

    def toggleFullscreen(self, forceToggle: bool = False):
        if not self.parent.isVideoOpened: return
        if time.time() - self.lastFullscreenToggle < self.timeBetweenToggles: return
        self.lastFullscreenToggle = time.time()
        self.isFullscreen = not self.isFullscreen

        winX, winY = self.root.winfo_width(), self.root.winfo_height()
        video = self.parent
        video.canvas.grid_forget()
        self.root.attributes("-fullscreen", self.isFullscreen)

        if self.isFullscreen:
            # save widget data
            self.widgetData["WindowSize"] = winX, winY

            video.actionBar.grid_forget()
            video.bFullscreen.grid_forget()
            video.progressBarSpacer.grid_forget()
            video.volumeBar.place_forget()

            # make canvas visible again (avoids tearing)
            video.canvas.grid(column=0, row=0, sticky='nswe', columnspan=2)
            self.root.update()
            video.progressBar.place(x=0, y=video.canvas.winfo_height() - video.progressBarHeight)    
            video.progressBar.lift()  

            # menubar
            self.root.config(menu=tk.Menu(self.root)) # remove menu

            # clipscene widgets
            clipScene = video.clipScene
            clipScene.topBar.grid_forget()
            clipScene.actionBar.grid_forget()
            clipScene.framePerfectButton.grid_forget()
            clipScene.footerBar.grid_forget()
            clipScene.tFilename.place_forget()
            clipScene.tFileCount.place_forget()


        else:
            video.actionBar.grid(column=0, row=2, sticky="nesw")
            video.bFullscreen.grid(column=1, row=2, sticky="nesw")
            video.progressBarSpacer.grid(column=0, row=1, sticky='nswe', columnspan=2)   

            # menubar
            self.root.config(menu=video.menuBar)
            self.root.update()

            # update widget data
            winX, winY = self.widgetData["WindowSize"]

            # make canvas visible again (avoids tearing)
            video.canvas.grid(column=0, row=0, sticky='nswe', columnspan=2)

            # clipscene widgets
            clipScene = video.clipScene
            clipScene.topBar.grid(column=0, row=0, sticky='nesw')
            clipScene.actionBar.grid(column=0, row=2, sticky='nesw')
            clipScene.framePerfectButton.grid(column=1, row=2, sticky='nesw')
            clipScene.footerBar.grid(column=2, row=2, sticky="nesw")
            clipScene.tFilename.place(x=4, y=2)
            clipScene.tFileCount.place(x=video.winfo_width()-5-clipScene.tFileCount.winfo_width(), y=2)
            clipScene.onResize(event=None)



        

            

            
            
        
        

class VolumeBar(tk.Frame):
    """
        A volume button for muting and changing output volume
    """
    def __init__(self, parent, player, defaultVolume: int, width: int, height: int):
        super().__init__(parent)
        self.parent = parent
        self.player = player
        self.width = width
        self.height = height
        self.volume = defaultVolume
        self.isHovering = False
        self.lastVolumeHover = 0

        self.canvas = tk.Canvas(self, width=width, height=height, borderwidth=0, highlightthickness=0, bg='#0F0F0F')

        center = int(self.width / 2)
        radius = 2.5
        self.verticalSpacing = 5
        self.backBar = self.canvas.create_rectangle(center-radius, self.verticalSpacing, center+radius, self.height-self.verticalSpacing, fill="#383838", outline='')

        # volume bar
        percent = defaultVolume / 100
        vPos = (1-percent) * (self.height - (2*self.verticalSpacing)) + self.verticalSpacing
        self.volumeBar = self.canvas.create_rectangle(center-radius, vPos, center+radius, self.height-self.verticalSpacing, fill="#4287f5", outline='')

        self.canvas.pack()

        # listeners
        self.bind("<Enter>", self.onHover)
        self.bind("<Leave>", self.onLeave)
        self.canvas.bind("<B1-Motion>", self.onDrag)
        self.canvas.bind("<Button-1>", self.onClick)

    def onDrag(self, event):
        y = event.y - self.canvas.canvasy(0) - self.verticalSpacing
        percent = 1 - (y / (self.height - (2*self.verticalSpacing)))
        percent = max(0, percent)
        percent = min(1, percent)

        volume = percent * 100
        self.setValue(volume)
        self.volume = int(volume)
        self.parent.volume = self.volume
        self.player.audio_set_volume(self.volume)
        self.parent.actionBar.bVolume.setVolume(self.volume)
        self.parent.actionBar.bVolume.unmute()
        self.parent.lastVolumeChange = time.time()

    def onClick(self, event):
        self.onDrag(event)

    def setValue(self, volume: float):
        if volume > 100 or volume < 0: return
        self.volume = volume

        # if 0, just hide the rectangle
        self.canvas.itemconfigure(self.volumeBar, state="hidden" if self.volume == 0 else "normal")

        x1, y1, x2, y2 = self.canvas.coords(self.volumeBar)
        percent = self.volume / 100
        vPos = (1-percent) * (self.height - (2*self.verticalSpacing)) + self.verticalSpacing
        self.canvas.coords(self.volumeBar, x1, vPos, x2, y2)

    def onHover(self, event):
        self.isHovering = True
        self.lastVolumeHover = time.time()

    def onLeave(self, event):
        self.isHovering = False


    

class VolumeButton(tk.Frame):
    """
        A volume button for muting and changing output volume
    """
    def __init__(self, parent, player, volumeBar: VolumeBar, defaultVolume: int, size: int):
        super().__init__(parent)
        self.player = player
        self.volume = defaultVolume
        self.isHovering = False
        self.timeToShowSlider = 300
        self.volumeBar = volumeBar
        self.lastVolumeHover = 0
        self.isMuted = False
        
        #images
        images = [Image.open(gui.getResourcePath("images/volume-mute.png")), Image.open(gui.getResourcePath("images/volume-min.png")), Image.open(gui.getResourcePath("images/volume-mid.png")), Image.open(gui.getResourcePath("images/volume-max.png"))]
        for image in images: image.thumbnail((size, size))
        self.images = [ImageTk.PhotoImage(image) for image in images]
        self.bVolume = tk.Button(self, width=size, command=self.toggleMute, borderwidth=0, highlightthickness=0, bg="black", activebackground="black")
        self.updateImage()

        self.bVolume.pack()

        # listeners
        self.bind("<Enter>", self.onHover)
        self.bind("<Leave>", self.onLeave)

    def toggleMute(self):
        self.isMuted = not self.isMuted
        self.mute() if self.isMuted else self.unmute()

    def setVolume(self, value):
        """
            Used for setting the volume bar for after unmuting
        """
        if value < 0 or value > 100: return
        self.volume = value
        self.updateImage()


    def updateImage(self):
        if self.isMuted:
            self.bVolume.config(image=self.images[0])
        elif self.volume == 0:
            self.bVolume.config(image=self.images[1])
        elif self.volume < 50:
            self.bVolume.config(image=self.images[2])
        else:
            self.bVolume.config(image=self.images[3])


    def mute(self):
        self.isMuted = True
        self.player.audio_set_volume(0)
        self.volumeBar.setValue(0)
        self.lastVolumeChange = time.time()
        self.updateImage()
        

    def unmute(self):
        self.isMuted = False
        self.player.audio_set_volume(self.volume)
        self.volumeBar.setValue(self.volume)
        self.lastVolumeChange = time.time()
        self.updateImage()

    def onHover(self, event):
        self.isHovering = True
        self.lastVolumeHover = time.time()

    def onLeave(self, event):
        self.isHovering = False

        


class PauseButton(tk.Frame):
    """
        A visual pause button for the video player
    """
    def __init__(self, parent, player, progressBar, startPaused: bool = True, size: int = 50):
        super().__init__(parent)
        self.player = player
        self.parent = parent
        self.isPaused = startPaused
        self.progressBar = progressBar

        self.imPlay = Image.open(gui.getResourcePath("images/play.png"))
        self.imPause = Image.open(gui.getResourcePath("images/pause.png"))
        self.imPlay.thumbnail((size, size))
        self.imPause.thumbnail((size, size))
        self.playImage = ImageTk.PhotoImage(self.imPlay)
        self.pauseImage = ImageTk.PhotoImage(self.imPause)

        self.bPause = tk.Button(self, width=size, command=self.onClick, image=self.playImage if startPaused else self.pauseImage, borderwidth=0, highlightthickness=0, bg="black", activebackground="black")
        self.bPause.image = self.playImage if startPaused else self.pauseImage

        self.bPause.pack()

    def onClick(self):
        self.togglePause()       
        
        # reset on past boundary
        while self.player.get_state() == vlc.State.Opening: pass
        if self.parent.parent.enableRestrictedPlayback and (round(self.player.get_position(), 6) >= round(self.parent.parent.restrictRight / self.player.get_length(), 6) or round(self.player.get_position(), 6) < round(self.parent.parent.restrictLeft / self.player.get_length(), 6)):  
            self.parent.parent._setPlayerPosition(0)   # set back to start  

    def togglePause(self):
        if not self.parent.parent.isVideoOpened: return
        while self.player.get_state() == vlc.State.Opening: pass


        # if past edge of video (250) and attempting to play, reset
        if self.player.get_length() - self.player.get_time() < 250:
            self.parent.parent._setPlayerPosition(0)
            self.setUnpaused()
            return

        # special case: reset from beginning if in end state
        if self.player.get_state() == vlc.State.Ended:
            self.player.stop()
            self.player.play()          
            self.setUnpaused()   
            self.progressBar.setValue(0) # update bar
            self.parent.parent.clipScene.updateOptions()

        if not self.isPaused:
            self.player.pause()
            self.bPause.config(image=self.playImage)
            self.isPaused = True
        else:
            self.player.play()
            self.bPause.config(image=self.pauseImage)
            self.isPaused = False

    def setPaused(self):
        self.player.pause()
        self.bPause.config(image=self.playImage)
        self.isPaused = True

    def setUnpaused(self):
        self.player.play()
        self.bPause.config(image=self.pauseImage)
        self.isPaused = False

class SkipButton(tk.Frame):
    def __init__(self, parent, player, progressBar, pauseButton: PauseButton, isForwardSkip: bool = True, size: int = 50):
        super().__init__(parent)
        self.parent = parent
        self.player = player
        self.pauseButton = pauseButton
        self.isForwardSkip = isForwardSkip
        self.progressBar = progressBar

        image = Image.open(gui.getResourcePath("images/skip-15.png")  if isForwardSkip else gui.getResourcePath("images/back-15.png"))
        image.thumbnail((size, size))
        self.image = ImageTk.PhotoImage(image)

        self.button = tk.Button(self, width=size, command=self.skip, image=self.image, borderwidth=0, highlightthickness=0, bg="black", activebackground="black")
        self.button.image = self.image

        self.button.pack()

    def skip(self):
        newTime = self.player.get_time() + (15000 if self.isForwardSkip else -15000)
        duration = self.player.get_length()
        # do nothing if skipping on bounds
        boundary = duration / 1000
        if self.isForwardSkip == False and self.player.get_position() == 0: return
        if self.isForwardSkip and self.player.get_position() >= duration-boundary/duration: return
        
        # reset player if video is completed
        if self.player.get_state() == vlc.State.Ended:
            if self.isForwardSkip: return
            else:
                self.player.stop()
                self.player.play()
                self.pauseButton.setUnpaused()
                self.parent.parent._setPlayerPosition(max(0, duration-15000))
                self.parent.parent.clipScene.updateOptions()
            
            while self.player.get_state() == vlc.State.Opening: pass
            self.player.pause()
            self.parent.bPause.setPaused()
                
        
        if newTime < 0: 
            self.parent.parent._setPlayerPosition(0)
        elif newTime > duration-250:    
            self.parent.parent._setPlayerPosition(max(0, (duration-boundary) / duration)) # skip to right before end of stream
            self.progressBar.setValue(max(0, (duration-boundary) / duration)) # update bar
        else:
            self.parent.parent._setPlayerPosition(newTime/duration)
        
        
        

class ProgressBar(tk.Frame):
    def __init__(self, parent, player, width: int, height: int, bg: str, fg: str):
        super().__init__(parent, bg="#000000")  
        self.parent = parent
        self.width = width
        self.height = height
        self.player = player
        self.isHovering = False
        self.isClicking = False
        self.lastClick_PauseState = None

        # instances
        self.canvas = tk.Canvas(self, width=width, height=height, borderwidth=0, highlightthickness=0, bg=bg)
        self.backBar = self.canvas.create_rectangle(0, 0, self.width, self.height, fill=bg, width=0)
        self.restrictBar = self.canvas.create_rectangle(0, 0, self.width, self.height, outline='', fill="#3b5071", state="hidden")
        self.progressBar = self.canvas.create_rectangle(0, 0, 0, self.height, fill=fg, outline='')
        

        # build
        self.canvas.pack()

        # add listener for events
        self.canvas.bind("<Enter>", self.onHover)
        self.canvas.bind("<Leave>", self.onLeave)
        self.canvas.bind("<Button-1>", self.onClick)
        self.canvas.bind("<Button-3>", self.onOtherClick)
        self.canvas.bind("<Button-2>", self.onOtherClick)
        self.canvas.bind("<B1-Motion>", self.onDrag)
        self.canvas.bind("<ButtonRelease-1>", self.onUnclick)

    def onDrag(self, event):
        if not self.isClicking: return
        x = event.x - self.canvas.canvasx(0)
        percent = x / self.width
        percent = max(0, percent)
        percent = min(1, percent)

        if self.player.get_state() == vlc.State.Ended: 
            self.player.stop()
            self.player.play()
            self.parent.bPause.setUnpaused()
            self.parent.clipScene.updateOptions()
        
        if 0 < percent < 1:
            self.parent._setPlayerPosition(percent)

    def onClick(self, event):
        self.isClicking = True
        self.lastClick_PauseState = self.parent.bPause.isPaused

        x = event.x - self.canvas.canvasx(0)
        percent = x / self.width
        percent = max(0, percent)
        percent = min(1, percent)

        if self.player.get_state() == vlc.State.Ended: 
            self.player.stop()
            self.player.play()
            self.parent.bPause.setUnpaused()
            self.parent._setPlayerPosition(percent)
            self.parent.clipScene.updateOptions()


            while self.player.get_state() == vlc.State.Opening: pass
            self.player.play()
            self.parent.bPause.setUnpaused()
            self.after(100, lambda: (self.player.pause(), self.parent.bPause.setPaused(), self.onDrag(event)))

             
        elif not self.parent.bPause.isPaused:
            self.parent._setPlayerPosition(percent)
            self.player.play()
            self.player.pause()
            self.parent.bPause.setPaused()
        else:
            self.parent._setPlayerPosition(percent)

    def onUnclick(self, event):
        self.isClicking = False
        if not self.lastClick_PauseState:   # if unpaused on click
            self.player.play()
            self.parent.bPause.setUnpaused()
        self.lastClick_PauseState = None

        # update bar size
        if not self.isHovering:
            # update canvas size
            self.canvas.config(height=self.height)

        # call other update function
        self.parent.onLeave_ProgressBar(event=None)

    def onOtherClick(self, event):
        if not self.isClicking: return
        self.isClicking = False
        # update bar size
        if not self.isHovering:
            # update canvas size
            self.canvas.config(height=self.height)

        # call other update function
        self.parent.onLeave_ProgressBar(event=None)

    def onHover(self, event):
        self.isHovering = True
        # update canvas size
        self.canvas.config(height=self.height*2)

    def onLeave(self, event):
        self.isHovering = False

        if not self.isClicking:
            # update canvas size
            self.canvas.config(height=self.height)

        # call other update function
        self.parent.onLeave_ProgressBar(event=None)

    def setValue(self, value: float):
        """
            Sets progress bar value

            Params:
            value: number between 0 and 1
        """
        if self.parent.enableRestrictedPlayback:
            if self.player.get_length() == 0: return
            leftTime = self.parent.restrictLeft
            rightTime = self.parent.restrictRight
            leftPercent = leftTime / self.player.get_length()
            rightPercent = rightTime / self.player.get_length()

            self.canvas.coords(self.backBar, 0, 0, self.width, self.height * 2)
            
            if value < leftPercent:
                self.canvas.coords(self.progressBar, int(max(0, leftPercent) * self.width), 0, int(max(0, leftPercent) * self.width), self.height * 2)
            else:
                self.canvas.coords(self.progressBar, int(max(0, leftPercent) * self.width), 0, int(min(value, rightPercent) * self.width), self.height * 2)
                
        else:
            self.canvas.coords(self.backBar, 0, 0, self.width, self.height * 2)
            self.canvas.coords(self.progressBar, 0, 0, int(value * self.width), self.height * 2)

        # update restriction bar
        if self.parent.enableRestrictedPlayback:
            self.canvas.coords(self.restrictBar, int(leftPercent * self.width), 0, int(rightPercent * self.width), self.height * 2)



if __name__ == "__main__":
    root = tk.Tk()
    root.title("Bulk Video Trimmer")
    root.geometry(str(WINDOW_WIDTH) + "x" + str(WINDOW_HEIGHT))

    video = VideoPlayer(root, root=root, playOnOpen=False)
    video.grid(column=0, row=0, sticky='nsew')
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    
    video.openVideo("test.mp4")
    video.scheduleUpdates()

    root.mainloop()
