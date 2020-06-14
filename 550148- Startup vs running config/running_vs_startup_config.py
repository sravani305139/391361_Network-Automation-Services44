print("Content-Type: text/html\n")

import cgi
import cgitb; cgitb.enable()
import time
import paramiko
from difflib import Differ
import logging
import random
import string
import bot_govern
import sqlite3
from datetime import datetime
from folders import *

# bot govern parameters
job_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)) + "-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) + "-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) + "-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) + "-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
use_case_name = "running_vs_startup_config.py"
target_count = "1"
status = "" # pick from try-exception block
start_time = ('{:%Y.%m.%d-%H.%M.%S}'.format(datetime.now()))

# main script
stamp=('{:%Y.%m.%d-%H.%M.%S}'.format(datetime.now()))

def startup_vs_running_config(Device_IP,Login_ID,Password):

    Startup_Log_File = startup_files_path + 'startup_' + Device_IP + '_' + stamp + ".log"  # log file

    Running_Log_File = running_files_path + 'running_' + Device_IP + '_' + stamp + ".log"  # log file

    fs = open(Startup_Log_File, 'w')  # write output in log file
    fr = open(Running_Log_File, 'w')  # write output in log file

    try:
        global channel

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(Device_IP, username=Login_ID, password=Password)

        channel = ssh.invoke_shell()
        time.sleep(5)

        channel.send('\n')
        time.sleep(1)

        output = channel.recv(999999)

        channel.send('terminal length 0\r\n')
        time.sleep(1)

        buffer_output = channel.recv(999999).decode("utf-8")

        channel.send("show startup-config\r\r")
        time.sleep(5)

        output = channel.recv(999999).decode("utf-8")
        output_list=output.split("\n")
        for line in output_list: fs.write(line.strip()+'\n')

        channel.send("show running-config\r\r")
        time.sleep(5)

        output = channel.recv(999999).decode("utf-8")
        output_list = output.split("\n")
        for line in output_list: fr.write(line.strip() + '\n')

        fs.close()
        fr.close()
        ssh.close()

    except Exception as e:
        print(str(e))

    return Startup_Log_File, Running_Log_File

try:

    logging.basicConfig(filename=datetime.now().strftime('../Logs/ProcessLogs/Processlog-running_vs_startup_config.log'),
                        level=logging.DEBUG)  # for storing process log
    
    logging.info("Script ran at " + stamp)
    
    form = cgi.FieldStorage()

    # get values from form
    Device_IP = form.getvalue("deviceIP")
    Login_ID = form.getvalue("loginID")
    Password = form.getvalue("password")

    # get the files to compare and display result
    startup_config_file, running_config_file = startup_vs_running_config(Device_IP,Login_ID,Password)

    d = Differ()

    startup_config_file_open = open(startup_config_file,"r")
    running_config_file_open = open(running_config_file,"r")

    list1 = []
    list2 = []

    diff = list(d.compare(startup_config_file_open.readlines(), running_config_file_open.readlines()))

    # segregate output
    for line in diff:
        if line.startswith('+ '):
            list1.append(line[:-1])
        if line.startswith('- '):
            list2.append(line[:-1])

    extra_lines = 0

    if len(list1) > len(list2):
        extra_lines = len(list1) - len(list2)

        for i in range(0, extra_lines):
            list2.append(" ")
    else:
        extra_lines = len(list2) - len(list1)

        for i in range(0, extra_lines):
            list1.append(" ")

    # print the result of diff in a table
    print("<html><body><center><table border='2'>")
    print("<style>table {font-family: arial, sans-serif;border-collapse: collapse;width: 100%;}td, th {border: 1px solid #dddddd;text-align: left;padding: 8px;}tr:nth-child(even) {background-color: #dddddd;}</style>")
    print("<tr><td>Command has been added since last save</td><td>Command was present in the last save, and has been deleted</td></tr>")
    for i in range(0, len(list1)):
        print("<tr><td style='width:50%'>" + list1[i] + "</td><td style='width:50%'>" + list2[i] + "</td></tr>")

    print("</table></body></html><br>")


    status = "Completed"

except Exception as e:
    log_file = "../Logs/ErrorLogs/running_vs_startup_config-" + stamp + ".log"
    fl = open(log_file, "w")
    fl.write(str(e))
    fl.close()
    
    status = "Failed"
    print(str(e))

# pushing data into table for bot govern
end_time = ('{:%Y.%m.%d-%H.%M.%S}'.format(datetime.now()))

# connect to db
conn=sqlite3.connect(db_path)
cursor=conn.cursor()

cursor.execute("insert into BG_Data (JOBID,UseCase_Name,Target_Count,Status,Start_Time,End_Time) VALUES (?,?,?,?,?,?)" , (job_id,use_case_name,target_count,status,start_time,end_time))

cursor.close()

# save changes
conn.commit()

# close connection
conn.close()

bot_govern.update_db(job_id,use_case_name) # update configurable details