import csv, logging
import os, requests, json
from trueskill import Rating, quality_1vs1, rate_1vs1
from ratelimit import limits, RateLimitException
from backoff import on_exception, expo
import SPO_functions as SPO
logging.basicConfig(filename='startgg_scrubber.log', encoding='utf-8', level=logging.DEBUG)

#does what it says, retrieve a player's name based on their startgg user slug
knownNames = {}
def processnames(sggGameID, skey): 
	#TODO open the names.csv file, if it doesn't exist make one and open that
	#also read all existing discriminator and name pairings into key array
	os.makedirs("data", exist_ok = True)
	os.chdir('./data')
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
			result = SPO.getPlayerName("\"user/" + data[0] + "\"",skey)
			if result == "None":
				continue
			else:
				e.write(data[0] + "," + result + "\n")
				logging.debug("added " + data[0] + "," + result + " to the names.csv write operations")
	e.close()
	f.close()
	print("All names retrieved")
	os.chdir('../')
