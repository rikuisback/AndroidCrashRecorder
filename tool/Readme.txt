CrashRecorder
--------------------------------------------------------------------------------------------------------------------------------------------
Description
Script to monitor logcat for crashes and capture logcat and bugreport once observed


********************************************************************************************************************************************
Instructions :
-------------
1. Replace the given android serial_id in "dev_id.txt" to serial id of device under test.

2. Default crash keywords are "uncaught exception, FATAL EXCEPTION, : ANR in, Fatal signal, Force finishing activity",
 if want to add or remove keywords, edit "config.txt" file.

3. Double click on "CrashRecorder_Ver4.1.exe" and the script will start monitoring live logcat logs from DUT and capture logcat & 
Bugreport in case of any crash.

4. To STOP the script press Ctrl+C, a HTML file "CrashRecords.html" will be generated showing all the caught and respective log location.

5. If the utility needs to be run on all the connected Android devices , double click on "runAllCrashRecorder.bat" **

**Note- Make sure to take backup of all the previous logs before starting the batch, as it will delete the old logs

*********************************************************************************************************************************************

Version 3.2 Release notes:

1. Fixed issue inhibiting the capturing of bugreport logs
2. Handled adb diconnection
3. Added module to generate HTML report showing exception and corresponding logs on keyboard interrupt
4. Added delays between each log capturing commands to ensure proper capture logs
5. Added logic to avaoid capturing of same issues multiple times

.............................................................................................................................................................................................

Version 4.0 Release notes:

1. Added support for multiple devices 
2. Enhanced HTML reporting module to generate device wise reports for multiple devices

...............................................................................................................................................................................................

Version 4.1 Release notes:

1. Added functionality to detect Shutdown\Reboot and collect logcat till device shutdowns.
2. Enhanced HTML reporting module to show reboot counts.
3. Added commands in batch file to delete old logs


...............................................................................................................................................................................................

Version 4.2 Release notes:

1. Fixed bug preventing capturing of redundant shutdown/ reboot logs.
2. Added logic to accomodate logcat line containing the process in which Fatal Exception occured.
3. Enhanced HTML reporting to give the start time of the tool [gives both PC time and DUT time as 
many times the PC & DUT are not in sync]
4. Added logic to detect and report abrupt rest and collect logs once device is online 
[ abrupt reset here means reboot without notifying the logcat it is shutting down for e.g "adb reboot"
where device doesn't gracefully shutdown all the OS services before shutting down ]

................................................................................................................................................................................................
Version 5.0  Release notes:

1. Added functionality to take screenshot on occurence of crash in addition to capturing logcat and bugreport

................................................................................................................................................................................................
Version 5.1  Release notes:

1. Fixed the addition of additional line while capturing bugreport 