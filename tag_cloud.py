import tweepy
import json
import Queue
import time
import sys
import string
import redis
from threading import Thread
import setup

#Used for parsing tweets stored in a given queue.
class Parser(Thread) :
	def __init__(self, q, startT, runT, limSize=False, maxSize=0, clrDB=True) :
		Thread.__init__(self)
		self.limitedSize = limSize
		self.maxSize = maxSize
		self.q = q
		self.startTime = startT
		self.runTime = runT
		self.clearDB = clrDB

		self.stopWords = dict()
		self.result = dict()
		self.rdb = redis.StrictRedis(host=setup.redisHost, port = setup.redisPort, db=0)

		if limSize :
			self.rdb.set(setup.other, 0)

		self.loadStopWords()


	#Loads a stopwords file.
	def loadStopWords(self) :
		with open(setup.stopWordsFile, 'r') as sWFile :
			for line in sWFile :
				for word in line.split() :
					self.stopWords[word] = True


	#Checks if character is letter or number.
	def isLetterOrNumber(self, l) :
		if (l >= 'a' and l <= 'z') or (l >= 'A' and l <= 'Z') or (l >= '0' and l <= '9') :
			return True
		else :
			return False


	#Removes leading or trailing punctuation.
	def removePunctuation(self, word) :
		while len(word) > 0 and not self.isLetterOrNumber(word[0]) :
			word = word[1:]

		while len(word) > 0 and not self.isLetterOrNumber(word[-1]) :
			word = word[:-1]

		return word


	#Checks if word is a link.
	def isLink(self, word) :
		if "http://" in word or "https://" in word :
			return True
		else :
			return False


	#Checks if a word is a username.
	def isUserName(self, word) :
		return word[0] == '@'


	#Removes unwanted words from a list: links, usernames, stopwords.
	def removeUnwanted(self, words):
		result = list()
		for w in words :
			if not (self.isLink(w) or self.isUserName(w) or w in self.stopWords) :
				newWord = self.removePunctuation(w)
				if not newWord == '':
					result.append(newWord)

		return result


	#Stores colected statistics from one tweet.
	def storeStatistics(self, words) :
		for word in words:
			if self.rdb.get(word) :
				self.rdb.incr(word)
			else :
				if self.limitedSize :
					if self.rdb.dbsize() < self.maxSize :
						self.rdb.set(word, 1)
					else :
						self.rdb.incr(setup.other) 
				else :
					self.rdb.set(word, 1)


	#Processes one tweet.
	def process(self, tweet) :
		words = tweet.split()
		words = self.removeUnwanted(words)
		self.storeStatistics(words)


	def run(self):

		while((time.time() - self.startTime) < self.runTime or not self.q.empty()):
			data = self.q.get()
			if(data == None) :
				break
			else :
				self.process(data)

		keys = self.rdb.keys('*')

		output = dict();

		for key in keys:
			output[key] = self.rdb.get(key)

		#Checks if the user wants to use the currently stored data in the DB
		#in further use of the program, or wants to clear the data after 
		#displaying the results.

		if self.clearDB :
			self.rdb.flushdb()

		print json.dumps(output)


#Colects tweets from stream and stores them in a queue.
class StdOutListener(tweepy.StreamListener):
	def __init__(self, q, startTime, runTime) :
		tweepy.StreamListener.__init__(self)
		self.q = q
		self.startTime = startTime
		self.runTime = runTime

	def on_data(self, data):
		decoded = json.loads(data)

		if not ('delete' in decoded) and decoded['lang'] == setup.language :
			self.q.put(decoded['text'].encode('ascii', 'ignore').lower())

		if (time.time() - self.startTime) < self.runTime :
			return True
		else :
			self.q.put(None)
			return False

	def on_error(self, status):
		print status

if __name__ == '__main__' :
	tweets = Queue.Queue()

	auth = tweepy.OAuthHandler(setup.consumer_key, setup.consumer_secret)
	auth.set_access_token(setup.access_token, setup.access_token_secret)
	
	if len(sys.argv) == 1:
		print setup.usage
		sys.exit(setup.err1)
		 
	
	runTime = int(sys.argv[1])

	startTime = time.time()
	listener = StdOutListener(tweets, startTime, runTime)
	stream = tweepy.Stream(auth, listener)

	if len(sys.argv) >= 3 :
		maxSize = int(sys.argv[2])

		clrDb = False

		if len(sys.argv) == 4:
			clrDb = bool(sys.argv[3])
		
		parserUnit = Parser(tweets, startTime, runTime, True, maxSize, clrDb)
	else :
		parserUnit = Parser(tweets, startTime, runTime)


	parserUnit.start()
	stream.sample()
	parserUnit.join()