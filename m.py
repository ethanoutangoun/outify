from dotenv import load_dotenv
import os
import base64
import json
from requests import post,get
import spotipy
from spotipy.oauth2 import SpotifyOAuth
load_dotenv()

#Set up authentication
scope = ['user-top-read', 'user-read-recently-played'] # Define the scope of permissions needed
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

#Pull in local environment variables
client_id = os.getenv("SPOTIPY_CLIENT_ID")
client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
client_redirect = os.getenv("SPOTIPY_REDIRECT_URI")


def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization" : "Basic " + auth_base64,
        "Content-Type" : "application/x-www-form-urlencoded" 
    }
    data = {"grant_type" : "client_credentials"}
    result = post(url, headers = headers, data = data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token


def get_auth_header(token):
    return {"Authorization" : "Bearer " + token}


def search_for_artist(token, artist_name):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"q={artist_name}&type=artist&limit=1"

    query_url = url + "?" + query
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)['artists']['items']
    if len(json_result) == 0:
        print("No Artist with this name exists")
        return None
    
    return json_result[0]


def get_songs_by_artist(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?market=US"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)['tracks']
    return json_result


#Outputs a list of songs
def listSongs(name):
    token = get_token()
    artist_id = search_for_artist(token, name)['id'] #Get Id of artist based on name
    top_tracks = get_songs_by_artist(token, artist_id)
    return list(map(lambda x:x['name'], top_tracks))


def getProfile(token):
    url = "https://api.spotify.com/v1/me"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)
    print(json_result)


token = get_token()
getProfile(token)



