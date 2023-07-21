import csv, os, logging, requests, json
from trueskill import Rating, quality_1vs1, rate_1vs1
from ratelimit import limits, RateLimitException
from backoff import on_exception, expo
logging.basicConfig(filename='startgg_scrubber.log', encoding='utf-8', level=logging.DEBUG)
#read config.txt for required API credntials or throw an error while generating the file
#TODO replace this with variables being passed from main thread when called
try:
	
	with open("config.txt", "r") as config:
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
		f=open("config.txt", "x")
		f.write("challongeid=\nchallongekey=\nstarggid=\nstartggkey=\ngameid=")
		f.close()
	except:
		exit
	sys.exit("config.txt error, enter your challonge and startgg credentials into the generated file")
auth_token = skey

	
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
		return response
	else:
		print(response.status_code)
		print(response.text)
		exit()
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
def tsrate():
	os.makedirs("data", exist_ok = True)
	os.chdir('./data')
	tsMu= 25
	tsSigma = 8.333
	elowrite = True
	players = {}
	knownNames = {}
	try:
		e = open("names.csv", 'r', encoding="utf-8")
		names = 0
		for line in e:
			data = line[:-1].split(",")
			knownNames[data[0]] = data[1]
			names += 1
		e.close()
	except:
		logging.debug("Error loading known names from names.csv")
		exit()

	def rate(winner, loser):
		winner, loser = rate_1vs1(winner, loser)
		return(winner, loser)

	lastTime = 0
	dupeMatch = 0
	dupeWinner = ""
	dupeLoser = ""
	with open("startgg_matches.txt",'r', encoding='latin-1') as data_file:
		for line in data_file:
			data = line[:-1].split(",")
			if data[0] == "date":
				continue
			data[1] = data[1].strip()
			data[2] = data[2].strip()
			if data[0] == lastTime and dupeWinner == data[1] and dupeLoser == data[2]:
				dupeMatch += 1
				continue
			lastTime = data[0]
			dupeWinner = data[1]
			dupeLoser = data[1]
			if data[1] == "None" or data[2] == "None":
				continue
			if not data[1] in players.keys():
				#print("%s is new, adding to rankings" % data[1])
				players.update({data[1]: tuple((Rating(tsMu, tsSigma),0,0))})
			if not data[2] in players.keys():
				#print("%s is new, adding to rankings" % data[2])
				players.update({data[2]: tuple((Rating(tsMu, tsSigma),0,0))})
			try:
				p1, p2 = rate(players[data[1]][0], players[data[2]][0])
			except:
				print("Broke math with %s %s\n" % (data[1], data[2]))
				continue
			p1match = players[data[1]][1] + 1
			players.update({data[1]: tuple((p1,p1match,data[0]))})
			p2match = players[data[2]][1] + 1
			players.update({data[2]: tuple((p2,p2match,data[0]))})
	print("Finished the job and skipped over %i dupe matches\n" % dupeMatch)
	r = open('trueskillrankings.csv', 'w', encoding="utf-8")
	players = sorted(players.items(), key=lambda players:players[1][0].mu, reverse=True)
	for item in players:
		confidence = item[1][0].mu * (1 - (item[1][0].sigma/tsSigma))
		if item[0] in knownNames:
			playerName = knownNames[item[0]]
		else:
			playerName = ""
		try:
			r.write("%s,%s,%s,%s,%i,%s,%s\n" % (item[0], item[1][0].mu, item[1][0].sigma, confidence, item[1][1], item[1][2], playerName))
		except BaseException as error:
			print(error)
			print("%s broke everything\n" % item[0])
	r.close()
	os.chdir("../")
tsrate()
