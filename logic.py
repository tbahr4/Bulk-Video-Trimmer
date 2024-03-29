#
# logic.py
#
# Contains the logic necessary to trim video files
#

import multiprocessing
import subprocess
import os
import tempfile
import threading

# set ffmpeg path temporarily
os.environ["PATH"] = f"{os.getcwd()}" + r'\ffmpeg\bin' + f"{os.pathsep}{os.environ['PATH']}"


def trimVideo(inputPath: str, outputPath: str, startTime: float, endTime: float, isFramePerfect: bool, fullVideoLength: float, trimScene = None):
    """
        Trims the provided video and writes it to outputPath based on given params
    """
    # start by checking for any video already in the output
    if os.path.exists(outputPath):
        raise Exception(f"Video already exists: [{outputPath}]")

    if isFramePerfect:
        # Get the number of CPU cores
        threads = multiprocessing.cpu_count()       # logical processors, not physical cores

        # delete unprocessed file if needed
        if os.path.exists(outputPath):
            os.remove(outputPath)

        command = [
            'ffmpeg',
            '-ss', str(startTime),      # set start time
            '-to', str(endTime + 16/1000), # set end time (16/1000 includes final frame)
            '-i', str(inputPath),       # set input file
            '-c:v', 'libx264',          # set video codec
            '-crf', '15',               # set quality (0=lossless)
            '-preset', 'medium',        # set encoding time to file size ratio
            '-threads', str(threads-2), # set thread count
            '-c:a', 'libmp3lame',       # set audio codec
            '-b:a', '320k',             # set audio bitrate
            str(outputPath)             # set output file
        ]

        # exec on separate thread
        def execCommand():
            subprocess.run(command, creationflags=subprocess.CREATE_NO_WINDOW)
        cmdThread = threading.Thread(target=execCommand)
        cmdThread.start()

        while cmdThread.is_alive():
            trimScene.root.update()
            

        

    else:
        # since this is not frame perfect, need to grab adjactent keyframes
        interval = 5
        command = [
            'ffprobe',
            '-skip_frame', 'nokey',                # skip non-keyframes
            '-select_streams', 'v:0',              # set video stream to default
            '-show_entries', 'frame=pts_time',     # outputs only the timestamp
            '-of', 'csv=print_section=0',          # set output format
            '-read_intervals', f'{startTime-interval}%{startTime}',      # set time interval
            str(inputPath)                         # set input file
        ]

        # get keyframe start time
        #
        keyStartTime = None
        while keyStartTime == None:
            
            # exec on separate thread
            def execCommand(event):
                result = subprocess.run(command, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                event.returnValue = result
            event = threading.Event()
            cmdThread = threading.Thread(target=execCommand, args=(event,))
            cmdThread.start()
            
            while cmdThread.is_alive():
                trimScene.root.update()
            result = event.returnValue


            # clean output
            output = result.stdout.split('\n')[:-1]
            cleaned_output = []
            for line in output:
                if line != '':
                    new_line = line.split(",")[0]
                    cleaned_output.append(new_line)
            output = cleaned_output
            
            
            # get previous frame
            if keyStartTime == None:
                currFrame = None
                for frame in output:
                    if float(frame) <= startTime:
                        currFrame = float(frame)
                    else: break
                keyStartTime = currFrame        # keyframe is previous, or none if no frames found

            # if not found and out of bounds, not found
            if keyStartTime == None and startTime - interval < 0: 
                keyStartTime = 0
                break

            # if not found, increase interval
            interval += 5
            command[10] = f'{startTime-interval}%{startTime-interval+5}'


        # get keyframe end time
        #
        interval = 5
        command[10] = f'{endTime}%{endTime+interval}'
        keyEndTime = None
        while keyEndTime == None:
            
            # exec on separate thread
            def execCommand(event):
                result = subprocess.run(command, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                event.returnValue = result
            event = threading.Event()
            cmdThread = threading.Thread(target=execCommand, args=(event,))
            cmdThread.start()
            
            while cmdThread.is_alive():
                trimScene.root.update()
            result = event.returnValue


            # clean output
            output = result.stdout.split('\n')[:-1]
            cleaned_output = []
            for line in output:
                if line != '':
                    new_line = line.split(",")[0]
                    cleaned_output.append(new_line)
            output = cleaned_output
            

            # get next frame
            if keyEndTime == None:
                for frame in output:
                    if float(frame) >= endTime:
                        keyEndTime = float(frame)      # keyframe is next, or none if no frames found
                        break    

            # if not found and out of bounds, not found
            if keyEndTime == None and endTime + interval > fullVideoLength/1000: 
                keyEndTime = fullVideoLength/1000
                break

            # if not found, increase interval
            interval += 5
            command[10] = f'{endTime+interval-5}%{endTime+interval}'

        # extract on the corrected times
        command = ['ffmpeg', '-loglevel', 'quiet', '-i', inputPath, '-ss', str(keyStartTime-.1), '-to', str(keyEndTime+.1), '-c', 'copy', '-map', '0', outputPath]

        # exec on separate thread
        def execCommand():
            subprocess.run(command, creationflags=subprocess.CREATE_NO_WINDOW)
        cmdThread = threading.Thread(target=execCommand)
        cmdThread.start()

        while cmdThread.is_alive():
            if trimScene != None:
                trimScene.root.update()



def checkIsSilent(inputPath: str, startTime: float, endTime: float, trimScene = None):
    """
        Returns true if the video has no audio (only checks the first 5 seconds)
    """
    command = ['ffmpeg', '-i', inputPath, '-map', '0:a:1?', '-af', 'astats', '-f', 'null', '-ss', str(startTime-1), '-to', str(endTime+1), '-threads', '10', '-']

    # exec on separate thread
    def execCommand(event):
        result = subprocess.run(command, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        event.returnValue = result.stdout, result.stderr

    # check multiple positions for silence to save time
    event = threading.Event()
    cmdThread = threading.Thread(target=execCommand, args=(event,))
    cmdThread.start()

    while cmdThread.is_alive():
        if trimScene != None:
            trimScene.root.update()

    cmdThread.join()
    result = event.returnValue


    # process results
    noSound = []
    data = result[0 if len(result[0]) > 0 else 1].split('\n')
    for line in data:
        if line[37::].startswith("RMS level dB"): 
            if len(line) < 50: return False
            else: return line[51::] == "-inf"

    return False



#
# Main
#
if __name__ == "__main__":
    for file in ['test.mp4','test2.mp4','test3.mp4','test-2hr.mp4','nosound.mp4','multitrack.mp4','nosound2.mp4']:
        print(checkIsSilent(file, 0, 5))