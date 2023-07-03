; Example installer.nsi

; Set the name of the installer
Outfile "BVTsetup.exe"
Name "Bulk Video Trimmer"

; Default installation directory
InstallDir "$PROGRAMFILES\Bulk Video Trimmer"

; Request administrator privileges
RequestExecutionLevel admin

; Installer sections
Section
    ; Set output path
    SetOutPath $INSTDIR   

    ; Add Application
    File "dist\Bulk Video Trimmer.exe"

    ; Copy folders
    SetOutPath $INSTDIR\ffmpeg
    File /r "dist\ffmpeg\*.*"
    SetOutPath $INSTDIR\plugins
    File /r "dist\plugins\*.*"

    ; Copy libs
    SetOutPath $INSTDIR
    File "libvlc.dll"
    File "libvlccore.dll"

    ; Write the uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; Register the uninstaller in the system registry
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Bulk Video Trimmer" "DisplayName" "Bulk Video Trimmer"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Bulk Video Trimmer" "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Bulk Video Trimmer" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Bulk Video Trimmer" "NoRepair" 1
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Bulk Video Trimmer" "DisplayIcon" "$\"$INSTDIR\Bulk Video Trimmer.exe$\""

    ; Add to PATH
    $EnvVarUpdate $0 "PATH" "A" "HKLM" "$INSTDIR\ffmpeg\bin"  
SectionEnd

; Create a shortcut on the desktop
Section "Desktop Shortcut"
    SetShellVarContext all
    SetOutPath $INSTDIR
    SetShellVarContext current
    ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders" "Desktop"
    CreateShortcut "$0\Bulk Video Trimmer.lnk" "$INSTDIR\Bulk Video Trimmer.exe"
SectionEnd

; Uninstaller section
Section "Uninstall"
    ; Remove installed files
    Delete "$INSTDIR\*.*"

    ; Remove the "images" folder
    RMDir /r "$INSTDIR\images"

    ; Remove the installation directory
    RMDir "$INSTDIR"

    ; Remove the desktop shortcut
    SetShellVarContext current
    ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders" "Desktop"
    Delete "$0\Bulk Video Trimmer.lnk"

    ; Remove from PATH
     $un.EnvVarUpdate $0 "PATH" "R" "HKLM" "$INSTDIR\ffmpeg\bin"  

    ; Remove the uninstaller registry entry
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Bulk Video Trimmer"
SectionEnd