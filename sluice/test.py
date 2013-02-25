#!/usr/bin/python
# coding: utf-8

import os
import unittest
import string
import time
import shutil
import _mysql
import json
from string import letters
from random import randint, choice
from datetime import datetime, timedelta
from MySQLdb.constants import FIELD_TYPE

import clear_files

LOG_FILENAME = "../log/test_clear_files.log"
LOG_DIR = os.path.dirname(LOG_FILENAME)
FILE_DIR = 'test_files'
MYSQL_DB = "sms16_test_test"
MYSQL_USER = "user"
MYSQL_PWD = "password"


class TestClearFiles(unittest.TestCase):
    file_list = {}

    def create_time(self):
        """
        Возвращает unix timestamp для случайного дня из 150 в прошлое от текущего
        """
        create = datetime.now() - timedelta(days=randint(1, 150))
        return time.mktime(create.timetuple())

    def setUp(self):
        """
        Подготовка данных для тестов
        """

        def rand_param():
            """
            Возвращает случайный параметр(срок хранения файла) для пользователя
            """
            return _mysql.escape_string(json.dumps({'store_files': randint(0, 120)}))

        def gen(length=6):
            """
            Возвращает случайную строку
            :param length: Длинна строки
            :return: Строка
            """
            chars = letters
            return ''.join(choice(chars) for _ in range(length))

        clear_files.prepare_log_file(LOG_FILENAME)
        os.mkdir(FILE_DIR)

        for file_id in range(1, 20):
            file_name = os.path.join(FILE_DIR, str(file_id) + '.txt')
            f = open(file_name, 'w')
            f.close()
            self.file_list[file_id] = file_name

        self.db = _mysql.connect(user=MYSQL_USER, passwd=MYSQL_PWD, db=MYSQL_DB, conv={FIELD_TYPE.LONG: int})
        self.db.query(""" CREATE TABLE IF NOT EXISTS `users` (
                    `id_user` int(11) unsigned NOT NULL AUTO_INCREMENT,
                    `login` varchar(255) NOT NULL DEFAULT '',
                    `pass` varchar(255) NOT NULL DEFAULT '',
                    `params` text COMMENT 'Дополнительные параметры в виде json документа',
                    PRIMARY KEY (`id_user`)
                    ) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=0;""")

        self.db.query("""CREATE TABLE IF NOT EXISTS `user_files` (
                    `id_file` int(11) unsigned NOT NULL AUTO_INCREMENT,
                    `id_user` int(11) unsigned NOT NULL DEFAULT '0',
                    `time_creations` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    `params` text COMMENT 'Дополнительные параметры файла в виде json документа',
                    PRIMARY KEY (`id_file`)
                    ) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=0;""")

        self.db.query("""INSERT INTO `users` (`login`,`pass`,`params`)
                        VALUES ("%s","%s","%s")""" % (gen(), gen(), rand_param()))

        for i in range(1, 21):
            self.db.query("""INSERT INTO `user_files` (`id_user`,`time_creations`,`params`)
                            VALUES (%d,FROM_UNIXTIME(%d),"%s")""" % (1, self.create_time(), rand_param()))

    def doCleanups(self):
        """
        Очистка после тестов
        """
        shutil.rmtree(FILE_DIR)
        self.db.query(""" DROP TABLE `user_files` """)
        self.db.query(""" DROP TABLE `users` """)

    def test_log(self):
        """
        Тестируем создание лога и его формат
        """
        clear_files.log(operation="test", user_login="test", user_id="2",
                        file_name="test.file", comment="test")

        test_file = open(LOG_FILENAME, 'r')
        lines = test_file.readlines()
        line = lines[-1]
        test_file.close()
        self.assertEqual(string.split(line, "|")[1:], ["test", "test", "2", "test.file", "test\n"])
        os.remove(LOG_FILENAME)

    def test_check_file(self):
        """
        Тестируем проверку файлов на необходимость удаления
        """
        create_time = time.mktime((datetime.now() - timedelta(days=15)).timetuple())
        self.assertEqual(clear_files.check_file((1, create_time, 'User', '{"store_files": 10}', 1)), True)
        self.assertEqual(clear_files.check_file((2, create_time, 'User', '{"store_files": 20}', 1)), False)
        self.assertEqual(clear_files.check_file((3, create_time, 'User', '{"store_files": 0}', 1)), False)
        self.assertEqual(clear_files.check_file((4, create_time, 'User', '', 1)), False)

    def test_file_list(self):
        """
        Тестируем создание списка файлов в папке
        """
        file_list = clear_files.prepare_file_list(FILE_DIR)
        self.assertEqual(file_list, self.file_list)

    def test_get_files(self):
        """
        Проверяем правильность выборки файлов из БД
        """
        files = clear_files.get_files(self.db)
        self.assertEqual(len(files), 99)

    def test_delete_files(self):
        """
        Проверка удаления файла из ФС и БД
        """
        clear_files.remove_file((1, self.create_time, 'User', '{"store_files": 10}', 1), self.db, self.file_list)
        self.assertEqual(os.path.exists(self.file_list[1]), False)
        self.db.query("""SELECT * FROM `user_files` WHERE `id_file`=1 """)
        result = self.db.store_result()
        self.assertEqual(result.fetch_row(0), tuple())

if __name__ == '__main__':
    unittest.main()