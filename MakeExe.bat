pyinstaller --add-data "images;images" -F -w --additional-hooks-dir=. -i images\logo.ico main.py -n "Bulk Video Trimmer"

set "dest=dist"
robocopy "plugins" "%dest%\plugins" /E
robocopy "ffmpeg" "%dest%\ffmpeg" /E
copy "libvlc.dll" "%dest%"
copy "libvlccore.dll" "%dest%"
pause