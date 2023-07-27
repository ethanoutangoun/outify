import os
from dotenv import load_dotenv
load_dotenv()


import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Set up authentication
scope = ['user-top-read', 'user-read-recently-played'] # Define the scope of permissions needed
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

def get_user_top_tracks(limit=10):
    results = sp.current_user_top_tracks(limit=limit, time_range='medium_term')
    return results['items']


def suggest_songs():
    top_tracks = get_user_top_tracks()
    suggested_songs = []

    for track in top_tracks:
        # Use the track or artist details to get recommended tracks
        # Example: recommended_tracks = sp.recommendations(seed_tracks=[track['id']], limit=5)

        # For simplicity, we'll just add the track name to the suggested songs list
        
        suggested_songs.append(track['name'])

    return suggested_songs





#Playground
def main():
    tracks = get_user_top_tracks()
    for track in tracks:
        print(track['name'] + " : " + track['artists'][0]['name'])

    
    temp = sp.current_user_recently_played(limit=50, after=None, before=None)
    #print(temp['name'])

    print(temp['items'])







if __name__ == "__main__":
    main()
  