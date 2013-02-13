#!/usr/bin/python
# coding: utf-8

from datetime import datetime,timedelta
import _mysql
import json
import time
import os
import glob
import shutil
from subprocess import call

from MySQLdb.constants import FIELD_TYPE

LOG_DIR = "../log"
LOG_FILENAME = os.path.join(LOG_DIR,"clear_files.log")
MYSQL_DB = "sms16_test"
MYSQL_USER = "user"
MYSQL_PWD = "password"

FILE_DIR = "../user_files"

def log(operation,user_login="",user_id="",file_name="",comment=""):
    global log_file    
    log_file.write("|".join((datetime.now().isoformat(),operation,user_login,str(user_id),str(file_name),comment)))
    log_file.write("\n")
    log_file.flush()

def get_files(db):
    try:
        db.query("""SELECT 
                    `user_files`.`id_file`,
                    UNIX_TIMESTAMP(`user_files`.`time_creations`),
                    `users`.`login`,
                    `users`.`params`,
                    `users`.`id_user` 
                FROM `user_files` 
                JOIN `users` 
                ON `users`.`id_user`=`user_files`.`id_user` """);
        result = db.store_result()
        return result.fetch_row(0)
    except:
        log(operation="error",comment="DB query error")
        return list();

def check_file(file_data):
    try:
        store_files = int(json.loads(file_data[3]).get("store_files",90))
    except ValueError:
        store_files = 90
    if store_files == 0:
        store_files = 90
    time_border=datetime.now()-timedelta(days=store_files)
    return int(file_data[1])<time.mktime(time_border.timetuple())

def prepare_filelist():
    file_list={}
    for root, dirs, files in os.walk(FILE_DIR):
        for name in files:
            file_list[int(os.path.splitext(name)[0])]=os.path.join(root,name)
    return file_list

def remove_file(file,db,file_list):
    if file[0] in file_list:
        filename = file_list[file[0]]
    else:
        log(operation="warning",user_login=file[2],user_id=file[4],file_name=file[0],comment="File not found")
        return
    os.unlink(filename)
    log(operation="delete file",user_login=file[2],user_id=file[4],file_name=filename)
    db.query("""DELETE FROM `user_files` WHERE `id_file`= %d""" % file[0])
    log(operation="delete record",user_login=file[2],user_id=file[4],file_name=filename)

if __name__ == '__main__':
    if not os.path.exists(LOG_DIR):
        os.mkdir(LOG_DIR)
    log_file = open(LOG_FILENAME, 'a+')
    log(operation="start")
    if os.path.exists(FILE_DIR):
        try:
            db=_mysql.connect(user=MYSQL_USER, passwd=MYSQL_PWD, db=MYSQL_DB, conv = { FIELD_TYPE.LONG: int })
        except:
            log(operation="error",comment="DB connection error")
        file_list = prepare_filelist()
        for file in filter(check_file,get_files(db)):
            remove_file(file,db,file_list)
        db.close()
    else:
        log(operation="error",comment="Dir with user files not found")
    log(operation="stop")
    log_file.close()
