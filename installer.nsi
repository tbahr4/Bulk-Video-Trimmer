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
SectionEnd

; Create a shortcut on the desktop
Section "Desktop Shortcut"
    SetShellVarContext all
    StrCpy $0 $DESKTOP
    CreateShortcut "$0\Bulk Video Trimmer.lnk" "$INSTDIR\Bulk Video Trimmer.exe"
SectionEnd

; Uninstaller section
Section "Uninstall"
    ; Remove installed files
    Delete "$INSTDIR\*.*"

    ; Remove folders
    RMDir /r "$INSTDIR\images"
    RMDir /r "$INSTDIR\ffmpeg"
    RMDir /r "$INSTDIR\plugins"

    ; Remove the installation directory
    RMDir "$INSTDIR"

    ; Remove the desktop shortcut
    SetShellVarContext all
    StrCpy $0 $DESKTOP
    Delete "$0\Bulk Video Trimmer.lnk"

    ; Remove the uninstaller registry entry
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Bulk Video Trimmer"
SectionEnd