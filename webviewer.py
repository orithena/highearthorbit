# -*- coding: utf-8 -*-

import os, glob, sys, json
workdir = os.curdir
try: 
  workdir = os.path.dirname(__file__)
except: pass
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
import re
        
app = Flask(__name__)
genshi = Genshi(app)

def flatten(lst):
  for elem in lst:
    if type(elem) in (list,):
      for i in flatten(elem):
        yield i
    else:
      yield elem


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
  archive_dirs = sorted([ f for f in glob.glob(os.path.join(config.archive_dir, '[0-9]*')) if os.path.isdir(f) and os.path.basename(f) >= idx['last_seen'] ])
  for dir in archive_dirs:
    for jsonfile in sorted(glob.glob(os.path.join(dir, '*.json'))):
      with open(jsonfile) as f:
        tweet = json.load(f)
        if (not config.show_only_photos_in_archive) or (tweet.has_key('entities') and tweet['entities'].has_key('media') and True in [ m.has_key('type') and m['type'] == 'photo' for m in tweet['entities']['media'] ]):
          if not any(word in tweet['text'].lower() for word in config.spamfilter_word_blacklist):	# Blacklisted words?
            tweettime = dateutil.parser.parse(tweet['created_at']).astimezone(pytz.timezone('Europe/Berlin'))
            if config.paginate_by_day:
              year = str(tweettime.year)
              month = "%02d" % tweettime.month
              day = "%02d" % tweettime.day
              if not idx['tweets'].has_key(year):
                idx['tweets'][year] = {}
              if not idx['tweets'][year].has_key(month):
                idx['tweets'][year][month] = {}
              if not idx['tweets'][year][month].has_key(day):
                idx['tweets'][year][month][day] = []
              if not tweet['id_str'] in idx['tweets'][year][month][day]:
                idx['tweets'][year][month][day].append(tweet['id_str'])
            else:
              (year, kw, day) = [ str(x) for x in tweettime.isocalendar() ]
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

def insensitive(pattern):
  def either(c):
    return '[%s%s]'%(c.lower(),c.upper()) if c.isalpha() else c
  return ''.join(map(either,pattern))

def update_user_index(screenname):
  user_archive_dir = os.path.join(config.archive_dir, 'users')
  try: 
    os.makedirs(user_archive_dir)
  except: pass
  index_file = os.path.join(user_archive_dir, '%s.json' % screenname)
  idx = {
    'last_seen': '0',
    'tweets': [],
  }
  try:
    with open(index_file, 'r') as fp:
      idx = json.load(fp)
  except:
    pass
  archive_dirs = sorted([ f for f in glob.glob(os.path.join(config.archive_dir, '[0-9]*')) if os.path.isdir(f) and os.path.basename(f) >= idx['last_seen'] ])
  for dir in archive_dirs:
    for jsonfile in sorted(glob.glob(os.path.join(dir, '*-'+insensitive(screenname)+'.json'))):
      with open(jsonfile) as f:
        tweet = json.load(f)
        if (not config.show_only_photos_in_archive) or (tweet.has_key('entities') and tweet['entities'].has_key('media') and True in [ m.has_key('type') and m['type'] == 'photo' for m in tweet['entities']['media'] ]):
          if tweet['user']['screen_name'].lower() == screenname or (tweet.has_key('retweeted_status') and tweet['retweeted_status']['user']['screen_name'].lower() == screenname):
            if not any(word in tweet['text'].lower() for word in config.spamfilter_word_blacklist):	# Blacklisted words?
              if not tweet['id_str'] in idx['tweets']:
                idx['tweets'].append(tweet['id_str'])
  if len(idx['tweets']) > 0:
    idx['last_seen'] = os.path.basename(archive_dirs[-1])
    with open(index_file + '.new', 'w') as fp:
      json.dump(idx, fp) 
    if os.path.isfile(index_file + '.new'):
      os.rename(index_file + '.new', index_file)
  return idx

def update_user_tweetindex(screenname):
  user_archive_dir = os.path.join(config.archive_dir, 'users')
  try: 
    os.makedirs(user_archive_dir)
  except: pass
  index_file = os.path.join(user_archive_dir, '%s.full.json' % screenname)
  idx = {
    'last_seen': '0',
    'tweets': [],
  }
  try:
    with open(index_file, 'r') as fp:
      idx = json.load(fp)
  except:
    pass
  archive_dirs = sorted([ f for f in glob.glob(os.path.join(config.archive_dir, '[0-9]*')) if os.path.isdir(f) and os.path.basename(f) >= idx['last_seen'] ])
  for dir in archive_dirs:
    for jsonfile in sorted(glob.glob(os.path.join(dir, '*-'+insensitive(screenname)+'.json'))):
      with open(jsonfile) as f:
        tweet = json.load(f)
        if tweet.has_key('entities') and tweet['entities'].has_key('media') and True in [ m.has_key('type') and m['type'] == 'photo' for m in tweet['entities']['media'] ]:
          if tweet['user']['screen_name'].lower() == screenname or (tweet.has_key('retweeted_status') and tweet['retweeted_status']['user']['screen_name'].lower() == screenname):
            if not tweet['id_str'] in idx['tweets']: 
              idx['tweets'].append(tweet)
  if len(idx['tweets']) > 0:
    idx['last_seen'] = os.path.basename(archive_dirs[-1])
    with open(index_file + '.new', 'w') as fp:
      json.dump(idx, fp) 
    if os.path.isfile(index_file + '.new'):
      os.rename(index_file + '.new', index_file)
  return idx

@app.route('/user/<screenname>')
def user(screenname):
  screenname = re.sub(r'[^a-z0-9_]+', '', screenname.lower())
  idx = update_user_index(screenname)
  return render_template(
    'index.html', 
    { 
      'screenname': screenname,
      'title': config.track,
      'tweetids': json.dumps(sorted(idx['tweets'], reverse=False)),
    });

@app.route('/collage/<screenname>')
def collage(screenname):
  screenname = re.sub(r'[^a-z0-9_]+', '', screenname.lower())
  idx = update_user_tweetindex(screenname)
  return render_template(
    'collage.html', 
    { 
      'screenname': screenname,
      'title': config.track,
      'tweetids': json.dumps(sorted(idx['tweets'])),
    });
  

@app.route('/')
@app.route('/<year>/<kw>')
def index(year=None, kw=None):
  if config.paginate_by_day:
    return index_days()
  tweetids = []
  idx = {}
  try:
    year = str(int(year))
    kw = str(int(kw))
  except:
    year = None
    kw = None
  if year is None:
    (year, kw, day) = [ str(x) for x in datetime.datetime.now().isocalendar() ]
  try:
    idx = update_index()
    tweetids = list(idx['tweets'][year][kw])
  except Exception as e:
    print e
  return render_template(
    'index.html', 
    { 'year':year, 
      'kw':kw,
      'title': config.track,
      'navigation': sorted(*[ [ (y, k) for k in idx['tweets'][y].keys() ] for y in idx['tweets'].keys() ], key=lambda x: int(x[1])),
      'tweetids': json.dumps(tweetids),
    });

@app.route('/<year>/<month>/<day>')
def index_days(year=None, month=None, day=None):
  tweetids = []
  idx = {}
  try:
    year = str(int(year))
    month = "%02d" % int(month)
    day = "%02d" % int(day)
  except:
    year = None
    month = None
    day = None
  if year is None:
    now = datetime.datetime.now()
    year = str(now.year)
    month = "%02d" % now.month
    day = "%02d" % now.day
  try:
    idx = update_index()
    tweetids = list(idx['tweets'][year][month][day])
  except Exception as e:
    print e
  return render_template(
    'index.html', 
    { 'year':year, 
      'month': month,
      'day': day,
      'title': config.track,
      'navigation': sorted(flatten([ [ [ (y, m, d) for d in idx['tweets'][y][m].keys() ] for m in idx['tweets'][y].keys() ] for y in idx['tweets'].keys() ])),
      'tweetids': json.dumps(tweetids),
    });

if __name__ == '__main__':
  app.run(host='0.0.0.0', debug=True)
