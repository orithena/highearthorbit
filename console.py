import twython
import config
import time
import highearthorbit
import webviewer
from exceptions import StopIteration
import os, json, datetime, dateutil.parser, pytz

twitter = twython.Twython(app_key=config.app_key, app_secret=config.app_secret, oauth_token=config.oauth_token, oauth_token_secret=config.oauth_token_secret)

class MyStreamer(twython.TwythonStreamer):
    friends = []
    listmembers = []
    rts = []
    def on_success(self, data):
        if 'text' in data:
            print ("%s: %s" % (data['user']['screen_name'], data['text'])).encode('utf-8')
        elif 'direct_message' in data:
            print ("DM %s: %s" % (data['direct_message']['sender']['screen_name'], data['direct_message']['text']))
            #if data['direct_message']['sender']['id'] in self.listmembers:
            #    self.tweet(data['direct_message']['text'])
        else:
            print("unknown notification received:")
            print(data)

    def on_error(self, status_code, data):
        print status_code
        # Want to stop trying to get data because of the error?
        # Uncomment the next line!
        # self.disconnect()

stream = MyStreamer(app_key=config.app_key, app_secret=config.app_secret, oauth_token=config.oauth_token, oauth_token_secret=config.oauth_token_secret)

def _fmt(func, args, kwargs):
    return "%s(%s)" % (func.__name__, ', '.join([ a for a in args ] + [ "%s=%s" % (k, repr(v)) for k,v in kwargs.iteritems() ]))

def yielder(func, *args, **kwargs):
  min_id = max_id = None
  queue = []
  last_returns = 0
  backwards = kwargs.has_key('until')
  while True:
    if len(queue) == 0:
      if not backwards:
        kwargs['max_id'] = min_id
      else:
        kwargs['since_id'] = max_id
      print( "Calling %s" % _fmt(func, args, kwargs) )
      queue.extend( func(*args, **kwargs)["statuses"] )
      last_returns = len(queue)
      if len(queue) > 3:
        if min_id is None or min_id > queue[-1]['id']:
          min_id = queue[-1]['id']
        if max_id is None or max_id > queue[0]['id']:
          max_id = queue[0]['id']
        if backwards and kwargs.has_key('until'):
          kwargs.pop('until')
      else:
        print( "Twitter returned less than 3 objects. Stopping." )
        raise StopIteration()
    time.sleep(120.0 / last_returns)
    yield(queue.pop(-1 if backwards else 0))

def save_search(q, out_dir):
  for t in yielder(twitter.search, q=q, count=100):
    dirname = os.path.join(out_dir, t['id_str'][:-15].zfill(6))
    if not os.path.isdir(dirname):
      os.makedirs(dirname)
    fname = os.path.join(dirname, "%s-%s.json" % (t['id_str'], t['user']['screen_name']))
    with open(fname, 'w+') as fp:
      json.dump(t, fp)
      print("Written %s by %s at %s to %s" % (t['id_str'], t['user']['screen_name'], t['created_at'], fname))
    if dateutil.parser.parse(t['created_at']).astimezone(pytz.timezone('Europe/Berlin')) < pytz.utc.localize(datetime.datetime(2014,12,31)):
      print("Reached new year 2015. Stopping.")
      break
    
