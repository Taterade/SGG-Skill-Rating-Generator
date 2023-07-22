import requests, json
from ratelimit import limits, RateLimitException
from backoff import on_exception, expo
apiVersion = 'alpha'
api_url = "https://api.start.gg/gql/alpha"
@on_exception(expo, Exception, max_time=61)
@limits(calls=80, period=61)
def make_query(query, auth_token):
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
def getPlayerName(slug, skey):
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
	result = make_query(query, skey).json()
	if result["data"]["user"] == None:
		return "None"
	else:
		return result["data"]["user"]["player"]["gamerTag"]