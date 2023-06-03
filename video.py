
import tkinter as tk
import vlc
import threading
import time
from PIL import Image, ImageTk

WINDOW_HEIGHT = 768
WINDOW_WIDTH = 1024




class VideoPlayer(tk.Frame):
    def __init__(self, parent, screenWidth: int, screenHeight: int, playOnOpen: bool):
        """
            Params:
            screenWidth: the width of the video screen
            screenHeight: the height of the video screen
            playOnOpen: autoplay automatically upon opening a video using openVideo()
        """
        super().__init__(parent)
        self.parent = parent

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
        progressBarHeight = 5
        self.progressBar = ProgressBar(self, self.player, width=screenWidth, height=progressBarHeight, bg='#383838', fg='#4287f5', cursorRadius=10)
        # buttons
        self.actionBar = ActionBar(self, self.player, 25, self.progressBar, progressBarHeight)
        self.bPause = self.actionBar.bPause

        

        # init canvas
        width, height = self.player.video_get_size(0)
        self.canvas = tk.Canvas(self, width=screenWidth, height=self.screenHeight, bg='black', borderwidth=0, highlightthickness=0)
        

        # display elements
        self.canvas.pack()
        self.progressBar.place(x=0, y=screenHeight)
        self.actionBar.place(x=5, y=screenHeight)
        self.progressBar.lift()
        self.bg = self.canvas.create_rectangle(0,0, WINDOW_WIDTH, WINDOW_HEIGHT, fill="orange", outline="")

        # add listener for events
        root.bind("<KeyPress>", self.onKeyPress)
        self.progressBar.bind("<Enter>", self.onHover_ProgressBar)
        self.progressBar.bind("<Leave>", self.onLeave_ProgressBar)

    def onHover_ProgressBar(self, event):
        self.progressBar.place(x=0, y=self.screenHeight - self.progressBar.height)
    
    def onLeave_ProgressBar(self, event):
        if not self.progressBar.isClicking and not self.progressBar.isHovering:
            self.progressBar.place(x=0, y=self.screenHeight)

    def onKeyPress(self, event):
        key = event.keysym
        if key == "space":
            self.bPause.togglePause()
        elif key == "Left":
            self.seek(-10000)
        elif key == "Right":
            self.seek(10000)
        elif key == "Up":
            self.volume += 1 if self.volume < 100 else 0
            self.player.audio_set_volume(self.volume)
        elif key == "Down":
            self.volume -= 1 if self.volume > 0 else 0
            self.player.audio_set_volume(self.volume)
        elif key == "period":
            if self.bPause.isPaused:
                fps = self.player.get_fps()
                duration = int(1000 / fps)       # number of ms per frame
                self.seek(duration)
        elif key == "comma":
            if self.bPause.isPaused:
                fps = self.player.get_fps()
                duration = int(1000 / fps)       # number of ms per frame
                self.seek(-duration)
    
    def seek(self, time):
        """
            Seeks the video forward by the given time in milliseconds. 
            Specify a negative value for reverse seek
        """
        if time == 0: return
        newTime = self.player.get_time() + time
        duration = self.player.get_length()

        # do nothing if skipping on bounds
        if time < 0 and self.player.get_position() == 0: return
        if time > 0 and self.player.get_position() >= duration-100/duration: return
        
        # reset player if video is completed
        if self.player.get_state() == vlc.State.Ended:
            if time > 0: return
            else:
                self.player.stop()
                self.player.play()
                self.bPause.setUnpaused()
                self.player.set_position(max(0, duration-time))    
                self.progressBar.setValue(max(0, duration-time)) # update bar

        if newTime < 0: 
            self.player.set_position(0)
            self.progressBar.setValue(0) # update bar
        elif newTime > duration: 
            self.player.set_position(max(0, (duration-100) / duration))    # skip to right before end of stream
            self.progressBar.setValue(max(0, (duration-100) / duration)) # update bar
        else:
            self.player.set_time(newTime)
            self.progressBar.setValue(newTime/duration) # update bar


    def openVideo(self, filepath: str):
        media = self.instance.media_new(filepath)
        self.player.set_media(media)
        self.player.set_hwnd(self.canvas.winfo_id())
        
        # get video dimensions if screen size not specified
        if self.screenWidth == None and self.screenHeight == None:
            media.parse()
            while not media.is_parsed(): time.sleep(.1)     # TODO
            width = self.player.video_get_width()
            height = self.player.video_get_height()
            self.canvas.config(width=width, height=height)
        
        # Load thumbnail
        self.play()
        while not self.player.is_playing(): pass
        self.pause() 
        
        self.player.set_position(0)
        
        # play if set to autoplay on open
        if self.playOnOpen: self.play()


    def play(self):
        self.bPause.setUnpaused()
    
    def pause(self):
        self.bPause.setPaused()

    def scheduleUpdates(self):
        """
            Initializes constant updates to elements over an interval
        """
        # Get the VLC player position and duration
        position = self.player.get_position()
        duration = self.player.get_length()

        # update pause button
        playState = self.player.get_state()
        if playState == vlc.State.Ended:
            self.bPause.setPaused()

        # update progress bar
        if position != 0:       # do not update on restart video
            self.progressBar.setValue(1 if playState == vlc.State.Ended else position)

        # Schedule the next update
        self.after(10, self.scheduleUpdates)


class ActionBar(tk.Frame):
    """
        A frame of buttons used to control the video player
    """
    def __init__(self, parent, player, buttonSize: int, progressBar, progressBarHeight: int):
        super().__init__(parent, bg="black")
        self.parent = parent
        self.player = player
        self.buttonSize = buttonSize
        self.progressBar = progressBar
        padX = 5

        # init elements
        self.bPause = PauseButton(self, self.player, size=buttonSize)
        self.bSkipBackward = SkipButton(self, self.player, self.progressBar, pauseButton=self.bPause, isForwardSkip=False, size=buttonSize)
        self.bSkipForward = SkipButton(self, self.player, self.progressBar, pauseButton=self.bPause, isForwardSkip=True, size=buttonSize)
        self.bVolume = VolumeButton(self, defaultVolume=50, size=buttonSize)

        # display
        self.bPause.grid(column=0, row=0, padx=padX, pady=progressBarHeight*2)
        self.bSkipBackward.grid(column=1, row=0, padx=padX)
        self.bSkipForward.grid(column=2, row=0, padx=padX)
        self.bVolume.grid(column=3, row=0, padx=padX)

        self.after(100, self.retrieve_coordinates)

    def retrieve_coordinates(self):
        # Print coordinates of the PauseButton relative to the root window
        print("PauseButton Coordinates:", self.bPause.winfo_x(), self.bPause.winfo_y())



class VolumeButton(tk.Frame):
    """
        A volume button for muting and changing output volume
    """
    def __init__(self, parent, defaultVolume: int, size: int = 50):
        super().__init__(parent)
        self.volume = defaultVolume

        image = Image.open("images/volume.png")
        image.thumbnail((size, size))
        self.image = ImageTk.PhotoImage(image)

        self.bVolume = tk.Button(self, width=size, command=self.toggleMute, image=self.image, borderwidth=0, highlightthickness=0, bg="black", activebackground="black")

        self.bVolume.pack()

    def toggleMute(self):
        pass


class PauseButton(tk.Frame):
    """
        A visual pause button for the video player
    """
    def __init__(self, parent, player, startPaused: bool = True, size: int = 50):
        super().__init__(parent)
        self.player = player
        self.isPaused = startPaused

        imPlay = Image.open("images/play.png")
        imPause = Image.open("images/pause.png")
        imPlay.thumbnail((size, size))
        imPause.thumbnail((size, size))
        self.playImage = ImageTk.PhotoImage(imPlay)
        self.pauseImage = ImageTk.PhotoImage(imPause)

        self.bPause = tk.Button(self, width=size, command=self.togglePause, image=self.playImage if startPaused else self.pauseImage, borderwidth=0, highlightthickness=0, bg="black", activebackground="black")
        self.bPause.image = self.playImage if startPaused else self.pauseImage

        self.bPause.pack()


    def togglePause(self):
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
        if self.isForwardSkip == False and self.player.get_position() == 0: return
        if self.isForwardSkip and self.player.get_position() >= duration-100/duration: return
        
        # reset player if video is completed
        if self.player.get_state() == vlc.State.Ended:
            if self.isForwardSkip: return
            else:
                self.player.stop()
                self.player.play()
                self.pauseButton.setUnpaused()
                self.player.set_position(max(0, duration-15000))
                self.progressBar.setValue(max(0, duration-15000)) # update bar
                

        if newTime < 0: 
            self.player.set_position(0)
            self.progressBar.setValue(0) # update bar
        elif newTime > duration: 
            self.player.set_position(max(0, (duration-100) / duration))    # skip to right before end of stream
            self.progressBar.setValue(max(0, (duration-100)/duration)) # update bar
        else:
            self.player.set_time(newTime)
            self.progressBar.setValue(newTime/duration) # update bar
        
        
        

class ProgressBar(tk.Frame):
    def __init__(self, parent, player, width: int, height: int, bg: str, fg: str, cursorRadius: int):
        super().__init__(parent)  
        self.parent = parent
        self.width = width
        self.height = height
        self.player = player
        self.isHovering = False
        self.isClicking = False

        # instances
        self.canvas = tk.Canvas(self, width=width, height=height, borderwidth=0, highlightthickness=0)
        self.backBar = self.canvas.create_rectangle(0, 0, self.width, self.height, fill=bg, width=0)
        self.progressBar = self.canvas.create_rectangle(0, 0, 0, self.height, fill=fg, outline='')

        # build
        self.canvas.pack()

        # add listener for events
        self.canvas.bind("<Enter>", self.onHover)
        self.canvas.bind("<Leave>", self.onLeave)
        self.canvas.bind("<Button-1>", self.onClick)
        self.canvas.bind("<B1-Motion>", self.onDrag)
        self.canvas.bind("<ButtonRelease-1>", self.onUnclick)

    def onDrag(self, event):
        x = event.x - self.canvas.canvasx(0)
        percent = x / self.width
        percent = max(0, percent)
        percent = min(1, percent)

        if self.player.get_state() == vlc.State.Ended: 
            self.player.stop()
            self.player.play()
            self.parent.bPause.setUnpaused()
        self.player.set_position(percent)

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
        self.player.set_position(percent)

        # pause until unclick
        if not self.parent.bPause.isPaused:
            self.player.pause()
            self.parent.bPause.setPaused()

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
            # update bar size
            x1, y1, x2, y2 = self.canvas.coords(self.backBar)
            self.canvas.coords(self.backBar, 0, 0, x2, self.height)
            x1, y1, x2, y2 = self.canvas.coords(self.progressBar)
            self.canvas.coords(self.progressBar, 0, 0, x2, self.height)  

        # call other update function
        self.parent.onLeave_ProgressBar(event=None)

    def onHover(self, event):
        self.isHovering = True
        # update canvas size
        self.canvas.config(height=self.height*2)
        # update bar size
        x1, y1, x2, y2 = self.canvas.coords(self.backBar)
        self.canvas.coords(self.backBar, 0, 0, x2, self.height * 2)
        x1, y1, x2, y2 = self.canvas.coords(self.progressBar)
        self.canvas.coords(self.progressBar, 0, 0, x2, self.height * 2)

    def onLeave(self, event):
        self.isHovering = False

        if not self.isClicking:
            # update canvas size
            self.canvas.config(height=self.height)
            # update bar size
            x1, y1, x2, y2 = self.canvas.coords(self.backBar)
            self.canvas.coords(self.backBar, 0, 0, x2, self.height)
            x1, y1, x2, y2 = self.canvas.coords(self.progressBar)
            self.canvas.coords(self.progressBar, 0, 0, x2, self.height)  

    def setValue(self, value: float):
        """
            Sets progress bar value

            Params:
            value: number between 0 and 1
        """
        self.canvas.coords(self.backBar, 0, 0, self.width, self.height * (2 if self.isHovering or self.isClicking else 1))
        self.canvas.coords(self.progressBar, 0, 0, int(value * self.width), self.height * (2 if self.isHovering or self.isClicking else 1))



if __name__ == "__main__":
    root = tk.Tk()
    root.title("Video Trimmer")
    root.geometry(str(WINDOW_WIDTH) + "x" + str(WINDOW_HEIGHT))
    root.resizable(width=False, height=False)

    video = VideoPlayer(root, screenWidth=WINDOW_WIDTH, screenHeight=int(1080/2), playOnOpen=False)
    video.place(x=0,y=0, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)


    video.openVideo("test-long.mp4")

    updater = threading.Thread(target=video.scheduleUpdates)
    updater.start()

    root.mainloop()
