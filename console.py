import twython
import config
import time
from exceptions import StopIteration

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

def yielder(func, *args, **kwargs):
  min_id = max_id = None
  queue = []
  backwards = kwargs.has_key('until')
  while True:
    if len(queue) == 0:
      if not backwards:
        kwargs['max_id'] = min_id
      else:
        kwargs['since_id'] = max_id
      queue.extend( func(*args, **kwargs)["statuses"] )
      if len(queue) > 0:
        if min_id is None or min_id > queue[-1]['id']:
          min_id = queue[-1]['id']
        if max_id is None or max_id > queue[0]['id']:
          max_id = queue[0]['id']
        if backwards and kwargs.has_key('until'):
          kwargs.pop('until')
      else:
        raise StopIteration()
    time.sleep(1)
    yield(queue.pop(-1 if backwards else 0))

def tweets_since(since):
  for a in yielder(twitter.search, q='#zkk15', until=since):
    print a['created_at'], a['user']['screen_name']
    print a['text']
    print
      