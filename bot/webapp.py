import os
import json

import flask
from flask import Flask, request

from . import db, PACKAGEDIR

goldstarsapp = Flask('goldstarsapp',
                     static_folder=os.path.join(PACKAGEDIR, 'static'),
                     static_url_path='',
                     template_folder=os.path.join(PACKAGEDIR, 'templates'))

@goldstarsapp.route('/')
def root():
    return goldstarsapp.send_static_file('index.html')


@goldstarsapp.route('/stars')
def stars():
    mydb = db.GoldStarDB()
    cur = mydb.con.execute('SELECT recipient_handle, COUNT(*) AS stars '
                           'FROM transactions GROUP BY recipient_handle '
                           'ORDER BY stars DESC')
    stars = cur.fetchall()
    return flask.render_template('stars.html', stars=stars)


#@goldstarsapp.route('/report/<screen_name>')
@goldstarsapp.route('/report', methods=['GET'])
def report():
    name = request.args.get('name')
    if name[0] == '@':
        name = name[1:]
    mydb = db.GoldStarDB()
    cur = mydb.con.execute('SELECT tweet, donor_id AS stars '
                           'FROM transactions '
                           'WHERE lower(recipient_handle) = lower(?) '
                           'ORDER BY time DESC', [name])
    rows = cur.fetchall()
    tweets = [json.loads(r[0]) for r in rows]
    unique_donors = len(set([r[1] for r in rows]))
    return flask.render_template('report.html', tweets=tweets, name=name, unique_donors=unique_donors)
