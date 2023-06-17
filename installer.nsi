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
    SetOutPath $TEMP   
    
    ; Copy the requirements.txt file
    File "requirements.txt"

    ; Install dependencies
    ExecWait 'pip install -r requirements.txt'

    ; Delete the requirements.txt file
    Delete "$TEMP\requirements.txt"

    ; Set output path
    SetOutPath $INSTDIR   

    ; Install Python app
    File "dist\Bulk Video Trimmer.exe"

    ; Copy the "images" folder
    SetOutPath $INSTDIR\images
    File /r "dist\images\*.*"

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

    ; Remove the uninstaller registry entry
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Bulk Video Trimmer"
SectionEnd
