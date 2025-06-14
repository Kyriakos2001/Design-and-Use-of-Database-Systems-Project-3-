import sys, os
sys.path.append(os.path.join(os.path.split(os.path.abspath(__file__))[0], 'lib'))
from bottle import route, run, static_file, request
import pymysql as db
import settings
import app

def renderTable(tuples):
    printResult = """<style type='text/css'> h1 {color:red;} h2 {color:blue;} p {color:green;} </style>
    <table border='1' frame='above'>"""
    header = '<tr><th>' + '</th><th>'.join([str(x) for x in tuples[0]]) + '</th></tr>'
    data = '<tr>' + '</tr><tr>'.join(['<td>' + '</td><td>'.join([str(y) for y in row]) + '</td>' for row in tuples[1:]]) + '</tr>'
    printResult += header + data + "</table>"
    return printResult

@route('/updateRank')
def updateRank():
    r1 = request.query.rank1 or "Unknown Rank"
    r2 = request.query.rank2 or "Unknown Rank"
    mtitle = request.query.movieTitle or "Unknown Title"
    table = app.updateRank(r1, r2, mtitle)
    return "<html><body>" + renderTable(table) + "</body></html>"

@route('/colleaguesOfColleagues')
def colleaguesOfColleagues():
    aid1 = request.query.actorId1
    aid2 = request.query.actorId2
    table = app.colleaguesOfColleagues(aid1, aid2)
    return "<html><body>" + renderTable(table) + "</body></html>"

@route('/actorPairs')
def actorPairs():
    aid = request.query.actorId
    table = app.actorPairs(aid)
    return "<html><body>" + renderTable(table) + "</body></html>"

@route('/selectTopNactors')
def selectTopNactors():
    n = request.query.n.strip()
    table = app.selectTopNactors(n)
    return "<html><body>" + renderTable(table) + "</body></html>"

@route('/traceActorInfluence')
def traceActorInfluence():
    aid = request.query.actorId
    table = app.traceActorInfluence(aid)
    return "<html><body>" + renderTable(table) + "</body></html>"

@route('/<path:path>')
def callback(path):
    return static_file(path, root='web')

@route('/')
def index():
    return static_file("index.html", root='web')

run(host='localhost', port=settings.web_port, reloader=True, debug=True)

import os

@route('/<path:path>')
def callback(path):
    abs_path = os.path.join('web', path)
    print(f"Serving file from: {abs_path}")
    return static_file(path, root='web')

@route('/')
def index():
    print("Serving index.html")
    return static_file("index.html", root='web')