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
scope = 'user-read-private user-top-read user-read-email playlist-read-private user-read-currently-playing'


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


#Outputs a list of songs
def listSongs(name):
    token = session['access_token']
    artist_id = search_for_artist(token, name)['id'] #Get Id of artist based on name
    top_tracks = get_songs_by_artist(token, artist_id)
    return list(map(lambda x:x['name'], top_tracks))



def getPlayLists(token):
    
    url = "https://api.spotify.com/v1/me/playlists?"
    headers = get_auth_header(token)
    result = get(url,headers=headers)
    json_result = json.loads(result.content)['items']
    playlists = list(map(lambda x:[x['name'], x['images'][0]["url"]], json_result))
    
  
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
        
        image_url = json_result['album']['images'][0]['url']

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

@app.route('/user')
def user():
    if 'access_token' not in session:
        
        return redirect('/')
    
   
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
    
    
    
    return render_template("dash.html",username = f"{user_info['display_name']}",
                           email = user_info['email'], playlists = json.dumps(getPlayLists(session['access_token'])),
                           playbackStatus = getCurrentlyPlaying(session['access_token']),
                           access_token = session['access_token'])



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



if __name__ == '__main__':
    app.run()
