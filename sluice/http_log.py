#!/usr/bin/python
#coding: utf-8

from os import path
from mod_python import apache,util

PROJECT_PATH = path.dirname(path.abspath(__file__))
LOG_FILENAME = path.join(PROJECT_PATH,"../log/clear_files.log")

def handler(req):

    form = util.FieldStorage(req, keep_blank_values=1)
    offset = form.getfirst("offset")
    limit = form.getfirst("limit")

    end = False

    if limit:
        try:
            limit=int(limit.value) 
        except:
            limit=30
    else:
        limit=30

    if offset:
       if offset.value == "end":
           end=True
           offset=-limit
       else:
           try:
                offset=int(offset.value)
           except:
                offset=0
    else:
       offset=0

    log = open(LOG_FILENAME,"r")

    start = offset
    stop = offset+limit
    if (stop<start):
       start,stop = stop,start
    stop = stop if stop<>0 else None
    start = start if start<>0 else None
    lines = log.readlines()[start:stop]

    req.content_type = "text/html"

    req.write("""<!DOCTYPE HTML>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
    <link href="css/bootstrap.css" rel="stylesheet">
  </head>
  <body>
<div class="container" style="max-width: 900px;">
""")
    req.write("<p>start: %d, stop: %d</p>" % (start if start else 0,stop if stop else 0))

    req.write("<a href=\"?limit=%d&offset=%d\" class=\"btn btn-link\">Вперед</a>" % (limit,offset+limit))    
    req.write("<a href=\"?limit=%d&offset=%d\" class=\"btn btn-link\">Назад</a>" % (limit,offset-limit))
    req.write("<a href=\"?limit=%d&offset=%d\" class=\"btn btn-link\">В начало</a>" % (limit,0))
    req.write("<a href=\"?limit=%d&offset=%s\" class=\"btn btn-link\">В конец</a>" % (limit,"end"))

    req.write("<br>")

    offset = "end" if end else offset

    req.write("<a href=\"?limit=%d&offset=%s\" class=\"btn btn-link\">30</a>" % (30,offset))
    req.write("<a href=\"?limit=%d&offset=%s\" class=\"btn btn-link\">50</a>" % (50,offset))
    req.write("<a href=\"?limit=%d&offset=%s\" class=\"btn btn-link\">100</a>" % (100,offset))
    req.write("<a href=\"?limit=%d&offset=%s\" class=\"btn btn-link\">150</a>" % (150,offset))


    req.write("<table class=\"table table-condensed table-striped\"><thead><tr><th>full time</th><th>operation</th><th>user login</th><th>user id</th><th>file name</th><th>comment</th></tr></thead><tbody>")

    for line in lines:
        req.write("<tr><td>%s</td></tr>" % "</td><td>".join(line.split("|")))

    req.write("</tbody></table>")

    req.write("</div></body></html>")

    return apache.OK
