import tweepy
import json

consumer_key = 'uPekGEsc5dFlRJGZzPWxzpgH4'
consumer_secret = 'wkmbmjMdlNQqUpkji7XmvZMarGm3gBLVNLYUxbgoz1LEYQ5s8d'
access_token = '3141574606-vJD1t4oJCwbdZMLIpXDi0miHjHNotAcDcRwqiqr'
access_token_secret = 'ngWqWlsikvEdNEmOrzuVJuQDKkWhCUJOUFTluUV5DAxFp'

class Parser():
	def parse(self, rawData):
		pass

class StdOutListener(tweepy.StreamListener):
    def on_data(self, data):
        decoded = json.loads(data)

        if (not ('delete' in decoded) and decoded['lang'] == 'en') :
        	print decoded['text'].encode('ascii', 'ignore')

        return True

    def on_error(self, status):
        print status

if __name__ == '__main__':
    listener = StdOutListener()
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    stream = tweepy.Stream(auth, listener)
    stream.sample() 