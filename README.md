High Earth Orbit
================

A Twitter Bot to follow a hashtag on twitter, archive and optionally retweet
all tweets found.  Also, shows the archive as a website.

Configured correctly and started before it happened, this Bot can retweet
and archive a whole Hashtag-Timeline on Twitter, while providing a
convenient web page as an archive viewer.

As far as possible, the Bot and archive web page will honour actions done in
the connected Twitter account.  Depending on configuration, the following
actions have consequences:

  * Blocking a user: The Bot will check it's last 100 retweets for any
    tweets from that user and destroy the retweet.  Also, it will delete
    that retweet's archive file from the archive (but not from it's cache
    file!).  And in the future, this user will be completeley ignored. 
    Updating the blocklist, unfortunately, is a scheduled event.  On
    average, this takes 7.5 minutes to take effect; but in extreme cases, it
    might take up to 30 minutes.
  * Taking back a Retweet: The retweet's ID will appear on the archive
    webpage as "deleted".  One catch, though: If the Bot is restarted, it
    will check the last 100 search results for tweets that it did not
    retweet yet...  and maybe retweets it again.  (Effective only if
    archive_own_retweets_only=True)
  * Retweeting a tweet: The Retweet is archived and, if a photo is attached,
    shown on the archive web page (Should work, never watched it being
    executed; Effective only if archive_own_retweets_only=True)
  * Adding a user to a Twitter list: Well, the bot can read it, but I'm not
    quite sure what to do with it.  To fulfill the original purpose (which
    was letting the Bot tweet anything that was DM'd to him from people on
    the list), I'd need to read a second Twitter data stream in a different
    thread...  which just isn't evaluated and implemented yet.

While the Bot itself completely archives all his own retweets and their
metadata (which includes the original tweet in it's entirety), the web page
only publishes the tweet ID and uses Twitters widget.js to load and display
the original tweets.  This gives the original author the power to delete his
own tweet from the archive webpage by just deleting it on Twitter.  In this
case, the web page will just show a message that a tweet might have been
deleted.  If Twitter users decide to protect, suspend or delete their
account, their Tweets are shown in the same fashion as long as they stay
protected or suspended.

To work with this Bot, you'll need to get some tokens from
https://apps.twitter.com.  These tokens have to be put into config.py (copy
config_clean.py to config.py and edit it).


Configurable to:
  
  * Retweet everything found in a hashtag stream.
  * Listen and archive only without retweeting anything.
  * Archive only it's own retweets or everything excluding retweets (the
    latter disables the bot owner's power to delete a tweet from the archive
    web page just by taking back the retweet).
  * Archive photos attached to a tweet (no re-publishing, though).
  * Do Spam filtering
    * against users: by blocking the user in the connected Twitter account
    * against words: by using a word blacklist
    * against hashtag spammers: by ignoring all tweets sporting more than 
      $configurable_amount hashtags.
  * Doing nothing except filling memory and the logfile with tweets (You'd
    have to configure it to "listen and archive only" while only archiving
    it's own retweets.  Actually, this is the default configured behaviour).

Not configurable yet (a.k.a TODOs for which I would accept pull requests):
  
  * Show all tweets (not only those with photo) on the archive web page.
  * Using a different time resolution than "weekly" on the archive web page.
  * Adding words to the blacklist without restarting the bot.

Modifiable to:

  * do anything...? Sure, you could modify this source code to eventually
    trigger broadcasting Rick Astley on all TV channels worldwide just by
    receiving a carefully worded tweet including a fateful hashtag.  But why
    would you want to do that?


Dependencies
------------

  * Python 2.7 (although 3.x might just work)
  * Python modules for the Bot:
    * twython
  * Python modules for archive web page:
    * flask
    * genshi
    * pytz
  * a Twitter account to connect this bot to. This account needs to be
    connected to a mobile phone number due to Twitter's rules.  Also, think
    twice before using your personal account for this.
  * running on a linux box that runs 24/7
  * a working internet connection


Install
-------

```bash
$ git clone https://github.com/orithena/sportswarnbot.git
```


Configure
---------

```bash
$ cp config_clean.py config.py
$ $EDITOR config.py
```

Configuration is described in config_clean.py. The main point is the Twitter
API key and OAuth secret -- use https://apps.twitter.com to obtain one (you
need to be logged in to the Twitter account you wish to use for this Bot).

Keep the layout of the config file intact, do not introduce whitespace at
the start of a line ...  after all, it's just another python source file.


Run
---

Well, I just start a screen session and run "python highearthorbit.py" in
there...  I just didn't write a startup script for it yet.

You might serve the archive web page via highearthorbit.wsgi (see your
webserver's documentation, section "WSGI apps") or just start "python
webarchive.py" on the command line (which will then serve the web page on
http://localhost:5000 in debug mode).


Modify
------

Have fun! Well... eventually I'll come around to write some more code
comments.


Republish modifications
-----------------------

I accept pull requests on github.
