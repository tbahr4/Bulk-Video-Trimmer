from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import json
import subprocess
import datetime
import sys
import io
import os
from contextlib import redirect_stdout

# bool for enforcing strict ordering (places 1,2,3,... for each clip)

# order - NAME - time1-time2 
# auto-splice consecutive clips

# maintain order of folder automatically, otherwise user may specify ordering using (X)

# or view video and specify times, name, but do this after auto-ordering




# trimClipOnParams
# Trims the clip at path 'filepath' between time1 and time2 seconds.
# Stores in output with name 'outputName'
#
def trimClipOnParams(filepath: str, time1: float, time2: float, outputName: str):
    print(f"Trimming file from {str(time1)} - {str(time2)} seconds ({filepath})")
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
            if len(timeString.split(".")[1]) > 3: sys.exit("ERROR: invalid time format. 3 millisecond digits maximum")

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
            if len(timeString.split(".")[1]) > 3: sys.exit("ERROR: invalid time format. 3 millisecond digits maximum")

        time = datetime.datetime.strptime(timeString, fmt).time()
        seconds = time.second + (time.minute * 60) + (time.hour * 60 * 60) + (time.microsecond / 1000000)

        return seconds


    # INVALID form
    #
    else:
        sys.exit("ERROR: invalid time form")
        
    
# getClipLength
# Returns the length of the clip at given path
#
def getClipLength(filepath: str):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries","format=duration", "-of","default=noprint_wrappers=1:nokey=1", filepath],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)

    try:
        return float(result.stdout)
    except:
        print("ERROR: cannot find file: \"" + str(filepath) + "\"")
        


# splitStringData
# Splits the clip string data into trimmable data
#
def splitStringData(fileString: str):
    try:
        # save file dir
        path = fileString

        # get and remove file extension
        fileTypeStart = fileString.rfind('.')
        if (fileTypeStart == -1): print("ERROR: cannot find file extension")
        fileExtension = fileString[fileTypeStart:]
        fileString = fileString[:-len(fileExtension)]

        # extract between -'s
        stringData = fileString.split("-")
        

        # get ordering
        order = stringData[0][len(stringData[0])-3]
        
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
        sys.exit("ERROR: invalid file name format")




# getTimes
# Computes the true float times depending on time strings
#
def getTimes(time1, time2, filepath: str):
    # no time specified
    # return original clip
    #
    if (time1 == None and time2 == None):
        a = convertTime("start", filepath), convertTime("end", filepath)
        return a

    # 1 time specified
    # beginning or end of clip, depending on first char
    #
    elif (time2 == None):
        # check if only 'end' or 'start' are specified
        if (time1 == "start" or time1 == "end"):
            sys.exit("ERROR: invalid time format")

        # time-end
        # will be properly handled for 'e'
        return convertTime(time1, filepath), convertTime("end", filepath)

    # 2 times specifed
    # simply start to end time
    #
    elif (time1 != None and time2 != None):
        return convertTime(time1, filepath), convertTime(time2, filepath)

    else: 
        sys.exit("ERROR: internal time calculation error")




#trimClipOnParams("TestVideos/(7) - Clip7 - E10s.mp4", convertTime("e1s", "TestVideos/(7) - Clip7 - E10s.mp4"), convertTime("end", "TestVideos/(7) - Clip7 - E10s.mp4"), "output/out.mp4")

def trimClip(filepath: str):
    stringData = splitStringData(filepath)

    # gather params
    path = stringData[0]
    order = stringData[1]
    name = stringData[2]
    time1 = stringData[3]
    time2 = stringData[4]
    fileExtension = stringData[5]
    outputName = f"output/({order}) - {name}{fileExtension}"

    # perform trim
    trimClipOnParams(path, time1, time2, outputName)








path = "TestVideos/"
if (not os.path.isdir("output")):
    os.mkdir("output")

#trimClip(path + "(1) - Clip1 - 0s-10s.mp4")         
#trimClip(path + "(2) - Clip2 - 1m50s-2m.mp4")
#trimClip(path + "(3) - Clip3 - start-end.mp4")
#trimClip(path + "(4) - Clip4 - 1m50s-end.mp4")
#trimClip(path + "(5) - Clip5 - 1m50s.mp4")
#trimClip(path + "(6) - Clip6 - 1s.5.mp4")
#trimClip(path + "(7) - Clip7 - E10s.mp4")
#trimClip(path + "(8) - Clip8.mp4")
#trimClip(path + "(9) - Clip9 out of bounds - start-1h.mp4")               # SHOULD start at 1s, then goto end instead
                            # also handle when start time is out of bounds, throw error, rather than trim


                            # also git before continuing