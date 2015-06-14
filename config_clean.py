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

# Enter a local directory for the archive.
# If it does not exist yet, it is attempted to be created.
archive_dir = "archive"

# The list of approved twitter users with additional rights.
approved_list = { 
  'name': 'Approved',
  'owner': owner,
}

# Rate limit per 15min sliding window.
# Never enter more than 15 here or you might run the risk that Twitter blocks you for hammering!
rate_limit_per_15min = 12

# Whether to actually tweet anything.
# If this is True, this Bot only archives tweets.
dry_run = False

# How many Tweets to read back on startup/restart?
# This is limited to 100 by the Twitter API. Also, don't count on getting that many.
# Don't set this to less than 5.
read_back = 100
