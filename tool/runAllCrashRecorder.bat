@echo off
setlocal enabledelayedexpansion
path=%path%;c:\androidtools\platform-tools;C:\androidtools;

REM Clean up any device list left over from a prior run

del /Q /F devices.txt
del /Q /F temp.txt

REM get a list of all of the attached Android devices
adb devices > temp.txt
timeout 5
find "device" temp.txt > devices.txt

REM If a APK was specified on the command line then install that APK
for /F "skip=3 tokens=1" %%i in (.\devices.txt) DO (
	start CrashRecorder_ver5.3 %%i 
	
)

REM Clean up
timeout 5
del /Q /F devices.txt
del /Q /F temp.txt
@echo on