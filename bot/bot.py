import json
import re

from twython import Twython
from twython import TwythonStreamer

from .db import DEFAULT_DB, GoldStarDB

from .secrets import *

# Configuration
TWITTERHANDLE = 'AstroGoldStars'
LOGFILE = 'bot.log'
STREAMING_LOGFILE = 'streaming.log'


class InvalidTweetException(Exception):
    """Raised when a tweet should not result in a star transaction."""
    pass


class TweetHandler():

    def __init__(self, tweet, dbfile=DEFAULT_DB, dry_run=False):
        self.validate(tweet)
        self.tweet = tweet
        self.dbfile = dbfile
        self.db = GoldStarDB(self.dbfile)
        self.dry_run = dry_run

    def validate(self, tweet):
        """Do not allow non-status, retweets, or the bot's own tweets."""
        if 'text' not in tweet:
            raise InvalidTweetException('{} does not look like a status.'.format(tweet['id']))
        if 'retweeted_status' in tweet:
            raise InvalidTweetException('{} is a retweet.'.format(tweet['id']))
        if tweet['user']['screen_name'] == TWITTERHANDLE:
            raise InvalidTweetException('{} posted by {}.'.format(tweet['id'], TWITTERHANDLE))

    def get_recipients(self):
        """Returns the recipients of the star as a list of dictionaries."""
        recipients = []
        for mention in self.tweet['entities']['user_mentions']:
            screen_name = mention['screen_name']
            if ((screen_name != TWITTERHANDLE) and
                    (screen_name not in recipients) and
                    (self.tweet['text'][mention['indices'][1]] == '+')):
                recipients.append(mention)
        return recipients  # unique recipients only

    def handle_hide(self):
        re.findall('@AstroGoldStars\W+hide\W+(\d+)', '@AstroGoldStaRs hiDe 3039445', re.IGNORECASE)

    def handle(self):
        """Save stars to the database and tweet the responses."""
        responses = []
        recipients = self.get_recipients()
        # Allow a star to be hidden by tweeting '@TWITTERHANDLE hide statusid'
        if re.findall('^\W*@' + TWITTERHANDLE + '\W+hide\W+(\d+)', self.tweet['text'], re.IGNORECASE):
            self.db.delete_star(self.tweet['id'], self.tweet['user']['id'])
            text = '@{} Ok, no problem.'.format(self.tweet['user']['screen_name'])
            self.post_tweet(status=text)
            return [text]
        # Do not allow a user to give a star to self
        if self.tweet['user']['screen_name'] in [rec['screen_name'] for rec in recipients]:
            text = ("@{} I'm sorry, {}. "
                    "I'm afraid I can't do that.".format(
                        self.tweet['user']['screen_name'],
                        self.tweet['user']['name'].split(' ')[0]))
            self.post_tweet(status=text)
            return [text]
        for recipient in recipients:
            # Save the transaction in the db
            self.db.add(donor=self.tweet['user'],
                        recipient=recipient,
                        tweet=self.tweet)
            # Create the tweet
            url = 'https://twitter.com/{}/status/{}'.format(self.tweet['user']['screen_name'], self.tweet['id'])
            text = ('@{} Congratulations, '
                    'you just earned a 🌟 from @{}! Your total is {}. '
                    '{}'.format(
                            recipient['screen_name'],
                            self.tweet['user']['screen_name'],
                            self.db.count_stars(recipient['id']),
                            url))
            responses.append(text)
            self.post_tweet(status=text)
        return responses

    def post_tweet(self, status):
        if not self.dry_run:
            twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
            result = twitter.update_status(status=status,
                                           in_reply_to_status_id=self.tweet['id'])
            with open(LOGFILE, 'a') as log:
                log.write(json.dumps(result))
            return twitter, result


class GoldStarStreamer(TwythonStreamer):

    def __init__(self):
        super(GoldStarStreamer, self).__init__(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

    def on_success(self, data):
        try:
            with open(STREAMING_LOGFILE, 'a') as log:
                log.write(json.dumps(data))
                TweetHandler(data).handle()
        except Exception as e:
            print('ERROR! {}'.format(e))

    def on_error(self, status_code, data):
        print('STREAMER ERROR: {}'.format(status_code))


def run():
    stream = GoldStarStreamer()
    stream.statuses.filter(track='@'+TWITTERHANDLE)


if __name__ == '__main__':
    run()
