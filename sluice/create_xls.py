#!/usr/bin/python
# coding: utf-8

import xlwt

LOG_FILENAME = "../log/clear_files.log"

if __name__ == '__main__':
    log_file = open(LOG_FILENAME, 'r')
    # log_file.readlines()
    lines = 0
    wb = xlwt.Workbook()
    sheet = 0
    ws = wb.add_sheet('Log Sheet ' + str(sheet))

    for line in log_file:
        cells = 0
        for cell in line.split('|'):
            ws.write(lines, cells, cell)
            cells = cells + 1
        lines = lines + 1
        if lines == 60000:
            sheet = sheet +1
            ws = wb.add_sheet('Log Sheet ' + str(sheet))
            lines = 0

    wb.save('log.xls')