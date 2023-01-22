from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from pydub import AudioSegment
import json
import subprocess
import datetime
import sys
import io
import os
from contextlib import redirect_stdout
from os import listdir
from os.path import isfile, join
from datetime import datetime
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import tkinter.messagebox as msgbox

# Properties
enable_logging = True



# log
# prints and logs the data to log file if it is enabled
#
def log(msg: str):
    if enable_logging: file.write(f"{msg}\n")
    print(msg)                              # print to console 

    # print to gui console
    tOutput.configure(state="normal")
    tOutput.insert(tk.END, f"{msg}\n")        
    tOutput.configure(state="disabled")
    tOutput.see(tk.END)

# trimClipOnParams
# Trims the clip at path 'filepath' between time1 and time2 seconds.
# Stores in output with name 'outputName'
#

def trimClipOnParams(filepath: str, time1: float, time2: float, outputName: str, muteAudio: bool, fileExtension: str):
    log(f"Trimming file from {str(round(time1, 2))} - {str(round(time2, 2))} seconds [{filepath}]")
    
    if muteAudio:
        ffmpeg_extract_subclip(filepath, time1, time2, targetname=f"temp.mp4")
        log(f"Muting audio[{filepath}]")

        import ffmpeg
        (
            ffmpeg
            .input(f"temp.mp4")
            .output(outputName, vcodec='copy', an=None)
            .run()
        )
        os.remove(f"temp.mp4") # clean up

    else:
        ffmpeg_extract_subclip(filepath, time1, time2, targetname=outputName)

# convertTime
# Converts the given string into a proper time format
#
# Acceptable formats:
# time-time
# Xms
# Xs    - X seconds
# Xm    - X minutes
# Xh    - X hours
# XmXs
# XhXmXs
# XhXmXsXXXms
# start
# end
# EXs (last X seconds)
#
def convertTime(timeString: str, filepath: str):
    # start form
    #
    if timeString.lower() == "start":
        return 0
    
    # end form
    #
    elif timeString.lower() == "end":
        return getClipLength(filepath)

    # last X seconds
    #
    elif timeString[0].upper() == 'E':  
        timeString = timeString[1:]     # remove E tag

        # create format - only allow last X seconds and X ms
        fmt = ''.join('%'+c.upper()+c for c in 's' if c in timeString)
        ms = '.%f' if '.' in timeString else ''
        fmt = fmt + ms

        # ensure that ms is 3 digits max
        if (ms != ''):
            if len(timeString.split(".")[1]) > 3:
                log(f"ERROR: invalid time format. 3 millisecond digits maximum [{filepath}]")
                sys.exit()

        time = datetime.strptime(timeString, fmt).time()
        seconds = time.second + (time.minute * 60) + (time.hour * 60 * 60) + (time.microsecond / 1000000)

        return getClipLength(filepath) - seconds



    # h/m/s form
    #
    elif 'h' in timeString or 'm' in timeString or 's' in timeString or 'ms' in timeString:  

        # create format
        fmt = ''.join('%'+c.upper()+c for c in 'hms' if c in timeString)
        ms = '.%f' if '.' in timeString else ''
        fmt = fmt + ms

        # ensure that ms is 3 digits max
        if (ms != ''):
            if len(timeString.split(".")[1]) > 3: 
                log(f"ERROR: invalid time format. 3 millisecond digits maximum [{filepath}]")
                sys.exit()

        time = datetime.strptime(timeString, fmt).time()
        seconds = time.second + (time.minute * 60) + (time.hour * 60 * 60) + (time.microsecond / 1000000)

        return seconds


    # INVALID form
    #
    else:
        log(f"ERROR: invalid time form [{filepath}]")
        raise Exception()
        
    
# getClipLength
# Returns the length of the clip at given path
#
def getClipLength(filepath: str):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries","format=duration", "-of","default=noprint_wrappers=1:nokey=1", filepath],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)

    try:
        return float(result.stdout)
    except:
        log(f"ERROR: cannot find file: [{filepath}]")
        


# splitStringData
# Splits the clip string data into trimmable data
#
def splitStringData(pathToDir: str, fileName: str):
    try:
        isMuted = False

        # save file dir
        path = pathToDir + fileName
        
        # get and remove file extension
        fileTypeStart = fileName.rfind('.')
        if (fileTypeStart == -1): log(f"ERROR: cannot find file extension [{path}]")
        fileExtension = fileName[fileTypeStart:]
        fileName = fileName[:-len(fileExtension)]
        
        # extract between -'s
        stringData = fileName.split("-")   

        # get ordering
        order = stringData[0][stringData[0].find('(') + 1 : stringData[0].find(')')]
        
        # get name
        name = stringData[1][1:]
        
        # get times
        time1 = None
        time2 = None
        
        # check for 0 or 1 or 2 times
        if len(stringData) == 2:
            # do nothing
            pass

        elif len(stringData) == 4:    # 2 times
            # check if tags are provided
            splitTime = stringData[3].split(" ")
            if len(splitTime) > 1:
                for i in range(1,len(splitTime)):
                    if splitTime[i].lower() == "(mute)":
                        isMuted = True

            time1 = stringData[2][1:]
            time2 = splitTime[0]


            
            
        else:                         # 1 time
            # check if tags are provided
            splitTime = stringData[2][1:].split(" ")
            if len(splitTime) > 1:
                for i in range(1,len(splitTime)):
                    if splitTime[i].lower() == "(mute)":
                        isMuted = True

            time1 = splitTime[0]

 
        # done; return resulting strings
        #
        t1,t2 = getTimes(time1, time2, path)        # convert times to true time floats
        return path, order, name, t1, t2, isMuted, fileExtension

    except:
        log(f"ERROR: invalid file name format {fileName} @ {pathToDir}")
        raise Exception()




# getTimes
# Computes the true float times depending on time strings
#
def getTimes(time1, time2, filepath: str):
    # no time specified
    # return original clip
    #
    if (time1 == None and time2 == None):
        return convertTime("start", filepath), convertTime("end", filepath)
        

    # 1 time specified
    # beginning or end of clip, depending on first char
    #
    elif (time2 == None):
        # check if only 'end' or 'start' are specified
        if (time1 == "start" or time1 == "end"):
            log(f"ERROR: invalid time format [{filepath}]")
            sys.exit()

        # time-end
        # will be properly handled for 'e'
        return convertTime(time1, filepath), convertTime("end", filepath)

    # 2 times specifed
    # simply start to end time
    #
    elif (time1 != None and time2 != None):
        return convertTime(time1, filepath), convertTime(time2, filepath)

    else: 
        log(f"ERROR: internal time calculation error [{filepath}]")
        sys.exit()




# trimClip
# Gather parameters of clip and perform trim
# May delay trim for pre-trim checks
#
def trimClip(pathToSrcDir: str, fileName: str, pathToDestDir: str, performTrim: bool):
    stringData = splitStringData(pathToSrcDir, fileName)

    # gather params
    path = stringData[0]
    order = stringData[1]
    name = stringData[2]
    time1 = stringData[3]
    time2 = stringData[4]
    isMuted = stringData[5]
    fileExtension = stringData[6]
    outputName = f"{pathToDestDir}/({order}) - {name}{fileExtension}"

    # check for valid times
    if (time1 > time2): 
        log(f"ERROR: Start time must be before the end time [{pathToSrcDir+fileName}]")
        sys.exit()
    if (time2 > getClipLength(pathToSrcDir+fileName)): 
        log(f"ERROR: End time out of bounds [{pathToSrcDir+fileName}]")
        sys.exit()

    # perform trim
    if performTrim:
        trimClipOnParams(path, time1, time2, outputName, isMuted, fileExtension[::1])



# getFilePaths
# gather all directories from folder path
#
def getFilePaths(dirPath: str):
    files = [file for file in listdir(dirPath) if isfile(join(dirPath, file))]
    return files

# testFiles
# Attempts pre-trim checks to be used before performing the full directory trim
def testFiles(pathToSrcDir: str):
    files = getFilePaths(pathToSrcDir)
    # for each filename, check if trim would work
    for fileName in files:
        trimClip(pathToSrcDir, fileName, None, False)       # Attempt pre-trim checks

# trimDirectory
# Trims all clips in specified directory
#
def trimDirectory(pathToSrcDir: str, pathToDestDir: str):
    global progressBar
    
    files = getFilePaths(pathToSrcDir)
    fileCount = len(files)
    currFile = 0

    # Generate output directory - should not occur as directory is currently selected
    #
    if (not os.path.isdir(pathToDestDir)):
        log(f"Generating output directory ({pathToDestDir})")
        os.mkdir(pathToDestDir)

    # for each filename, trim and update progress bar
    for fileName in files:
        trimClip(pathToSrcDir, fileName, pathToDestDir, True)

        # done trimming, update progress bar
        currFile += 1
        progressBar.config(value=currFile/fileCount*100)
        root.update_idletasks()         # force gui update









###
###         TODO
###

# multithreading? if it takes a while

# bool for enforcing strict ordering (places 1,2,3,... for each clip)

# order - NAME - time1-time2 
# auto-splice consecutive clips

# enable auto-ordering

# maintain order of folder automatically, otherwise user may specify ordering using (X)

# or view video and specify times, name, but do this after auto-ordering

# more tags

# check for valid format BEFORE continuing

# give option to enable logs, or just always on

# tick for close when done

#################################################
#                                               #
#                     MAIN                      #
#                                               #
#################################################


# Open log file if enabled
#
if enable_logging:
    # Generate output directory - should not occur as directory is currently selected
    #
    if (not os.path.isdir("logs")):
        os.mkdir("logs")

    now = str(datetime.now().strftime("%d-%m-%Y %H_%M_%S"))
    file = open(f"logs/log - {now}.txt", "w")
    file.write(f"{now}\n")





# init vars
#
sourceDir = None
destDir = None


#
# Display form
#

root = tk.Tk()
root.title("Video Trimmer")
root.iconbitmap("images/logo.ico")     # set the window's logo

root.geometry("400x281")
root.resizable(width=False, height=False)




# define event handlers
#

# bHelp_onClick
# Displays a help message tutorial
#
def bHelp_onClick():
    msgbox.showinfo("How to trim a clip", "To trim a list of clips, you must specify a valid file name format for every file in the directory.\n\nGENERAL FORMATS:\n(N) - Name - time1-time2\n(N) - Name - time1\n\nThe times are specific, though it allows many formats.\n\nAllowed times:\nThe following, when specified without a second time, will generate a clip starting at the specified time, but two times can be specified if needed.\nXh                      - Hours\nXm                     - Minutes\nXs                      - Seconds\nXms or XXXms  - Milliseconds\nOR any combination in that order:   XhXmXs\n\nIf 'e' is specified before any time (i.e. e10s), then the time acts in reverse and specifies the time at the end of the clip. \n\nstart        - Specifies the start of the original clip\nend         - Specifies the end of the original clip\n")







def bStart_onClick(event):
    try:
        global sourceDir
        global destDir
        global progressBar

        # disable input
        bStart.configure(state="disabled")
        bSetSource.configure(state="disabled")
        bSetDest.configure(state="disabled")

        # check for bad files
        log(f"Checking for bad files.")
        root.update_idletasks()         # force gui update
        testFiles(f"{sourceDir}/")
        

        # begin trim
        log(f"Beginning directory trim [{sourceDir}]")
        trimDirectory(f"{sourceDir}/", destDir)
        log(f"Done.")

        # re-enable input and reset fields
        bSetSource.configure(state="normal")
        bSetDest.configure(state="normal")

        tSourceDir.configure(state="normal")
        tSourceDir.delete("1.0", "end")
        tSourceDir.configure(state="disabled")

        tDestDir.configure(state="normal")
        tDestDir.delete("1.0", "end")
        tDestDir.configure(state="disabled")

        # reset globals
        sourceDir = None
        destDir = None

    except:
        # fell out, keep dirs but reset buttons
        bStart.configure(state="normal")
        bSetSource.configure(state="normal")
        bSetDest.configure(state="normal")
        progressBar.config(value=0)
        root.update_idletasks()         # force gui update

        
    


# bSetDest_onClick
# Allows the user to select a source directory
#
def bSetSource_onClick():
    global sourceDir
    global destDir

    # get file directory
    directory_path = filedialog.askdirectory()
    if directory_path == None or directory_path == "": return       # cancelled file select
    sourceDir = directory_path

    # update text box
    tSourceDir.configure(state="normal")
    tSourceDir.delete("1.0", "end")
    tSourceDir.insert("1.0", directory_path)
    tSourceDir.configure(state="disabled")

    # update start button if both source and dest are filled
    if sourceDir != None and destDir != None:
        bStart.configure(state="normal")

# bSetDest_onClick
# Allows the user to select a destination directory
#
def bSetDest_onClick():
    global sourceDir
    global destDir

    # get file directory
    directory_path = filedialog.askdirectory()
    if directory_path == None or directory_path == "": return       # cancelled file select
    destDir = directory_path

    # update text box
    tDestDir.configure(state="normal")
    tDestDir.delete("1.0", "end")
    tDestDir.insert("1.0", directory_path)
    tDestDir.configure(state="disabled")

    # update start button if both source and dest are filled
    if sourceDir != None and destDir != None:
        bStart.configure(state="normal")


# onClose
# Always runs on close
#
def onClose():
    if enable_logging: file.close()
    root.quit()
root.protocol("WM_DELETE_WINDOW", onClose)


# define elements

# menu bar
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)
file_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Menu", menu=file_menu)
# add items to the drop-down menu
file_menu.add_command(label="Help", command=bHelp_onClick)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)

tFileDisplay = tk.Label(root, text="Files", font=("Helvetica", 10))

bSetSource = tk.Button(root, width=20, text="Source Directory", command=bSetSource_onClick)
bSetDest = tk.Button(root, width=20, text="Destination Directory", command=bSetDest_onClick)
tSourceDir = tk.Text(root, height=1, width = 35, state="disabled", font=("Helvetica", 10), wrap="none")
tDestDir = tk.Text(root, height=1, width = 35, state="disabled", font=("Helvetica", 10), wrap="none")

tOutput = tk.Text(root, height=8, width=55, state="disabled", font=("Helvetica", 10), wrap="none")
tOutputText = tk.Label(root, text="Output", font=("Helvetica", 10))
scrollbar = tk.Scrollbar(root)

bStart = tk.Button(root, text="Start", width=7)
bStart.bind("<ButtonRelease-1>", lambda event: bStart_onClick(event) if bStart["state"] == "active" else None)        # only fire event if within bounds of button

progressBar = ttk.Progressbar(root, mode="determinate", maximum=100)
progressBar.config(value=0)






# styling for the progress bar
style = ttk.Style()
style.theme_create("style", parent="default", settings={
    "TProgressbar": {
        "configure": {
            "background": "lime",
            "troughcolor": "grey",
            "borderwidth": 1,
            "darkcolor": "red",
            "lightcolor": "yellow",
            "thickness": 2,
            "relief": "groove"
        }
    }
})
# apply the new style to the progress bar
style.theme_use("style")


# setup layout

tFileDisplay.grid(row=0, column=0, sticky="w")

bSetSource.grid(row=1, column=0, sticky="w")
bSetDest.grid(row=2, column=0, sticky="w")
tSourceDir.grid(row=1, column=1, sticky="w")
tDestDir.grid(row=2, column=1, sticky="w")

tOutputText.grid(row=3, column=0, sticky="w")
scrollbar.grid(row=4, column=1, sticky="nes")
tOutput.grid(row=4, column=0, columnspan=2)
# configure the output box to use the scrollbar
tOutput.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=tOutput.yview)

bStart.grid(row=5, column=0, columnspan=2, sticky="e")
bStart.configure(state="disabled")

progressBar.grid(row=6, column=0, columnspan=2, pady=1, sticky="we")


# center the grid horizontally
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

progressBar.config(value=0)




root.mainloop()

