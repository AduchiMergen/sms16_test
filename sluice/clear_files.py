#!/usr/bin/python
# coding: utf-8

from datetime import datetime, timedelta
import _mysql
import json
import time
import os
import logging

from MySQLdb.constants import FIELD_TYPE

LOG_FILENAME = "../log/clear_files.log"
FILE_DIR = "../user_files"
MYSQL_DB = "sms16_test"
MYSQL_USER = "user"
MYSQL_PWD = "password"


def prepare_log_file(file_name):
    if not os.path.exists(os.path.dirname(file_name)):
        os.mkdir(os.path.dirname(file_name))
    logging.basicConfig(filename=file_name, filemode="a+", level=logging.INFO, format='%(message)s')


def log(operation, user_login="", user_id="", file_name="", comment=""):
    """
    Функция довавляет в лог строку в соответствии с форматом:
        full time | operation | user login | user id | file name | comment

    Keyword arguments:
    :global log_file: Файловый дескриптор лога
    :param operation: действие выполняемое системой:
            start (скрипт начал работу),
            stop (скрипт завершил работу),
            delete file, delete record (удаление записи в базе),
            error (указание на фатальную ошибку),
            warring (уведомление о некорректной работе системы. не вызывающее
                фатального сбоя)
    :param user_login: Логин пользователя
    :param user_id: Идентификатор пользователя
    :param file_name: Имя файла для удаления
    :param comment: текстовый комментарий работы системы, в котом пишется
            описание действия. в том числе описание ошибки или уведомления.
            длина не более 255 символов. язык английский
    """
    logging.info("|".join((datetime.now().isoformat(), operation, user_login, str(user_id), str(file_name), comment)))


def get_files(db):
    """
    Получение информации о файлах из базы данных
    :param db: Дескриптор базы данных
    :return list: Возвращает список с информацией о всех файлах в базе данных вида:
        (id_file, time_creations, user_login, user_params, user_id)
    """
    try:
        db.query("""SELECT 
                    `user_files`.`id_file`,
                    UNIX_TIMESTAMP(`user_files`.`time_creations`),
                    `users`.`login`,
                    `users`.`params`,
                    `users`.`id_user` 
                FROM `user_files` 
                JOIN `users` 
                ON `users`.`id_user`=`user_files`.`id_user` """)
        result = db.store_result()
        return result.fetch_row(0)
    except _mysql.DatabaseError:
        log(operation="error", comment="DB query error")
        return list()


def check_file(file_data):
    """
    Функция проверяет необходимо ли удаление файла
    :param file_data: информация о файле в виде:
        (id_file, time_creations, user_login, user_params, user_id)
    :return bool: Возвращает логическое значение, необходимо ли удалять файл
    """
    try:
        store_files = int(json.loads(file_data[3]).get("store_files", 90))
    except ValueError:
        store_files = 90
    if store_files == 0:
        store_files = 90
    time_border = datetime.now() - timedelta(days=store_files)
    return int(file_data[1]) < time.mktime(time_border.timetuple())


def prepare_file_list(file_dir):
    """
    Подготавливает список файлов в директории для пользовательских файлов.
    Для быстрого поиска полного имени файла по идентификатору.

    :return dict: Возвращает словарь, идентификатор файла в качестве ключа
        и полного имени файла в качестве значения
    """
    file_list = {}
    for root, dirs, files in os.walk(file_dir):
        for name in files:
            file_list[int(os.path.splitext(name)[0])] = os.path.join(root, name)
    return file_list


def remove_file(file_tuple, db, file_list):
    """
    Удаляет файл и запись о файле из БД.
    :param file_tuple: Информация из БД о файле
    :param db: Дескриптор базы данных
    :param file_list: Список файлов в директории для пользовательских файлов
    """
    if file_tuple[0] in file_list:
        filename = file_list[file_tuple[0]]
        os.unlink(filename)
        log(operation="delete file", user_login=file_tuple[2], user_id=file_tuple[4],
            file_name=filename)
        try:
            db.query("""DELETE FROM `user_files` WHERE `id_file`= %d""" % file_tuple[0])
            log(operation="delete record", user_login=file_tuple[2], user_id=file_tuple[4],
                file_name=filename)
        except _mysql.DatabaseError:
            log(operation="warning", user_login=file_tuple[2], user_id=file_tuple[4],
                file_name=file_tuple[0], comment="Error remove file data from DB")
    else:
        log(operation="warning", user_login=file_tuple[2], user_id=file_tuple[4], file_name=file_tuple[0],
            comment="File not found")


if __name__ == '__main__':
    # Подготавливаем папку и файл для лога
    prepare_log_file(LOG_FILENAME)
    log(operation="start")
    # Если каталог для файлов пользователя существует подключаемся к базе данных
    if os.path.exists(FILE_DIR):
        try:
            db = _mysql.connect(user=MYSQL_USER, passwd=MYSQL_PWD, db=MYSQL_DB, conv={FIELD_TYPE.LONG: int})
            # Подготавливаем список файлов каталоге для быстрого поиска по идентификатору
            file_list = prepare_file_list(FILE_DIR)
            # Фильтруем список файлов из дб и обходим его для удаления каждого файла
            for file_tuple in filter(check_file, get_files(db)):
                remove_file(file_tuple, db, file_list)
            db.close()
        except _mysql.DatabaseError:
            log(operation="error", comment="DB connection error")
    else:
        log(operation="error", comment="Dir with user files not found")
    log(operation="stop")

















