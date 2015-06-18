# -*- coding: utf-8 -*-

import os, glob, sys, json
workdir = os.path.dirname(__file__)
from flask import Flask
from flaskext.genshi import Genshi, render_template
from genshi.template import MarkupTemplate 
from genshi.template import TemplateLoader
from genshi import Stream  
from genshi.input import XML
from genshi.core import QName
import os.path
import logging
import config
import datetime, dateutil.parser
import pytz
        
app = Flask(__name__)
genshi = Genshi(app)

def update_index():
  index_file = os.path.join(config.archive_dir, 'archiveindex.json')
  idx = {
    'last_seen': '0',
    'tweets': {},
  }
  try:
    with open(index_file, 'r') as fp:
      idx = json.load(fp)
  except:
    pass
  archive_dirs = sorted([ f for f in glob.glob(os.path.join(config.archive_dir, '*')) if os.path.isdir(f) and os.path.basename(f) >= idx['last_seen'] ])
  print archive_dirs
  for dir in archive_dirs:
    for jsonfile in sorted(glob.glob(os.path.join(dir, '*.json'))):
      with open(jsonfile) as f:
        tweet = json.load(f)
        if tweet.has_key('entities') and tweet['entities'].has_key('media') and True in [ m.has_key('type') and m['type'] == 'photo' for m in tweet['entities']['media'] ]:
          (year, kw, day) = [ str(x) for x in dateutil.parser.parse(tweet['created_at']).astimezone(pytz.timezone('Europe/Berlin')).isocalendar() ]
          if not idx['tweets'].has_key(year):
            idx['tweets'][year] = {}
          if not idx['tweets'][year].has_key(kw):
            idx['tweets'][year][kw] = []
          if not tweet['id_str'] in idx['tweets'][year][kw]:
            idx['tweets'][year][kw].append(tweet['id_str'])
  idx['last_seen'] = os.path.basename(archive_dirs[-1])
  with open(index_file + '.new', 'w') as fp:
    json.dump(idx, fp) 
  if os.path.isfile(index_file + '.new'):
    os.rename(index_file + '.new', index_file)
  return idx

@app.route('/')
@app.route('/<year>/<kw>')
def index(year=None, kw=None):
  tweetids = []
  idx = {}
  if year is None:
    (year, kw, day) = [ str(x) for x in datetime.datetime.now().isocalendar() ]
  try:
    idx = update_index()
    tweetids = idx['tweets'][year][kw]
  except Exception as e:
    print e
  return render_template(
    'index.html', 
    { 'year':year, 
      'kw':kw,
      'title': config.track,
      'navigation': [ [ (y, k) for k in idx['tweets'][y].keys() ] for y in idx['tweets'].keys() ], 
      'tweetids': json.dumps(tweetids),
    });

if __name__ == '__main__':
  app.run(host='0.0.0.0', debug=True)
