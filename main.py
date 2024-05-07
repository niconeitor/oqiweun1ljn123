import spotipy
from spotipy.oauth2 import SpotifyOAuth


sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="fbf2eaabfd1947f698f3e8e75b32b53b",
    client_secret="8e45d169e24547c7b88f8fc0c4e3284c",
    redirect_uri="http://127.0.0.1:8000/callback",
    scope="user-library-read playlist-modify-public playlist-read-private playlist-modify-private user-modify-playback-state user-modify-playback-state"
))

# salsa
# samba


def add_song_to_queue_if_genre_matches(song_name):
    results = sp.search(q=song_name, limit=1)
    track = results['tracks']['items'][0]
    track_uri = track['uri']

    artist_id = track['artists'][0]['id']
    artist = sp.artist(artist_id)

    genres_to_match = ['salsa', 'samba', 'tango']
    if any(genre in artist['genres'] for genre in genres_to_match):
        print(
            f"Adding {track['name']} by {track['artists'][0]['name']} to queue")
        sp.add_to_queue(track_uri)
    else:
        print(
            f"{track['name']} by {track['artists'][0]['name']} does not match any genre")


cancion = input("Ingrese el nombre de la cancion: ")
add_song_to_queue_if_genre_matches(cancion)
