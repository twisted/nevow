; Compile with "makensis" from http://nsis.sourceforge.net/download/
Name "Nevow"
OutFile "nevow.exe"
InstallDir C:\Python23\Lib\site-packages
Page instfiles
Section "" 
  WriteUninstaller $INSTDIR\nevow\Uninst.exe
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Nevow" "UninstallString" "$INSTDIR\nevow\Uninst.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Nevow" "DisplayName" "Nevow"
  SetOutPath $INSTDIR\nevow
  File /r nevow\*.py
  File nevow\Canvas.swf
  SetOutPath $INSTDIR\formless
  File /r formless\*.py
  ExecWait "C:\Python23\pythonw C:\Python23\Lib\compileall.py $INSTDIR\nevow $INSTDIR\formless"
SectionEnd
Section "Uninstall"
  Delete $INSTDIR\Uninst.exe
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Nevow"
  RMDir /r $INSTDIR\nevow
  RMDir /r $INSTDIR\formless
SectionEnd
