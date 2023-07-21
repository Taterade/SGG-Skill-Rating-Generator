import challonge #challonge python integration from ZEDGR: https://github.com/ZEDGR/pychallonge
import time, logging
import datetime
from trueskill import Rating, quality_1vs1, rate_1vs1
import csv
import sys
import os
import requests
import urllib.request
import json
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
	if len(cid) < 3 or len(ckey) < 3 or len(skey) < 3:
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
sg2_id = 32
api_url = "https://api.start.gg/gql/alpha"
#TODO merge all instances of this into an import
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
    else:
        print(response.status_code)
        print(response.text)
        exit()
#returns just the Startgg internal ID for an event using the url
def GetEventID(trn):
	with urllib.request.urlopen("https://api.smash.gg/%s" % trn) as url:
		data = json.load(url)
		trn = str(data["entities"]["event"]["id"])
	return(trn)
#retrieve startgg phases with the url
def PhasesBySlug(slug):
    query = """query PhasesBySlug
    {{
        tournament(slug: "{slug}")
        {{
            id
            events
            {{
                id
                name
                phaseGroups
                {{
                    displayIdentifier
					standings(query: {{ perPage:100 }})
                    {{
                        nodes
                        {{
                            entrant
                            {{
                                participants
                                {{
                                    gamerTag
                                    requiredConnections
                                    {{
                                        externalUsername
                                        type
                                    }}
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        }}
    }}""".format(slug = slug)
    return make_query(query)
#retrieve entrants and their descriminators with event ID, usually from GetEventID
def ParseEntrants(page, perPage, eventId):
		query = """query EventEntrants
		{{
			event(id: {eventId})
			{{
				id
				name
				phaseGroups
				{{
					displayIdentifier
					standings(query: {{ perPage:{perPage}}})
					{{
						nodes
						{{
							entrant
							{{
								participants
								{{
									user {{
										discriminator
									}}
									gamerTag
									requiredConnections
									{{
										externalUsername
										type
									}}
								}}
							}}
						}}
					}}
				}}
			}}
		}}""".format(page = page, perPage = perPage, eventId = eventId)
		return make_query(query)
#
def seeder(mode, burl):
	os.chdir('./data')
	players = {}
	playersInBracket = {}
	playerNamesStartgg = {}

	#optionally switch to only using very recent rankings for players (important for older games)
	#TODO make this an argument switch after making the trueskill rater generate both on each run
	with open("trueskillrankings.csv", 'r', encoding='latin-1') as e:
	#with open("tschallonge.csv", 'r', encoding='latin-1') as e:
		for line in e:
			data = line[:-1].split(",")
			players[data[0]] = float(data[3])
	if mode == "-s":
		try:
			url = burl
			url = url[url.index("tournament"):]
			chop = url.split("/")
			#TODO make sure URLs are input in the form of tournament/X/event/Y
			if len(chop) < 3:
				url = "%s/%s" % (chop[0], chop[1])
			else:
				if chop[2] == "event":
					url = "%s/%s/%s/%s" % (chop[0], chop[1], chop[2], chop[3])
				else:
					url = "%s/%s" % (chop[0], chop[1])
			print(url)
			eventid = GetEventID(url)
			print(eventid)
		except Exception as err:
			print("Give a valid startgg url for your tournament like https://www.start.gg/tournament/mix-masters-online-3-1")
			print(f"Unexpected {err=}, {type(err)=}")
			quit()
		result = ParseEntrants(1,100,eventid).json()
		#result = PhasesBySlug(url).json()
		#doesn't matter unless troubleshooting bad json data
		s = open("phasesbyslug.txt", 'w', encoding='utf-8')
		s.write(str(result))
		s.close()
		entries = []
		pools = []
		if True:
			for phaseGroup in result["data"]["event"]["phaseGroups"]:
				identifier = phaseGroup["displayIdentifier"]
				temp = []
				for entrant in phaseGroup["standings"]["nodes"]:
					if entrant["entrant"] is not None:
						if entrant["entrant"]["participants"][0]["user"] is not None:
							entries.append(entrant["entrant"]["participants"][0]["user"]["discriminator"])
						else:
							break
						disc = ""
						temp.append([disc, entrant["entrant"]["participants"][0]["gamerTag"]])
						pools.append([identifier, temp])
			s = open("seeding.txt", 'w', encoding='utf-8')
			i = 0
			for entry in entries:
				if entry in playerNamesStartgg:
					entry = playerNamesStartgg[entry]
				if entry in players.keys():
					playersInBracket[entry] = players[entry]
				else:
					playersInBracket[entry] = 1
			playersInBracket = sorted(playersInBracket.items(), key=lambda playersInBracket:playersInBracket[1], reverse=True)
			print(len(playersInBracket))
			for key in playersInBracket:
				i += 1
				s.write("%s\n" % str(key[0]))
				print("%s" % str(key[0]))
			s.close()
		os.chdir("../")
		#if error is thrown on opening input file put it in data/ folder but don't include data/ when specifying file name
	elif mode == "-paperbracketmode":
		i = open(burl, 'r')
		s = open("seeding.txt", 'w', encoding='utf-8')
		for entry in i:
			entry = nameCleaning(entry)#dirty inputs are dirty
			if entry in playerNamesChallonge:
				entry = playerNamesChallonge[entry]
			if entry in playerNamesStartgg:
				entry = playerNamesStartgg[entry]
			if entry in players.keys():
				playersInBracket[entry] = players[entry]
			else:
				playersInBracket[entry] = 1
		playersInBracket = sorted(playersInBracket.items(), key=lambda playersInBracket:playersInBracket[1], reverse=True)
		print(len(playersInBracket))
		top24 = 0
		for key in playersInBracket:
			top24 = top24 + 1
			s.write("%s\n" % str(key[0]))
			#s.write("%s,%s\n" % (str(key[0]), str(key[1])))
			print("%s,%s" % (str(key[0]), str(key[1])))
			if(top24 == 32):
				s.write("Top 32 Cut Off------------------\n")
				print("--------------------\n")
			if(top24 == 24):
				s.write("Top 24 Cut Off------------------\n")
				print("--------------------\n")
		s.close()
		i.close()
		os.chdir("../")
#TODO remove when GUI remake is done to call seeder
seeder("-s", "https://www.start.gg/tournament/sf6-game-realms-7-14/event/street-fighter-6")