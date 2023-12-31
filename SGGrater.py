import os, sys
import tkinter as tk
import startgg_scrubber as gg
import namestorage as nm
import startgg_apply_seeding as seed
import trueskill_rating_generator as tsr
import seedgenerator as sg
#read config.txt for required API credntials or throw an error while generating the file
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
		if os.path.isfile("config.txt"):
			exit("Error reading config.txt, either remake the file using default.txt template or delete to allow program to auto remake it.")
		else:
			f=open("config.txt", "x")
			f.write("challongeid=\nchallongekey=\nstarggid=\nstartggkey=\ngameid=")
			f.close()
	except:
		exit("Config file read error and config file generation error")
	exit("config.txt error, enter your challonge and startgg credentials into the generated file")
auth_token = skey
window = tk.Tk()
window.title("Spiritual Phenomena Observatory")
bracketurl = ""
bracketid = ""


startggbtn= tk.Button(
		text="Update matches from StartGG",
		fg="yellow",
		bg="black"
		)
startggbtn.pack()
ratingbtn= tk.Button(
		text="Generate Trueskill Ratings",
		fg="yellow",
		bg="black"
		)
ratingbtn.pack()
nameMergebtn= tk.Button(
		text="Retrieve display names for Descriminators",
		fg="yellow",
		bg="black"
		)
nameMergebtn.pack()
seedbtn= tk.Button(
		text="Generate Seed Order in Seeding.txt",
		fg="yellow",
		bg="black"
		)
seedbtn.pack()
paperseed = tk.Button(
		text="Generate Seed Order from Text File",
		fg="yellow",
		bg="black"
		)
paperseed.pack()
seedapplybtn = tk.Button(
		text="API seed a startgg bracket",
		fg="yellow",
		bg="black"
		)
seedapplybtn.pack()
bracketLinkLabel = tk.Label(text="Bracket URL Link")
bracketLinkLabel.pack()
bracketURLEntry = tk.Entry()
bracketURLEntry.pack()
bracketIDLabel = tk.Label(text="Bracket Seeding ID")
bracketIDLabel.pack()
bracketIDEntry = tk.Entry()
bracketIDEntry.pack()
startGGBracket = bracketURLEntry.get()
startGGID = bracketIDEntry.pack()
def loadLog():
	try:
		o = open('bracketseeder.log', 'r')
		for line in o:
			data = line.split(",")
			bracketurl = data[0]
			bracketid = data[1]
			bracketURLEntry.insert(1, bracketurl)
			bracketIDEntry.insert(1, bracketid)
			print("Loaded UI cache")
		o.close()
	except:
		return
	return
def saveLog():
	try:
		o = open('bracketseeder.log', 'w')
		bracketurl = bracketURLEntry.get()
		bracketid = bracketIDEntry.get()
		o.write(bracketurl + "," + bracketid)
		o.close()
		print("Saved UI input cache")
		print(str(bracketurl) +","+ str(bracketid))
	except: 
		return
	return
def startggscrub_click(event):
	print("Scrubbing StartGG")
	gg.startggscrub(sg_id, skey)
def namemerge_click(event):
	print("Matching Descriminators to Names")
	nm.processnames(sg_id, skey)
def rating_click(event):
	print("Generating scores")
	tsr.tsrate()
nameMergebtn.bind("<Button-1>", namemerge_click)
startggbtn.bind("<Button-1>", startggscrub_click)
ratingbtn.bind("<Button-1>", rating_click)
def seed_click(event):
	print("Creating seed order from StartGG bracket URL")
	saveLog()
	sg.seeder("-s", bracketURLEntry.get(), sg_id, skey)
seedbtn.bind("<Button-1>", seed_click)
def paperseed_click(event):
	print("Creating seed order from provided seed input file")
	saveLog()
	sg.seeder("-paperbracketmode", "CB2023.txt", sg_id, skey)
paperseed.bind("<Button-1>", paperseed_click)
def seed_apply_click(event):
	print("Applying seed to bracket over API")
	saveLog()
	seed.applySeed(bracketIDEntry.get())
seedbtn.bind("<Button-1>", seed_click)
loadLog()
window.mainloop()