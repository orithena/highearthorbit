# -*- coding: utf-8 -*-

# The API Keys and oauth tokens from https://apps.twitter.com/
# 
# Create a new App, set the Access Level to Read/Write, generate Tokens, copy and paste them here:
app_key=""
app_secret=""
oauth_token=""
oauth_token_secret=""

# The owner of the bot. Should be a real user who actually reads his timeline.
# Do not prepend the @ mark.
owner="anathem"

# What search query to track.
# This should be a search query understood by both search API and streaming API.
# Hint: "-filter:retweets" won't work in streaming API, which is why it's automatically appended
# for the catch-up search when starting up.
track = '#Fotoprojekt2015'

# Whether to actually do anything that changes anything regarding your twitter account.
# If this is True, this Bot only reads and archives tweets, but does not retweet nor post anything.
twitter_is_read_only = True

# Enter a local directory for the archive.
# If it does not exist yet, it is attempted to be created.
archive_dir = "archive"

# If you only save the bot's retweets to the archive, then the webviewer is able to "dumb-detect"
# that a Retweet by the Bot has been destroyed manually from the Botaccount.
archive_own_retweets_only = True

# Whether to auto-download and archive attached media files (of type photo) or not.
archive_photos = False

# The list of approved twitter users with additional rights (not really used yet).
approved_list = { 
  'name': 'Approved',
  'owner': owner,
}

# Hashtagspam threshold. If a tweet contains more than this count of hashtags (i.e. hashtags
# recognized and link-enhanced by twitter), it is considered spam and not even being archived. 
spamfilter_max_hashtags = 3

# Blacklisted words and phrases.
# The words have to be listed in lowercase. If you use characters that are not in ASCII range,
# you need to prepend the string literal with a u for Unicode, like so: u'arschlöcher'.
spamfilter_word_blacklist = [
  u'fick dich',
  u'fickt euch',
  u'arschlöcher',
]

# Rate limit per 15min sliding window.
# Never enter more than 15 here or you might run the risk that Twitter blocks you for hammering!
rate_limit_per_15min = 12

# How many Tweets to read back on startup/restart?
# This is limited to 100 by the Twitter API. Also, don't count on getting that many.
# Don't set this to less than 5.
read_back = 100


