from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
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
from tkinter import filedialog
import tkinter.messagebox as msgbox

# Properties
enable_logging = True
outputDirectory = "output"



# log
# prints and logs the data to log file if it is enabled
#
def log(msg: str):
    if enable_logging: file.write(f"{msg}\n")
    print(msg)

# trimClipOnParams
# Trims the clip at path 'filepath' between time1 and time2 seconds.
# Stores in output with name 'outputName'
#
def trimClipOnParams(filepath: str, time1: float, time2: float, outputName: str):
    log(f"Trimming file from {str(time1)} - {str(time2)} seconds [(]{filepath}]")
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

        time = datetime.datetime.strptime(timeString, fmt).time()
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

        time = datetime.datetime.strptime(timeString, fmt).time()
        seconds = time.second + (time.minute * 60) + (time.hour * 60 * 60) + (time.microsecond / 1000000)

        return seconds


    # INVALID form
    #
    else:
        log(f"ERROR: invalid time form [{filepath}]")
        sys.exit()
        
    
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
            time1 = stringData[2][1:]
            time2 = stringData[3]
            
        else:                       # 1 time
            time1 = stringData[2][1:]
        
        # done; return resulting strings
        #
        t1,t2 = getTimes(time1, time2, path)        # convert times to true time floats
        return path, order, name, t1, t2, fileExtension

    except:
        log(f"ERROR: invalid file name format [{path}]")
        sys.exit()




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





def trimClip(pathToDir: str, fileName: str):
    stringData = splitStringData(pathToDir, fileName)

    # gather params
    path = stringData[0]
    order = stringData[1]
    name = stringData[2]
    time1 = stringData[3]
    time2 = stringData[4]
    fileExtension = stringData[5]
    outputName = f"output/({order}) - {name}{fileExtension}"

    # check for valid times
    if (time1 > time2): 
        log(f"ERROR: Start time must be before the end time [{pathToDir+fileName}]")
        sys.exit()
    if (time2 > getClipLength(pathToDir+fileName)): 
        log(f"ERROR: End time out of bounds [{pathToDir+fileName}]")
        sys.exit()

    # perform trim
    trimClipOnParams(path, time1, time2, outputName)



# getFilePaths
# gather all directories from folder path
#
def getFilePaths(dirPath: str):
    files = [file for file in listdir(dirPath) if isfile(join(dirPath, file))]
    return files

# trimDirectory
# Trims all clips in specified directory
#
def trimDirectory(pathToDir: str):
    for fileName in getFilePaths(path):
        trimClip(path, fileName)


# combineClips
# Combines two specified clips
#
def combineClips(pathToDir: str, fileName1: str, fileName2: str):
    pass






###
###         TODO
###

# bool for enforcing strict ordering (places 1,2,3,... for each clip)

# order - NAME - time1-time2 
# auto-splice consecutive clips

# maintain order of folder automatically, otherwise user may specify ordering using (X)

# or view video and specify times, name, but do this after auto-ordering

#################################################
#                                               #
#                     MAIN                      #
#                                               #
#################################################


# Open log file if enabled
#
if enable_logging:
    file = open("log.txt", "w")
    file.write(str(datetime.now().strftime("%d/%m/%Y %H:%M:%S\n")))

# Generate output directory
#
if (not os.path.isdir(outputDirectory)):
    os.mkdir(outputDirectory)



# init vars
#
path = None
sourceDir = None
destDir = None


#
# Display form
#

root = tk.Tk()
root.title("Video Trimmer")
root.iconbitmap("images/logo.ico")     # set the window's logo

root.geometry("400x300")
root.resizable(width=False, height=False)

#file_browser = tk.filedialog.askopenfilename(parent=root)

#checkbox1 = tk.Checkbutton(root, text="Option 1")
#checkbox2 = tk.Checkbutton(root, text="Option 2")


#text1 = tk.Label(root, text="Enter text here:")
#text2 = tk.Text(root, height=10, width=30)

# define event handlers
#

# bHelp_onClick
# Displays a help message tutorial
#
def bHelp_onClick():
    msgbox.showinfo("Tutorial", "1. Rename all files to be trimmed to the proper file name format and place into a directory\n2. Designate the folder of clips to trim\n3. Designate the output directory for all of the clips\n4. Specify   \n\n\n TODO")

def bExit_onClick():
    sys.exit()


# bSetDest_onClick
# Allows the user to select a source directory
#
def bSetSource_onClick():
    global sourceDir

    # get file directory
    directory_path = filedialog.askdirectory()
    sourceDir = directory_path

    # update text box
    tSourceDir.configure(state="normal")
    tSourceDir.delete("1.0", "end")
    tSourceDir.insert("1.0", directory_path)
    tSourceDir.configure(state="disabled")

# bSetDest_onClick
# Allows the user to select a destination directory
#
def bSetDest_onClick():
    global destDir

    # get file directory
    directory_path = filedialog.askdirectory()
    destDir = directory_path

    # update text box
    tDestDir.configure(state="normal")
    tDestDir.delete("1.0", "end")
    tDestDir.insert("1.0", directory_path)
    tDestDir.configure(state="disabled")



# define elements

# menu bar
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)
file_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Menu", menu=file_menu)
# add items to the drop-down menu
file_menu.add_command(label="Help", command=bHelp_onClick)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=bExit_onClick)



tFileDisplay = tk.Label(root, text="Files", font=("Helvetica", 10))

bSetSource = tk.Button(root, width=20, text="Source Directory", command=bSetSource_onClick)
bSetDest = tk.Button(root, width=20, text="Destination Directory", command=bSetDest_onClick)
tSourceDir = tk.Text(root, height=1, width = 35, state="disabled", font=("Helvetica", 10), wrap="none")
tDestDir = tk.Text(root, height=1, width = 35, state="disabled", font=("Helvetica", 10), wrap="none")

tOutput = tk.Text(root, height=8, width=55, state="disabled", font=("Helvetica", 10), wrap="none")
tOutputText = tk.Label(root, text="Output", font=("Helvetica", 10))
scrollbar = tk.Scrollbar(root)

#file_browser.grid(row=0, column=0, sticky="w")
#checkbox1.grid(row=1, column=0, sticky="w")
#checkbox2.grid(row=2, column=0, sticky="w")
#text1.grid(row=3, column=0, sticky="w")
#text2.grid(row=4, column=0, sticky="w")
#button2.grid(row=5, column=1, sticky="w")






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

# center the grid horizontally
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)




root.mainloop()


#################################################
# close file if open
if enable_logging: file.close()