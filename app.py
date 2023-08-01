from flask import Flask, request, redirect, session, render_template, jsonify
import random
import requests
from requests import post,get
import os
import urllib.parse
from dotenv import load_dotenv
import json
load_dotenv()
app = Flask(__name__, static_url_path='/static')


app.secret_key = str(random.randint(0,10000000))

# Replace with your credentials
client_id = os.getenv("SPOTIPY_CLIENT_ID")
client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")
scope = 'user-read-private user-top-read user-read-email playlist-read-private playlist-modify-private user-read-currently-playing user-read-playback-state streaming user-modify-playback-state playlist-modify-public'


#User functions
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


#Outputs top songs of artist
def listSongs(token, name):
    artist_id = search_for_artist(token, name)['id'] #Get Id of artist based on name
    top_tracks = get_songs_by_artist(token, artist_id)
    return list(map(lambda x:x['name'], top_tracks))



def getPlayLists(token):
    
    url = "https://api.spotify.com/v1/me/playlists?"
    headers = get_auth_header(token)
    result = get(url,headers=headers)
    json_result = json.loads(result.content)['items']

    playlists = list(map(lambda x:[x['name'], x['images'][0]["url"], x['id']], json_result)) #parse into list of important values (name, image, id)
    

    
    return playlists


def getCurrentlyPlaying(token):
    url = "https://api.spotify.com/v1/me/player/currently-playing"
    headers = get_auth_header(token)
    result = get(url,  headers=headers)
    
    #String to display track info
    output_string = ""
    
    #valid response
    if result.status_code == 200:
        json_result = json.loads(result.content)['item']
        
        #Change the value of the index to control image size
        
        image_url = json_result['album']['images'][1]['url']

        #Get list of contributing artist
        artists = list(map(lambda x:x['name'], json_result['artists']))
        artist_string = ""

        for x, artist in enumerate(artists):
            if x!= len(artists)-1:
                artist_string+=artist + ", "
            else:
                artist_string+=artist 

        output_string = ([json_result['name'], artist_string, image_url])
        
       


    #invalid response
    else:
        output_string = ["No Song Currently Playing", "",""]

    return output_string

    

#Return : List of ID's
def getUserTopTracks(token, term, limit):

    t = ""
    if term == 0:
        t = "short_term"
    if term == 1:
        t = "medium_term"
    if term == 2:
        t = "long_term"

    url = f'https://api.spotify.com/v1/me/top/tracks?time_range={t}&limit={limit}'
    headers = get_auth_header(token)
    result = get(url,  headers=headers)
    json_result = json.loads(result.content)['items']

    track_ids = []
    for i in range(0, limit):
        track_ids.append(json_result[i]['id'])


    return track_ids


#Input: token, list of track ids
#Output: list of list [name, artist, album image, uri]
def getUserRecs(token,track_ids):
  
    s= ""
    for x, id in enumerate(track_ids):
        if x!=len(track_ids)-1:
            s+= id +","
        else:
            s+=id

    url = f'https://api.spotify.com/v1/recommendations?limit=5&seed_genres=k-pop&seed_tracks={s}'
    headers = get_auth_header(token)
    result = get(url,  headers=headers)
    json_result = json.loads(result.content)['tracks']

    recs = (list(map(lambda x: [x['name'], x['artists'][0]['name'], x['album']['images'][0]['url'], x['uri']], json_result)))
  

    return recs


#Get list of URI to put in a playlist
def getTopTrackURI(token, term, limit):

    t = ""
    if term == 0:
        t = "short_term"
    if term == 1:
        t = "medium_term"
    if term == 2:
        t = "long_term"

    url = f'https://api.spotify.com/v1/me/top/tracks?time_range={t}&limit={limit}'
    headers = get_auth_header(token)
    result = get(url,  headers=headers)
    json_result = json.loads(result.content)['items']

    track_uris = []
    for i in range(0, limit):
        track_uris.append(json_result[i]['uri'])


    return track_uris



def createPlaylists(token):

    
    headers = get_auth_header(token)
    user_info_response = requests.get('https://api.spotify.com/v1/me', headers=headers)
    user_id = user_info_response.json()['id']
    create_playlist_url = f'https://api.spotify.com/v1/users/{user_id}/playlists'
   
    data = {
        'name': "Outify Wrapped 2023",
        'description': "Your top 50 songs of 2023",
        'public': False
    }
   
    response = requests.post(create_playlist_url, headers=headers, json=data)
    if response.status_code == 201:
        print("Yay")
    else:
        print("NO")

    print(response.json()['id'])
    print(response.json()['href'])
    return response.json()['id']



def addToPlaylist(token, uris, playlist_id):


 
    


    headers = get_auth_header(token)

    nurl = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
  
    data = {
        "uris": uris,
        "position" : 0

    }

    response = requests.post(nurl, headers=headers, json=data)

    if response.status_code == 201:
        print("Yay")
    else:
        print("NO")





########
#ROUTES#
########


# Step 1: Get the authorization URL
auth_url = f'https://accounts.spotify.com/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&scope={scope}'

@app.route('/')
def index():
    
    # Open the authorization URL in the user's default web browser
    if 'access_token' in session:    
        return redirect('/user')
    

    else:
        return redirect('/welcome')
  

@app.route('/welcome')
def welcome():
    return render_template('index.html', auth_url = auth_url)

@app.route('/callback')
def callback():
    # Step 2: Exchange the authorization code for an access token
    code = request.args.get('code')
    



    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'client_secret': client_secret
    }
    response = requests.post('https://accounts.spotify.com/api/token', data=payload)
    access_token = response.json()['access_token']
    session['access_token'] = access_token



    # Step 3: Use the access token to get the user's information
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    user_info_response = requests.get('https://api.spotify.com/v1/me', headers=headers)
    user_info = user_info_response.json()

    # Step 4: Print the user's username
    return redirect('/user')


@app.route('/logout')
def logout():
    spotify_logout_uri = 'www.google.com'
    logout_url = f'https://accounts.spotify.com/en/logout?continue={urllib.parse.quote(spotify_logout_uri)}'
    session.clear()
    return redirect('/')

@app.route('/get_current_song')
def get_current_song():
    access_token = session.get('access_token')
    if access_token:
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get('https://api.spotify.com/v1/me/player/currently-playing', headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get('is_playing'):
            
                return jsonify(data['item'])  # Return the current song data
 
    return jsonify({})  # If no song is playing or error occurred, return an empty object



@app.route('/user')
def user():
    if 'access_token' not in session:
        
        return redirect('/')
    

    token = session['access_token']
   
    # Use the access token to get the user's information
    headers = {
        'Authorization': f'Bearer {session["access_token"]}'
    }
    user_info_response = requests.get('https://api.spotify.com/v1/me', headers=headers)
    
    # If the access token is invalid, clear the session and redirect to the login page
    if user_info_response.status_code == 401:  # Unauthorized
        session.clear()
        return redirect('/')

    user_info = user_info_response.json()
    
    #Get recs from user top 4 (short_term)
    track_ids = getUserTopTracks(token,0, 4)
    recs = getUserRecs(token, track_ids)

    playlist_id = createPlaylists(token)
    topTracksURIS = (getTopTrackURI(token, 1, 50))
    addToPlaylist(token, topTracksURIS, playlist_id)
    
    return render_template("dash.html",username = f"{user_info['display_name']}",
                           email = user_info['email'], playlists = json.dumps(getPlayLists(token)),
                           playbackStatus = getCurrentlyPlaying(token),
                           access_token = token,
                           recs = recs)





if __name__ == '__main__':
    app.run()
