from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

def trimVideo(inputPath: str, outputPath: str, startTime: float, endTime: float):
    """
        Trims the provided video and writes it to outputPath based on given params
    """
    ffmpeg_extract_subclip(inputPath, startTime, endTime, targetname=outputPath)
    