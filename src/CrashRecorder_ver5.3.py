# ----------------------------------------------------------------------------------------------------------------------
# Name Of File: CrashRecorder_ver5.3.py                                                                                #
# Author: Ashish Kumar                                                                                                 #
# Purpose Of File: Script to monitor logcat for crashes and capture logcat and bugreport once observed                 #
#                                                                                                                      #
# History:                                                                                                             #
# Date                   Author                  Changes                                                               #
# 09/01/2015             Ashish Kumar            First Version                                                         #
# 09/23/2015             Ashish Kumar            Stable version with shutdown detection implemented                    #
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
import subprocess
import os
import sys
import time
from datetime import datetime

lastErrorLine = None
rebootCount = 0
deviceNotAvailableCount = 0

# ----------------------------------------------------------------------------------------------------------------------
#   logMonitor
#
#   DESCRIPTION
#   1.Reads keywords from Config file
#   2.Finding keywords in running logcat lines and calling appropriate log capturing module once found
#   Args
#   Arg. 3
#   device_id - adb serial id of the the Device under test (DUT}
#   productName - DUT model name [getprop ro.product.mode]
#   buildName - DUT build details [ro.build.fingerprint]
# ----------------------------------------------------------------------------------------------------------------------


def logMonitor(device_id, productName = None, buildName = None):
    try:
        global lastErrorLine
        startTime = datetime.now()
        startTime=startTime.strftime('%a %b %d %H:%M:%S %Z %Y')
        deviceTime = subprocess.Popen('adb -s ' + device_id + ' shell date', shell=False,
                                               stdout=subprocess.PIPE).stdout.read().rstrip()
        startTime = startTime + '|'+ deviceTime

        statusFilePath = os.getcwd() + "/" + device_id + "/status.txt"
        if os.path.exists(statusFilePath):
            os.remove(statusFilePath)
        if not os.path.exists("config.txt"):
            keywords = ["uncaught exception", "FATAL EXCEPTION", ": ANR in", "Fatal signal", "Force finishing activity"]
        else:
            configFile = open("config.txt", 'r')
            keywords = str(configFile.read()).split(',')
        errorLine = None
        shutdownflag = False
        fatalErrorFlag = False
        while True:
            print keywords
            proc = subprocess.Popen(['adb', '-s', device_id, 'wait-for-device', 'logcat', '-v', 'time', '*:D'],
                                    stdout=subprocess.PIPE)
            for line in proc.stdout:
                print line
                if 'I/ShutdownThread' in line :
                    print "***********************"
                    print "device is shutting down"
                    print "***********************"
                    shutdownflag = True
                    proc.kill()
                    break
                elif fatalErrorFlag:
                    errorLine += "\t"+line
                    fatalErrorFlag = False
                    proc.kill()

                elif any(keyword in line for keyword in keywords):
                    if 'E/' in line or 'F/' in line:
                        if not 'FATAL EXCEPTION' in line:
                            errorLine = line
                            print "***************************************************"
                            print " found crash in line: ", line
                            print "***************************************************"
                            proc.kill()
                            break
                        else:
                            errorLine = line.rstrip()
                            fatalErrorFlag = True
                            proc.kill()
                elif 'tombstones' in line :
                    print "****************************************"
                    print "Tombstone found in line:",line
                    print "****************************************"
                    errorLine = line
                    proc.kill()
                    break
                    
                        

            proc.wait()
            print "Error line:",errorLine
            if shutdownflag is True:
                reboot_logs(device_id,shutdownflag)
                shutdownflag = False

            elif (errorLine is not None) and ((lastErrorLine is not None and lastErrorLine != errorLine)
                                              or (lastErrorLine is None)):
                if not fatalErrorFlag:
                    capture_log(device_id, errorLine)
            else:
                if not waitForDevice(device_id):
                    shutdownflag = False
                    reboot_logs(device_id, shutdownflag)
                else:
                    pass
    except KeyboardInterrupt:
        htmlReport(device_id, productName, buildName, startTime)

# ----------------------------------------------------------------------------------------------------------------------
#   reboot_logs
#
#   DESCRIPTION
#   1.Collects logcat till device shuts down
#   Args
#   Arg. 1
#   device_id - adb serial id of the the Device under test (DUT}
# ----------------------------------------------------------------------------------------------------------------------


def reboot_logs(device_id, shutdownflag):
    try:
        global rebootCount
        global deviceNotAvailableCount

        FNULL = open(os.devnull, "w")
        logTime = datetime.now()
        logTime = str(logTime)
        logTime = logTime.split("-")
        logTime = "_".join(logTime)
        logTime = logTime.split()
        logTime = "_".join(logTime)
        logTime = logTime.split(":")
        logTime = "_".join(logTime)
        logTime = logTime.split(".")
        logTime = "_".join(logTime)
        print logTime
        dirName = os.getcwd() + "/" + device_id + "/reboot logs"
        if not os.path.exists(dirName):
            os.makedirs(dirName)
        if shutdownflag:
            rebootCount += 1
            rebootLogcat = open(dirName + "/reboot_log_" + str(logTime) + ".out", 'wb')
            proc = subprocess.Popen(['adb', '-s', device_id, 'wait-for-device', 'logcat', '-v', 'time'],
                                    stdout=rebootLogcat)
            time.sleep(25)
            proc.kill()
            proc.wait()

            print "Done capturing Logcat"

            if waitForDevice(device_id):
                try:
                    sceenshotCmd = 'java -jar screenshot.jar -s ' + device_id + ' "' + dirName + '/Screenshot.png"'
                    print sceenshotCmd
                    temp = subprocess.call(sceenshotCmd, stdout=FNULL, stderr=subprocess.STDOUT)
                    print "Done capturing screenshot"
                except Exception, e:
                    print e
                logComm = 'adb -s ' + device_id + ' wait-for-device logcat -c'
                print logComm
                temp = subprocess.call(logComm, stdout=FNULL, stderr=subprocess.STDOUT)
                print "Done clearing logcat buffer"
        else:
            deviceNotAvailableCount += 1
            time.sleep(1)
            dirName = dirName+'/post_reboot_log_' + str(logTime)
            if not os.path.exists(dirName):
                os.makedirs(dirName)
            waitDeviceCmd = subprocess.Popen('adb -s ' + device_id + ' wait-for-device', shell=False,
                                             stdout=subprocess.PIPE)

            rebootLogcat = open(dirName + "/reboot_log_PostReboot.txt", "wb")
            rebootLogcat.write(subprocess.Popen('adb -s ' + device_id + ' wait-for-device logcat -d -v time',
                                                      shell=False, stdout=subprocess.PIPE).stdout.read())
            rebootLogcat.flush()
            rebootLogcat.close()
            print "Done capturing logcat"
            try:
                    sceenshotCmd = 'java -jar screenshot.jar -s ' + device_id + ' "' + dirName + '/Screenshot.png"'
                    print sceenshotCmd
                    temp = subprocess.call(sceenshotCmd, stdout=FNULL, stderr=subprocess.STDOUT)
                    print "Done capturing screenshot"
            except Exception, e:
                    print e
            time.sleep(1)
            bugReportFile = open(dirName + "/bugreport.txt", "wb")
            bugReportFile.write(subprocess.Popen('adb -s ' + device_id + ' wait-for-device bugreport', shell=False,
                                                     stdout=subprocess.PIPE).stdout.read())
            bugReportFile.flush()
            bugReportFile.close()
            print "Done capturing Bugreport"
    except Exception, e:
        print e

# ----------------------------------------------------------------------------------------------------------------------
#   capture_log
#
#   DESCRIPTION
#   1.Collects logcat and bugreports in unique folder
#   Args
#   Arg. 2
#   device_id - adb serial id of the the Device under test (DUT)
#   errorLine - the logcat line containing the keyword
# ----------------------------------------------------------------------------------------------------------------------


def capture_log(device_id, errorLine):
    try:
        global lastErrorLine
        lastErrorLine = errorLine
        FNULL = open(os.devnull, "w")
        logTime = datetime.now()
        logTime = str(logTime)
        logTime = logTime.split("-")
        logTime = "_".join(logTime)
        logTime = logTime.split()
        logTime = "_".join(logTime)
        logTime = logTime.split(":")
        logTime = "_".join(logTime)
        logTime = logTime.split(".")
        logTime = "_".join(logTime)
        print logTime
        if errorLine is not None:
            print "errorLine:" + errorLine
            dir1Name = device_id + "/" + logTime
            dirName = os.getcwd() + "/" + dir1Name

            if not os.path.exists(dirName):
                os.makedirs(dirName)
            statusFileDir = os.getcwd() + "/" + device_id
            if os.path.exists(dirName) and errorLine is not None:
                statusFile = open(statusFileDir + "/status.txt", "a")

                statusFile.write(dir1Name + "|" + errorLine)
                statusFile.flush()
                statusFile.close()

                try:
                    sceenshotCmd = 'java -jar screenshot.jar -s ' + device_id + ' "' + dirName + '/Screenshot.png"'
                    print sceenshotCmd
                    temp = subprocess.call(sceenshotCmd, stdout=FNULL, stderr=subprocess.STDOUT)
                    print "Done capturing screenshot"
                except Exception, e:
                    print e

                forceCloseFile = open(dirName + "/logcat.txt", "wb")

                forceCloseFile.write(subprocess.Popen('adb -s ' + device_id + ' wait-for-device logcat -d -v time',
                                                      shell=False, stdout=subprocess.PIPE).stdout.read())
                forceCloseFile.flush()
                forceCloseFile.close()
                print "Done capturing logcat"
                time.sleep(1)
                bugReportFile = open(dirName + "/bugreport.txt", "wb")
                bugReportFile.write(subprocess.Popen('adb -s ' + device_id + ' wait-for-device bugreport', shell=False, stdout=subprocess.PIPE).stdout.read().strip())
                bugReportFile.flush()
                bugReportFile.close()
                print "Done capturing Bugreport"
                time.sleep(5)
                logComm = 'adb -s ' + device_id + ' wait-for-device logcat -c'
                print logComm
                temp = subprocess.call(logComm, stdout=FNULL, stderr=subprocess.STDOUT)
                print "Done clearing logcat buffer"
    except Exception, e:
        print e

# ----------------------------------------------------------------------------------------------------------------------
#   htmlReport
#
#   DESCRIPTION
#   1. Creates HTML report with reboot count and crash logs links
#   Args
#   Arg. 3
#   device_id - adb serial id of the the Device under test (DUT}
#   productName - DUT model name [getprop ro.product.mode]
#   buildName - DUT build details [ro.build.fingerprint]
# ----------------------------------------------------------------------------------------------------------------------


def htmlReport(device_id, productName, buildName, startTime):
    global rebootCount
    global deviceNotAvailableCount
    if buildName is None or buildName == '':
        buildName = "Build name couldn't be fetched from DUT"
    if productName is not None or productName == '':
        devLog = open(productName + "_" + device_id + "_CrashRecords.html", "w")
    else:
        devLog = open(device_id + "_CrashRecords.html", "w")
        productName= "Product name couldn't be fetched from DUT"

    devLog.write("<body bgcolor='#B0C4DE'>")
    devLog.write("<font color='#300000'><h1><U>Crash Records</U></h1></font>")
    devLog.write("<h2><U>Product Name</U>: <font color='blue'>" + productName + "</h2></font>")
    devLog.write("<h2><U>Build Name</U>: <font color='blue'>" + buildName + "</h2></font>")
    devLog.write("<table border='1' cellpadding='10'>")
    devLog.write("<tr>")
    devLog.write("<th bgcolor='#300000' colspan='2' ><b><font color='#FFFFFF'>Start Time </b></th>")
    devLog.write("</tr>")
    devLog.write("<tr>")
    devLog.write("<th ><b>PC Time</b></th>")
    devLog.write("<th><b>" + startTime.split('|')[0] + "</b></th>")
    devLog.write("</tr>")
    devLog.write("<tr>")
    devLog.write("<th ><b>Device Time</b></th>")
    devLog.write("<th><b>" + startTime.split('|')[1] + "</b></th>")
    devLog.write("</tr>")
    devLog.write("</table>")
    devLog.write("<br>")
    devLog.write("<table border='1' cellpadding='10'>")
    devLog.write("<tr>")
    devLog.write("<th bgcolor='#300000'><b><font color='#FFFFFF'>Shutdown/Reboot Count</font></b></th>")
    devLog.write("<th><b>" + str(rebootCount) + "</b></th>")
    devLog.write("</tr>")
    devLog.write("<tr>")
    devLog.write("<th bgcolor='#300000'><b><font color='#FFFFFF'>Abrupt Reboot/Device Offline Count</font></b></th>")
    devLog.write("<th><b>" + str(deviceNotAvailableCount) + "</b></th>")
    devLog.write("</tr>")
    devLog.write("</table>")
    devLog.write("<br>")
    devLog.write("<table border='1' cellpadding='10'>")
    devLog.write("<tr>")
    devLog.write("<th bgcolor='#300000'><b><font color='#FFFFFF'>Crash Type</font></b></th>")
    devLog.write("<th bgcolor='#300000'><b><font color='#FFFFFF'>Log Location</font></b></th>")
    devLog.write("</tr>")
    statusFile = os.getcwd() + "/" + device_id + "/status.txt"
    if os.path.exists(statusFile):
        for line in open(statusFile):
            devLog.write("<tr>")
            crashLine = line.split('|')
            devLog.write("<td><b>" + crashLine[1] + "</b></td>")
            devLog.write("<td><b><a href=\"" + crashLine[0] + "\">log</a></b></td>")
            devLog.write("</tr>")
    else:
        devLog.write("<tr>")
        devLog.write("<td><b> No Crash found </b></td>")
        devLog.write("</tr>")
    devLog.write("</table>")
    devLog.flush()
    devLog.close()

# ----------------------------------------------------------------------------------------------------------------------
#   waitForDevice
#
#   DESCRIPTION
#   1. Checks if DUT is online/offline
#   Args
#   Arg. 1
#   device_id - adb serial id of the the Device under test (DUT)
# ----------------------------------------------------------------------------------------------------------------------


def waitForDevice(device_id):
    devices = subprocess.Popen('adb devices', shell=False, stdout=subprocess.PIPE)
    devices = str(devices.stdout.read())
    print devices
    if device_id in devices:
        return True
    else:
        return False


if __name__ == "__main__":
    try:
        if len(sys.argv) == 2:
            print sys.argv
            print len(sys.argv)
            if waitForDevice(sys.argv[1]):
                productName = subprocess.Popen('adb -s ' + sys.argv[1] + ' shell getprop ro.product.device', shell=False,
                                               stdout=subprocess.PIPE).stdout.read().rstrip()
                buildName = subprocess.Popen('adb -s ' + sys.argv[1] + ' shell getprop ro.build.display.id',
                                             shell=False,
                                             stdout=subprocess.PIPE).stdout.read().rstrip()
                logMonitor(sys.argv[1], productName, buildName)
            else:
                print "enter serial id of target device in dev_id.txt"

        elif os.path.exists("dev_id.txt"):
            f = open("dev_id.txt", 'r')
            dev_id = str(f.read()).split()[0]
            if waitForDevice(dev_id):
                productName = subprocess.Popen('adb -s ' + dev_id + ' shell getprop ro.product.device', shell=False,
                                               stdout=subprocess.PIPE).stdout.read().rstrip()
                buildName = subprocess.Popen('adb -s ' + dev_id + ' shell getprop ro.build.display.id', shell=False,
                                             stdout=subprocess.PIPE).stdout.read().rstrip()
                logMonitor(dev_id, productName, buildName)
            else:
                print "enter serial id of target device in dev_id.txt"

        else:
            print os.getcwd() + "/dev_id.txt"
            print os.path.exists(os.getcwd() + "/dev_id.txt")
            print "enter serial id of target device in dev_id.txt"
    except KeyboardInterrupt:
        print "Bye"
        sys.exit()
