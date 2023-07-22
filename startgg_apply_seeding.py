import csv, os, json, sys, codecs, requests, json
import urllib.request as urllib2
from graphqlclient import GraphQLClient
import SPO_functions as SPO
## Make sure to run `pip install graphqlclient`
#read config.txt for required API credntials or throw an error


#Change our current seed file into one that contains their seed ID and is ordered
players = {}
playerNamesStartgg = {}
def nameCleaning(name):
	name = name.lower()
	i = name.rfind("|")
	if i > 0:
		i = i + 1
		ugh = len(name) + 1
		name = name[i:]
	#very specific exception for a name that breaks all kinds of things
	gh = name.find("gh")
	ebu = name.find("ebu")
	if gh > 0 and ebu > 0:
		name = "nebu"
	name = name.replace("'","")
	name = name.replace("\"","")
	name = name.replace("\n","")
	name = name.strip(" ")
	return name
def PhaseSeedbyPhaseID(page, perPage, phaseId):
		query = """query PhaseSeeding
		{{
			phase(id:{phaseId})
			{{
				id
				seeds(query: {{ perPage:{perPage}}})
				{{
					nodes 
					{{
						id
						entrant 
						{{
							participants 
							{{
								gamerTag
							}}
						}}
					}}
				}}
			}}
		}}""".format(page = page, perPage = perPage, phaseId = phaseId)
		return make_query(query)

def applySeed(tourneyID, sggGameID, skey):
	os.chdir('./data')
	with open("names.csv",'r', encoding='UTF-8') as data_file:
		for line in data_file:
			data = line[:-1].split(",")
			if not len(data) == 3:
				continue
			playerNamesStartgg[data[1]] = data[2]
	# with open("MMentrants.csv",'r', encoding='latin-1') as data_file:
	# 	for line in data_file:
	# 		data = line[:-1].split(",")
	# 		if data[0] == "Seed ID":
	# 			continue
	# 		data[0] = data[0].strip()
	# 		data[1] = data[1].strip()
	# 		data[1] = nameCleaning(data[1])
	# 		if data[1] in playerNamesStartgg:
	# 			data[1] = playerNamesStartgg[data[1]]
	# 			players[data[1]] = data[0]
	# 			print("Found a player")
	# 		else:
	# 			players[data[1]] = data[0]
	# 		print("%s,%s" % (data[1], players[data[1]]))
	result = PhaseSeedbyPhaseID(1,100,tourneyID).json()
	for id in result["data"]["phase"]["seeds"]["nodes"]:
		shortgamertag = id["entrant"]["participants"][0]["gamerTag"]
		seedidnum = id["id"]
		print(str(seedidnum) + shortgamertag)
		shortgamertag = nameCleaning(shortgamertag)
		if shortgamertag in playerNamesStartgg:
			shortgamertag = playerNamesStartgg[shortgamertag]
			players[shortgamertag] = seedidnum
			print("Found a translated name to correct")
		else:
			players[shortgamertag] = seedidnum
	seednum = 1
	seedcsv = open("seeding.csv", 'w', encoding='UTF-8')
	seedcsv.write("seedId,seedNum\n")
	with open("seeding.txt", 'r', encoding='UTF-8') as s:
		for line in s:
			data = line.rstrip()
			print("%i,%s" %(seednum, players[data]))
			seedcsv.write("%s,%i\n"%(players[data], seednum))
			seednum += 1
	seedcsv.close()
	seedMapping = []
	with open("seeding.csv",'r', encoding='UTF-8') as data_file:
		for line in data_file:
			data = line[:-1].split(",")
			if data[0] == "seedId" : # skip the header row
				continue
			seedId = data[0] # check your columns!
			seedNum = data[1] # check your columns!
			seedMapping.append({
				"seedId": seedId,
				"seedNum": seedNum,
			})
	numSeeds = len(seedMapping)
	print("Importing " + str(numSeeds) + " seeds to phase " + str(tourneyID) + "...")
	client = GraphQLClient('https://api.start.gg/gql/' + apiVersion)
	client.inject_token('Bearer ' + authToken)
	result = client.execute('''
	mutation UpdatePhaseSeeding ($phaseId: ID!, $seedMapping: [UpdatePhaseSeedInfo]!) {
	updatePhaseSeeding (phaseId: $phaseId, seedMapping: $seedMapping) {
		id
	}
	}
	''',
	{
		"phaseId": tourneyID,
		"seedMapping": seedMapping,
	})
	resData = json.loads(result)
	if 'errors' in resData:
		print('Error:')
		print(resData['errors'])
	else:
		print('Success!')
	os.chdir("../")
# test = PhaseSeedbyPhaseID(1,100,1387701).json()
# for id in test["data"]["phase"]["seeds"]["nodes"]:
# 	shortgamertag = id["entrant"]["participants"][0]["gamerTag"]
# 	seedidnum = id["id"]
# 	print(str(seedidnum) + shortgamertag)