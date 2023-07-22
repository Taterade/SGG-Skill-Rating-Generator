import challonge #challonge python integration from ZEDGR: https://github.com/ZEDGR/pychallonge
import time, logging
import SPO_functions as SPO
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



#returns just the Startgg internal ID for an event using the url
def GetEventID(trn):
	with urllib.request.urlopen("https://api.smash.gg/%s" % trn) as url:
		data = json.load(url)
		trn = str(data["entities"]["event"]["id"])
	return(trn)
#retrieve startgg phases with the url
def PhasesBySlug(slug, skey):
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
    return SPO.make_query(query, skey)
#retrieve entrants and their descriminators with event ID, usually from GetEventID
def ParseEntrants(page, perPage, eventId, skey):
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
		return SPO.make_query(query, skey)
#
def seeder(mode, burl, sggGameID, skey):
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
		result = ParseEntrants(1,100,eventid, skey).json()
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
				sname = SPO.getPlayerName("\"user/" + key[0] + "\"", skey)
				s.write("%s\n" % str(key[0]))
				print("%s,%s" % (str(key[0]),sname))
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
