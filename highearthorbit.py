#!/usr/bin/python

import twython, time, pprint, traceback, os
import config
from twython import TwythonStreamer, TwythonError, TwythonRateLimitError
import urllib, json, glob
import thread
queuelock = thread.allocate_lock()
import logging
logging.basicConfig(filename='highearthorbit.log', format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

"""
Config: create a file named config.py with these lines:

app_key="<your app key>"
app_secret="<your app secret>"
oauth_token="<your oauth token>"
oauth_token_secret="<your oauth token secret"
owner="<twitter name of owner>"

All keys, secrets and tokens are creatable on http://apps.twitter.com

Run: until I implement a better solution, run it in a screen session

"""

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

def update_friends(friendlist):
    global friends
    friends = friendlist
    log.info("Updated friends", friends)

def update_approved_list():
    global listmembers
    try:
        listmembers = [ user["id"] for user in twitter.get_list_members(slug=config.approved_list['name'], owner_screen_name=config.approved_list['owner'])["users"] ]
        log.info("Updated members of list %s by @%s: %s", (config.approved_list['name'], config.approved_list['owner'], str(listmembers)))
    except:
        log.warning("Error updating list %s by @%s." % (config.approved_list['name'], config.approved_list['owner']))

def find_and_delete_blocked_retweets():
    global blocked
    log.info("Checking the last 100 tweets in my timeline for retweets of blocked users. Just to destroy them.")
    try:
        tl = twitter.get_home_timeline(count=100)
    except:
        log.error('Exception caught while checking for tweets of blocked users.')
    else:
        for t in tl:
            if t['retweeted_status']['user']['id'] in blocked:
                queue(twitter.destroy_status, id=t['id'])
                log.info('Will destroy status %s, because @%s is blocked.' % (t['id'], t['retweeted_status']['user']['screen_name']))
                for archived_file in glob.glob(os.path.join(config.archive_dir, '*', t['retweeted_status']['id_str']) + '-*.*'):
                    try:
                        os.remove(archived_file)
                    except:
                        log.warning("Unable to delete archive file %s" % archived_file)
                    else:
                        log.info("Removed archive file %s" % archived_file)

def update_block_list():
    global blocked
    old_blocked = blocked
    try:
        blocked = twitter.list_block_ids()['ids']
        log.info("Updated block list.")
    except Exception as e:
        log.warning("Could not update block list: %s", str(e))
    new = list(set(blocked) - set(old_blocked))
    if len(new) > 0:
        find_and_delete_blocked_retweets()

def cleanrts():
    for r in rts:
        m,t = r
        if t < time.time() - 3600:
            rts.remove(r)
            
def _fmt(func, args, kwargs):
    return "%s(%s)" % (func.__name__, ', '.join([ a for a in args ] + [ "%s=%s" % (k, repr(v)) for k,v in kwargs.iteritems() ]))

def run_queue():
    global _done, _queue, _fail, twitter
    queuelock.acquire()
    t = int(time.time())
    _done = dict([ (k,v) for k,v in _done.iteritems() if k > t - 86400 ])
    _fail = dict([ (k,v) for k,v in _fail.iteritems() if k > t - 3600 ])
    queuelock.release()
    log.info('Running queue (%s actions). Actions during last 24h: %s/last 15m: %s, Fails in the last 60m: %s.' % (len(_queue), len(_done), len([ k for k,v in _done.iteritems() if k > t - 900 ]), len(_fail)))
    while len(_queue) > 0 and twitter is not None:
        t = int(time.time())
        queuelock.acquire()
        if len([ k for k,v in _done.iteritems() if k > t - 900 ]) + len([ k for k,v in _fail.iteritems() if k > t - 900 ]) >= config.rate_limit_per_15min:
            log.warn("Rate Limit reached. Currently not working on the %s items in the queue." % len(_queue))
            queuelock.release()
            break
        if len(_fail) > 15:
            log.error("Fail Limit reached. Killing everything.")
            queuelock.release()
            thread.interrupt_main()
        (tries, (func, args, kwargs)) = _queue.pop(0)
        if not (func, args, kwargs) in _done.values():
            try:
                log.debug("Trying %s from queue" % _fmt(func, args, kwargs))
                if not config.dry_run:
                    func(*args, **kwargs)
            except Exception as e:
                if isinstance(e, TwythonError) and e.error_code == 403:
                    log.warn("Twitter says I did %s already." % _fmt(func, args, kwargs))
                    #_fail[t] = (func, args, kwargs)
                elif isinstance(e, TwythonRateLimitError):
                    log.warn("Twitter says I hit the Rate Limit with %s. Re-queuing." % _fmt(func, args, kwargs))
                    _queue.insert(0, (tries, (func, args, kwargs)) )
                    if e.retry_after is not None:
                        time.sleep(int(e.retry_after))
                    queuelock.release()
                elif tries < 3:
                    log.error(str(e), exc_info=True)
                    _queue.append( (tries+1, (func, args, kwargs)) )
                    _fail[t] = (func, args, kwargs)
                    log.warn("Try #%s of %s from queue failed, re-queuing." % (tries+1, _fmt(func, args, kwargs)))
                    log.warn("Reinitializing twitter connection except streaming.")
                    twitter = twython.Twython(app_key=config.app_key, app_secret=config.app_secret, oauth_token=config.oauth_token, oauth_token_secret=config.oauth_token_secret)
                else:
                    log.error("Tried 3 times, but always got an exception... giving up on %s" % _fmt(func, args, kwargs))
            else:
                _done[t] = (func, args, kwargs)
                log.info("%s is done." % _fmt(func, args, kwargs)) 
        else:
            log.warn("I already had that one in my queue: %s" % _fmt(func, args, kwargs))
        queuelock.release()
        time.sleep(5)
        
def queuewatch(check_time=900):
    while True:
        time.sleep(check_time)
        update_block_list()
        run_queue()
            
def queue(func, *args, **kwargs):
    global _queue
    _queue.append( (0, (func, args, kwargs)) )
    log.debug("Queued %s." % _fmt(func, args, kwargs)) 
            
def rt(tweetid):
    cleanrts()
    if twitter is not None:
        if not tweetid in [ m for m,t in rts ]:
            log.info("Will retweet id %s" % tweetid)
            queue(twitter.retweet, id=tweetid)
            rts.append( (tweetid, time.time(), ) )
        else:
            log.info("Tweet id %s has been retweeted already." % tweetid)
            
def tweet(tweettext):
    if twitter is not None:
        queue(twitter.update_status, status=tweettext[0:140])

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

def decide(data):
    if 'retweeted_status' in data and data['user']['screen_name'] == user_screenname:
        save(data)
    elif 'text' in data:
        log.info("%s @%s: %s" % (data['id'], data['user']['screen_name'], data['text'].replace('\n', ' ')))
        if data['user']['id'] in blocked:
            log.info('Not retweeting id %s because user @%s is blocked.' % (data['id'], data['user']['screen_name']))
        elif data['text'].lower().find(config.track.lower()) > -1 and not 'retweeted_status' in data:
            rt(data['id'])
            #save(data)
    elif 'direct_message' in data:
        update_approved_list()
        log.info("DM from @%s: %s" % (data['direct_message']['sender']['screen_name'], data['direct_message']['text']))
        if data['direct_message']['sender']['id'] in listmembers:
            tweet(data['direct_message']['text'])
    elif 'friends' in data:
        update_friends(data['friends'])
    else:
        log.warning("Unknown notification received:")
        log.warning(data)


class MyStreamer(TwythonStreamer):
    def on_success(self, data):
        decide(data)
        thread.start_new_thread(run_queue, ())

    def on_error(self, status_code, data):
        log.error("Error Code %s received in data package:" % status_code)
        log.error(data)

        # Want to stop trying to get data because of the error?
        # Uncomment the next line!
        # self.disconnect()

while True:
    try:
        log.info("====== Entering High Earth Orbit in the Twitterverse... ehm. Okay, okay, I'm initializing. ======")
        twitter = twython.Twython(app_key=config.app_key, app_secret=config.app_secret, oauth_token=config.oauth_token, oauth_token_secret=config.oauth_token_secret)
        creds = twitter.verify_credentials()
        userid = creds['id_str']
        user_screenname = creds['screen_name']
        update_approved_list()
        update_block_list()
        log.info('Reading last retweets.')
        rts += [ (t['retweeted_status']['id'], time.time(),) for t in twitter.get_home_timeline(count=config.read_back) if t.has_key('retweeted_status') ]
        for a in (1,2):
            time.sleep((a-1)*10)
            log.info("Catching up on missed tweets, take %s." % a)
            old_tweets = twitter.search(q=config.track + " -filter:retweets", count=config.read_back-5)['statuses']
            for t in sorted(old_tweets, key=lambda t: t['id']):
                decide(t)
        log.info('Caught up on missed tweets, running queue.')
        thread.start_new_thread(run_queue, ())
        thread.start_new_thread(queuewatch, (900,))

        stream = MyStreamer(config.app_key, config.app_secret, config.oauth_token, config.oauth_token_secret)
        stream.creds = creds
        
        log.info('Going into streaming mode')
        stream.statuses.filter(track=config.track)

    except Exception, e:
        log.warning('==Exception caught, restarting==')
        log.warning(e)
        log.debug(str(e), exc_info=True)
        if int(time.time()) - lasttry < 120:
            log.error('==Two Exceptions in the last 2 minutes are one too many, exiting to avoid hammering...')
            break
        else:
            time.sleep(5)
            lasttry = int(time.time())

