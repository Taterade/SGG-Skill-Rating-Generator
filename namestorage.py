import csv, logging
import os, requests, json
from trueskill import Rating, quality_1vs1, rate_1vs1
from ratelimit import limits, RateLimitException
from backoff import on_exception, expo
logging.basicConfig(filename='startgg_scrubber.log', encoding='utf-8', level=logging.DEBUG)
#read config.txt for required API credntials or throw an error while generating the file
#TODO replace this with variables being passed from main thread when called
try:
	with open("config.txt", "r", encoding="utf-8") as config:
		for line in config:
			name, var = line.partition("=")[::2]
			var.strip()
			if name == "challongeid":
				cid = var
				cid = cid.rstrip()
			if name == "challongekey":
				ckey = var
				ckey = ckey.rstrip()
			if name == "startggkey":
				skey = var
				skey = skey.rstrip()
			if name == "gameid":
				sg_id = var
				sg_id = sg_id.rstrip()
				sg2_id = sg_id
	if len(skey) < 3:
		raise Exception()
except:
	try:
		f=open("config.txt", "x", encoding="utf-8")
		f.write("challongeid=\nchallongekey=\nstarggid=\nstartggkey=\ngameid=")
		f.close()
	except:
		exit
	sys.exit("config.txt error, enter your challonge and startgg credentials into the generated file")
auth_token = skey
os.chdir('./data')
#TODO once again make this an imported function to reduce duplication
api_url = "https://api.start.gg/gql/alpha"
@on_exception(expo, Exception, max_time=61)
@limits(calls=80, period=61)
def make_query(query):
	response = requests.post(api_url,
					headers = {"Authorization": "Bearer " + auth_token},
					json={"query": query})
	if response.status_code == 429:
		raise Exception()
	elif response.status_code == 200:
		return response
	elif response.status_code == 503:
		logging.debug(response.text)
		return response
	else:
		print(response.status_code)
		print(response.text)
		exit()
#does what it says, retrieve a player's name based on their startgg user slug
def getPlayerName(slug):
	query = """query GetUserName
	{{
		user(slug: {slug})
		{{
		player
			{{
			gamerTag
			prefix
			}}
		}}
	}}""".format(slug = slug)
	return make_query(query)
knownNames = {}
def processnames(): 
	#TODO open the names.csv file, if it doesn't exist make one and open that
	#also read all existing discriminator and name pairings into key array
	try:
		e = open("names.csv", 'r', encoding="utf-8")
		names = 0
		for line in e:
			data = line[:-1].split(",")
			knownNames[data[0]] = data[1]
			names += 1
		print(str(names) + " known names")
		e.close()
	except: 
		print("names.csv not found, creating file")
		#e = open("names.csv", 'w', encoding="utf-8")
		#e.close()
		
	#TODO loop through all discriminator that do not have a name attached already and append them to names.csv 
	f = open("trueskillrankings.csv", 'r', encoding="utf-8")
	e = open("names.csv", 'a', encoding="utf-8")
	for line in f:
		data = line.split(",")
		if data[0] in knownNames:
			continue
		else:
			try:
				result = getPlayerName("\"user/" + data[0] + "\"").json()
			except:
				continue
			if result["data"]["user"] == None:
				continue
			else:
				e.write(data[0] + "," + result["data"]["user"]["player"]["gamerTag"] + "\n")
				logging.debug("added " + data[0] + "," + result["data"]["user"]["player"]["gamerTag"] + " to the names.csv write operations")
	e.close()
	f.close()
