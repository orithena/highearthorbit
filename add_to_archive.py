#!/usr/bin/python

import twython, time, pprint, traceback, os, sys
import config
from twython import TwythonStreamer, TwythonError, TwythonRateLimitError
import urllib, json, glob
import thread
queuelock = thread.allocate_lock()
import logging
logging.basicConfig(stream=sys.stdout, format='%(levelname)s %(message)s')
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


lasttry=0
rts = []
_queue = []
_fail = {}
_done = {}
friends = []
listmembers = []
blocked = []
twitter = None
user_screenname = ''

def insensitive(pattern):
  def either(c):
    return '[%s%s]'%(c.lower(),c.upper()) if c.isalpha() else c
  return ''.join(map(either,pattern))

def save(data):
    user = data['retweeted_status']['user'] if 'retweeted_status' in data else data['user']
    basedirname = os.path.join(config.archive_dir, data['id_str'][:-15].zfill(6))
    basefilename = '-'.join((data['id_str'], user['screen_name']))
    filename = os.path.join(basedirname, basefilename)
    if os.path.isfile(filename + '.json'):
        log.info("Archive file %s.json for tweet %s already exists." % (filename, data['id']))
        return
    try:
        if not os.path.isdir(basedirname):
            os.makedirs(basedirname)
    except Exception as e:
        log.error("Archive directory %s cannot be created or is not writable: %s" % (basedirname, str(e)))
        return
    try:
        with open(filename + '.json', 'w') as f:
            json.dump(data, f, indent=4)
        log.info("Archived tweet %s to %s.json" % (data['id'], filename))
        for a in glob.glob(os.path.join(config.archive_dir, 'users', '%s.json' % insensitive(user['screen_name']))):
            os.remove(a)
            log.info("Removed cache file %s" % a)

    except Exception as e:
        log.error("Archive file %s cannot be created or is not writable: %s" % (filename + '.json', str(e)))
        return
    if config.archive_photos and data['entities'].has_key('media'):
        for i,m in enumerate(data['entities']['media']):
            mediafile = '.'.join((filename, str(i), m['media_url_https'].split('.')[-1]))
            mediaurl = ':'.join((m['media_url_https'], 'orig'))
            if m.has_key('type') and m['type'] == 'photo':
                try:
                    urllib.URLopener().retrieve(mediaurl, mediafile)
                    log.info("Archived media: %s -> %s from tweet %s." % (mediaurl, mediafile, data['id']))
                except Exception as e:
                    log.error("Archive image cannot be downloaded from %s or created in %s: %s" % (mediaurl, mediafile, str(e)))


if __name__ == "__main__":
    twitter = twython.Twython(app_key=config.app_key, app_secret=config.app_secret, oauth_token=config.oauth_token, oauth_token_secret=config.oauth_token_secret)
    for arg in sys.argv[1:]:
        log.info("Retrieving Tweet ID [%s]" % arg)
        t = twitter.show_status(id="%s" % arg)
        save(t)
