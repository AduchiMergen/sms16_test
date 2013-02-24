#!/usr/bin/python
# coding: utf-8

import os
import unittest
import string
import time
from datetime import datetime, timedelta

import clear_files

LOG_FILENAME = "../log/test_clear_files.log"
LOG_DIR = os.path.dirname(LOG_FILENAME)


class TestClearFiles(unittest.TestCase):

    def test_log(self):
        clear_files.prepare_log_file(LOG_FILENAME)
        clear_files.log(operation="test", user_login="test", user_id="2",
                        file_name="test.file", comment="test")

        test_file = open(LOG_FILENAME, 'r')
        lines = test_file.readlines()
        line = lines[0]
        test_file.close()
        self.assertEqual(string.split(line, "|")[1:], ["test", "test", "2", "test.file", "test\n"])

    def test_check_file(self):
        create_time = time.mktime((datetime.now() - timedelta(days=15)).timetuple())
        self.assertEqual(clear_files.check_file((1, create_time, 'User', '{"store_files": 10}', 1)), True)
        self.assertEqual(clear_files.check_file((2, create_time, 'User', '{"store_files": 20}', 1)), False)
        self.assertEqual(clear_files.check_file((3, create_time, 'User', '{"store_files": 0}', 1)), False)
        self.assertEqual(clear_files.check_file((4, create_time, 'User', '', 1)), False)

if __name__ == '__main__':
    unittest.main()