
import tkinter as tk
import vlc
import threading
import time
import gui
from PIL import Image, ImageTk

WINDOW_HEIGHT = 649
WINDOW_WIDTH = 1024




class VideoPlayer(tk.Frame):
    def __init__(self, parent, screenWidth: int, screenHeight: int, playOnOpen: bool, backgroundHeight: int, restrictLeftButton = None, restrictRightButton = None, unrestrictLeftButton = None, unrestrictRightButton = None):
        """
            Params:
            screenWidth: the width of the video screen
            screenHeight: the height of the video screen
            playOnOpen: autoplay automatically upon opening a video using openVideo()
        """
        super().__init__(parent)
        root = parent
        self.parent = parent
        self.lastVolumeChange = 0  
        self.isVolumeBarVisible = False
        self.lastEndStateTime = 0
        self.timeToUpdateEndState = 1
        self.duration = 0
        self.fullscreenScaleX = root.winfo_screenwidth() / WINDOW_WIDTH
        self.fullscreenScaleY = root.winfo_screenheight() / WINDOW_HEIGHT
        self.isVideoOpened = False
        self.enableRestrictedPlayback = False
        self.restrictLeft = None
        self.restrictRight = None
        self.restrictLeftButton = restrictLeftButton
        self.restrictRightButton = restrictRightButton
        self.unrestrictLeftButton = unrestrictLeftButton
        self.unrestrictRightButton = unrestrictRightButton

        # properties
        self.playOnOpen = playOnOpen
        self.screenWidth = screenWidth
        self.screenHeight = screenHeight
        self.volume = 50

        # init vlc instance
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        
        # init properties
        self.player.audio_set_volume(self.volume)
        # progress bar
        self.progressBarHeight = 5
        self.progressBar = ProgressBar(self, self.player, width=screenWidth, height=self.progressBarHeight, bg='#383838', fg='#4287f5')
        # buttons
        padX = 5
        self.volumeBar = VolumeBar(self, player=self.player, defaultVolume=50, width=19, height=50)
        self.buttonSize = 25
        self.actionBar = ActionBar(self, self.player, buttonSize=self.buttonSize, progressBar=self.progressBar, volumeBar=self.volumeBar, progressBarHeight=self.progressBarHeight, padX=padX)
        self.bPause = self.actionBar.bPause
        # background
        self.background = tk.Canvas(self, width=WINDOW_WIDTH, height=screenHeight+backgroundHeight, bg='black', borderwidth=0, highlightthickness=0)
        # init canvas
        width, height = self.player.video_get_size(0)
        self.canvas = tk.Canvas(self, width=screenWidth, height=self.screenHeight, bg='black', borderwidth=0, highlightthickness=0)
        # fullscreen button, initialized with a list of all widgets to be resized
        self.bFullscreen = FullscreenButton(self, root=root, size=self.buttonSize)

        # display elements
        self.background.place(x=0, y=0)
        self.canvas.place(x=0,y=0)
        self.progressBar.place(x=0, y=screenHeight)
        self.actionBar.place(x=5, y=screenHeight+(self.progressBarHeight*2))
        root.update()  # update to get positions of button widgets 
        self.volumeBar.place(x=self.actionBar.bVolume.winfo_x() + 8, y=screenHeight - 55, width=self.volumeBar.width, height=self.volumeBar.height)
        self.bFullscreen.place(x=WINDOW_WIDTH-5-self.buttonSize, y=screenHeight+(self.progressBarHeight*2))
        self.actionBar.lift()
        self.bFullscreen.lift()
        self.progressBar.lift()
        self.volumeBar.lift()
        

        # add listener for events
        root.bind("<KeyPress>", self.onKeyPress)
        self.progressBar.bind("<Enter>", self.onHover_ProgressBar)
        self.progressBar.bind("<Leave>", self.onLeave_ProgressBar)
        root.bind("<FocusIn>", self.onWindowFocus)

    def onWindowFocus(self, event):
        """
            Used to avoid 0 size window on Win+D keypress
        """
        self.parent.geometry(str(WINDOW_WIDTH) + "x" + str(WINDOW_HEIGHT))

    def onHover_ProgressBar(self, event):
        self.progressBar.place(x=0, y=(self.screenHeight if not self.bFullscreen.isFullscreen else self.parent.winfo_screenheight()-self.progressBarHeight) - self.progressBar.height)
    
    def onLeave_ProgressBar(self, event):
        if not self.progressBar.isClicking and not self.progressBar.isHovering:
            self.progressBar.place(x=0, y=self.screenHeight if not self.bFullscreen.isFullscreen else self.parent.winfo_screenheight()-self.progressBarHeight)

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
            self.bPause.togglePause()       

            # do not toggle pause if in restricted mode and past boundary
            while self.player.get_state() == vlc.State.Opening: pass
            if self.enableRestrictedPlayback and (round(self.player.get_position(), 6) >= round(self.restrictRight / self.player.get_length(), 6) or round(self.player.get_position(), 6) < round(self.restrictLeft / self.player.get_length(), 6)):  
                self._setPlayerPosition(0)   # set back to start  
        elif key == "Left":
            self.seek(-10000)
        elif key == "Right":
            self.seek(10000)
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
        # reset values
        self.lastEndStateTime = 0
        self.duration = 0
        self.unrestrictPlayback()

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


    def play(self):
        self.bPause.setUnpaused()
    
    def pause(self):
        self.bPause.setPaused()

    def scheduleUpdates(self):
        updater = threading.Thread(target=self._update)
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

        # pause if at end of video
        framesToEnd = duration - self.player.get_time()
        if self.player.get_state() == vlc.State.Playing and framesToEnd < 250:
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

        if (timeSinceLastVolHover < 1 or timeSinceLastVolChange < 1):
            self.isVolumeBarVisible = True
            self.volumeBar.place(x=self.actionBar.bVolume.winfo_x() + 8, y=(self.screenHeight - 55) * (self.fullscreenScaleY if self.bFullscreen.isFullscreen else 1) + (22 if self.bFullscreen.isFullscreen else 0), width=self.volumeBar.width, height=self.volumeBar.height)
        else:   # hide
            self.isVolumeBarVisible = False
            self.volumeBar.place(x=self.actionBar.bVolume.winfo_x() + 8, y=(self.screenHeight - 55) * (self.fullscreenScaleY if self.bFullscreen.isFullscreen else 1) + (22 if self.bFullscreen.isFullscreen else 0), width=0, height=0)

        # update playback timer
        if self.isVideoOpened:
            if self.player.get_state() == vlc.State.Ended:
                self.actionBar.playbackTimer.setTime(self.player.get_length() / 1000)
            elif timeSinceLastEndState > self.timeToUpdateEndState or self.player.get_time() != 0:
                self.actionBar.playbackTimer.setTime(self.player.get_time() / 1000)

        # pause if in restricted mode and past boundary
        if duration != 0:
            if self.enableRestrictedPlayback and round(self.player.get_position(), 6) >= round(self.restrictRight / duration, 6): 
                if not self.bPause.isPaused: self.bPause.togglePause() 
                self._setPlayerPosition(self.restrictRight / duration) 

        # Schedule the next update
        self.after(10, self._update)

    def restrictPlayback(self, time1: int, time2: int):
        """
            Restricts playback to fall between the two time values
        """
        if time1 < 0 or time2 < 0 or time1 > self.player.get_length() or time2 > self.player.get_length() or time1 > time2: return
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
        self.restrictRight = 0
        


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
        self.bPause.grid(column=0, row=0, padx=padX)
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
        super().__init__(parent)
        self.root = root
        self.parent = parent
        self.isFullscreen = False
        self.lastFullscreenToggle = 0
        self.timeBetweenToggles = .2
        self.widgetData = {}

        image = Image.open("images/fullscreen.png")
        image.thumbnail((size, size))
        self.image = ImageTk.PhotoImage(image)
        self.button = tk.Button(self, width=size, command=self.toggleFullscreen, image=self.image, borderwidth=0, highlightthickness=0, bg="black", activebackground="black")

        self.button.pack()

    def toggleFullscreen(self):
        if not self.parent.isVideoOpened: return
        if time.time() - self.lastFullscreenToggle < self.timeBetweenToggles: return
        self.lastFullscreenToggle = time.time()
        self.isFullscreen = not self.isFullscreen

        # get scale value
        scaleX = self.parent.fullscreenScaleX
        scaleY = self.parent.fullscreenScaleY

        self.root.attributes("-fullscreen", self.isFullscreen)
        video = self.parent
        widgetList = [video.actionBar, video.bFullscreen, video.volumeBar]
        if self.isFullscreen:
            # video
            self.widgetData[video] = (video.winfo_x(), video.winfo_y())
            video.place(x=0, y=0, width=video.parent.winfo_screenwidth(), height=video.parent.winfo_screenheight())
            video.canvas.config(width=video.parent.winfo_screenwidth(), height=video.parent.winfo_screenheight())

            # hide widgets
            for widget in widgetList:
                x = widget.winfo_x()
                y = widget.winfo_y()
                width = widget.winfo_width()
                height = widget.winfo_height()
                self.widgetData[widget] = (x,y,width,height)
                widget.place_forget()

            # adjust widgets

            # progressbar
            self.widgetData[video.progressBar] = (video.progressBar.width, video.progressBar.canvas.winfo_width())
            video.progressBar.width = video.parent.winfo_screenwidth()
            video.progressBar.place(x=0, y=video.parent.winfo_screenheight() - video.progressBarHeight)
            video.progressBar.canvas.config(width=video.parent.winfo_screenwidth())
            

        else:
            # video
            data = self.widgetData[video]
            video.canvas.config(width=video.screenWidth, height=video.screenHeight)
            video.place(x=data[0], y=data[1], width=video.screenWidth, height=video.screenHeight + 40)

            # unhide widgets
            for widget in widgetList:
                data = self.widgetData[widget]
                widget.place(x=data[0], y=data[1], width=data[2], height=data[3])

            # adjust widgets

            # progressbar
            data = self.widgetData[video.progressBar]
            video.progressBar.width = data[0]
            video.progressBar.place(x=0, y=video.screenHeight)
            video.progressBar.canvas.config(width=data[1])
        
        

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
        images = [Image.open("images/volume-mute.png"), Image.open("images/volume-min.png"), Image.open("images/volume-mid.png"), Image.open("images/volume-max.png")]
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

        self.imPlay = Image.open("images/play.png")
        self.imPause = Image.open("images/pause.png")
        self.imPlay.thumbnail((size, size))
        self.imPause.thumbnail((size, size))
        self.playImage = ImageTk.PhotoImage(self.imPlay)
        self.pauseImage = ImageTk.PhotoImage(self.imPause)

        self.bPause = tk.Button(self, width=size, command=self.togglePause, image=self.playImage if startPaused else self.pauseImage, borderwidth=0, highlightthickness=0, bg="black", activebackground="black")
        self.bPause.image = self.playImage if startPaused else self.pauseImage

        self.bPause.pack()


    def togglePause(self):
        if not self.parent.parent.isVideoOpened: return

        # do not toggle pause if in restricted mode and past boundary
        while self.player.get_state() == vlc.State.Opening: pass
        #if self.parent.parent.enableRestrictedPlayback and round(self.player.get_position(), 6) >= round(self.parent.parent.restrictRight / self.parent.parent.player.get_length(), 6): 
            #self.parent.parent._setPlayerPosition(0)   # set back to start
            #print("resetting")

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

        image = Image.open("images/skip-15.png" if isForwardSkip else "images/back-15.png")
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
        super().__init__(parent)  
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
    root.title("Video Trimmer")
    root.geometry(str(WINDOW_WIDTH) + "x" + str(WINDOW_HEIGHT))
    root.resizable(width=False, height=False)

    video = VideoPlayer(root, screenWidth=WINDOW_WIDTH, screenHeight=int(root.winfo_screenheight()/2), playOnOpen=False, backgroundHeight=40)
    video.place(x=0,y=0, width=root.winfo_screenwidth(), height=root.winfo_screenheight())


    video.openVideo("test-long.mp4")
    video.scheduleUpdates()

    root.mainloop()
