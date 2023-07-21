import requests
import json
import os
import logging
from ratelimit import limits, RateLimitException
from backoff import on_exception, expo
#entire script is a function to account for a future GUI calling it
def startggscrub():
	logging.basicConfig(filename='startgg_scrubber.log', encoding='utf-8', level=logging.DEBUG)
	#read config.txt for required API credntials or throw an error while generating the file
	#TODO replace this with variables being passed from main thread when called
	try:
		with open("config.txt", "r") as config:
			for line in config:
				name, var = line.partition("=")[::2]
				var.strip()
				#TODO switch this for just raw mapping key=value pairs instead of if statments and ignore comment lines in the file
				if name == "challongeid":
					cid = var
					cid = cid.rstrip()
				elif name == "challongekey":
					ckey = var
					ckey = ckey.rstrip()
				elif name == "startggkey":
					skey = var
					skey = skey.rstrip()
				#TODO rename these variables and all instances of them to not be SG specific
				elif name == "gameid":
					sg_id = var
					sg_id = sg_id.rstrip()
					sg2_id = sg_id
		#sanity check startgg key because it is the only value neccesary
		if len(skey) < 3:
			raise Exception()
	#TODO replace the string write with an default file copy
	#On any failure of reading the file recreates it. Change this to non destructive so edge cases
	#can fix it manually without retreiving API keys again
	except:
		try:
			f=open("config.txt", "x")
			f.write("challongeid=\nchallongekey=\nstarggid=\nstartggkey=\ngameid=")
			f.close()
		except:
			exit
		sys.exit("config.txt error, enter your challonge and startgg credentials into the generated file")
	#Store startgg key in a better named variable
	auth_token = skey

	#Start gg api url, possible updates in the future
	api_url = "https://api.start.gg/gql/alpha"
	os.makedirs("data", exist_ok = True)
	os.chdir('./data')
	#TODO also swap based on current game sggid so multiple games can be 
	# tracked in their own directory

	#TODO make this repeat a query automatically up to 
	# 5 times on 503 to account for server API errors.
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

	#Query for getting all tournaments of a specified game
	def TournamentsByVideogame(page, perPage, gameId):
		query = """query TournamentsByVideogame {{
			tournaments(query:
			{{
				perPage: {perPage}
				page: {page}
				filter:
				{{
					past: true
					videogameIds: [
					{gameId}
					]
				}}
			}}
			)
			{{
				nodes
				{{
					events(
						filter:
						{{
							videogameId: [{gameId}]
							published: true
						}}
					)
					{{
						id
					}}
					name
				}}
			}}
		}}
		""".format(page = page, perPage = perPage, gameId = gameId)
		return make_query(query)

	#Query that requests all sets in a tournament
	def ParseSets(page, perPage, eventId):
		query = """query EventSets
		{{
			event(id: {eventId})
			{{
				sets(
					perPage: {perPage}
					page: {page}
					sortType: ROUND
				){{
					nodes
					{{
						id
						state
						completedAt
						winnerId
						totalGames
						slots
						{{
							entrant
							{{
								id
								name
								participants
								{{
									gamerTag
									user 
									{{
										discriminator
									}}
								}}
							}}
						}}
						winnerId
					}}
				}}
			}}
		}}""".format(page = page, perPage = perPage, eventId = eventId)
		return make_query(query)


	print("--- Starting start.gg Scrubber ---")
	print("checking for already scrubbed data")
	scrubbedIds = []
	#Open already read tournaments or create the file for it.
	try:
		ft = open("startgg_tourney.txt", "r", encoding="utf-8")
		for event in ft:
			scrubbedIds.append(event.split(",")[0])
		ft.close()
	except FileNotFoundError:
		print("No tourney history, building a new archive.")
		ft = open("startgg_tourney.txt", "w", encoding="utf-8")
		ft.close()
	print(str(len(scrubbedIds)) + " events already accounted for")

	print("checking start.gg for new data")
	eventIds = []
	cont = True
	count = 1
	while cont:
		result = TournamentsByVideogame(count, 100, sg2_id)
		count += 1

		if "data" in result.text:
			if result.json()["data"]["tournaments"]["nodes"]:
				for item in result.json()["data"]["tournaments"]["nodes"]:
					if item["events"] != []:
						for event in item["events"]:
							if str(event["id"]) not in scrubbedIds:
								print("Found: " + str(item["name"]) + " Event ID: " + str(event["id"]))
								eventIds.append([event["id"], item["name"]])
							else:
								cont = False

			else:
				cont = False
		else:
			cont = False

	print(str(len(eventIds)) + " events found")
	#TODO change this to a logging level check to prevent log file bloat
	logging.debug(str(len(eventIds)) + " events found")
	if len(eventIds) == 0:
		os.chdir("../")
		return()
	print("\n--- Iterating Through Event Ids ---")

	ft = open("startgg_tourney.txt", "a", encoding="utf-8")
	fm = open("startgg_matches.txt", "a", encoding="utf-8")
	for eventId in reversed(eventIds):
		count = 0
		match_count = 0
		cont = True
		while cont:
			cont = False
			try:
				count += 1
				result = ParseSets(count, 100, eventId[0])
			except:
				print("Failed to parse sets from " + str(eventId[0]))
				logging.error("Failed to parse sets from " + str(eventId[0]))
				cont = True
				break


			if "data" in result.text:
				if result.json()["data"]["event"]["sets"] != "null":
					for match in result.json()["data"]["event"]["sets"]["nodes"]:
						if match["state"] == 3 and match["totalGames"] != 0 and len(match["slots"]) == 2:
							try:
								p1 = match["slots"][0]["entrant"]["participants"][0]["user"]["discriminator"]
							except:
								p1 = "None"
							try:
								p2 = match["slots"][1]["entrant"]["participants"][0]["user"]["discriminator"]
							except:
								p2 = "None"
							if match["winnerId"] == match["slots"][0]["entrant"]["id"]:
								fm.write(str(match["completedAt"]) + "," + p1 + "," + p2 + "," + str(eventId[0]) + "," + eventId[1] + "\n")
								match_count += 1
							else:
								fm.write(str(match["completedAt"]) + "," + p2 + "," + p1 + "," + str(eventId[0]) + "," + eventId[1] + "\n")
								match_count += 1
							cont = True
		#After succesful match parse add the tournament to storage to be skipped in the future.
		ft.write(str(eventId[0]) + "," + eventId[1] + "," + str(match_count) + "\n")
		print("Found: " + str(match_count) + " matches for: " + eventId[1] + " Event Id: " + str(eventId[0]))
		logging.debug("Found: " + str(match_count) + " matches for: " + eventId[1] + " Event Id: " + str(eventId[0]))
	fm.close()
	ft.close()
	os.chdir("../")
	print("Finished iterating through matches")
	return()