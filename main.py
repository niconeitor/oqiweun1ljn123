import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
import os
import time
import psycopg2
import face_recognition
import cv2
import random
import psutil
import subprocess
try:
    conn = psycopg2.connect(host="localhost",dbname="salsia", user="postgres", password="nicolas_asdf1", port="5432")
    print("Conexión exitosa")
except Exception as ex:
    print(f"Error de conexión a la base de datos: {ex}")
    

load_dotenv("credentials.env")
# Variables de acceso desde el entorno
client_id = os.getenv('SPOTIPY_CLIENT_ID')
client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')

# Configuración de Spotipy 

scope = "playlist-read-private user-modify-playback-state playlist-read-collaborative user-read-currently-playing user-read-playback-state" #Se ajusta según necesario
def create_spotify():
    sp_oauth = SpotifyOAuth(client_id=client_id,
                            client_secret=client_secret,
                            redirect_uri=redirect_uri,
                            scope=scope)
    spotify = spotipy.Spotify(auth_manager=sp_oauth)
    return sp_oauth, spotify

def refresh_spotify(auth_manager, spotify):
    token_info = auth_manager.cache_handler.get_cached_token()
    if auth_manager.is_token_expired(token_info):
        auth_manager, spotify = create_spotify()
    return auth_manager, spotify

def add_song_to_queue_if_genre_matches(sp):
    """
    This function searches for a song by name, checks its genre, and adds it to the queue if it matches.
    Busca una canción por su nombre, chequea su genero y agrega la lista de reproducción actual solamente si tiene al menos uno de los generos en la lista
    """
    song_name = input("Ingrese el nombre de la cancion: ")
    results = sp.search(q=song_name, limit=1)
    if results['tracks']['items']:  # Chequea si se encontro una canción
        track = results['tracks']['items'][0]
        track_uri = track['uri']

        artist_id = track['artists'][0]['id']
        artist = sp.artist(artist_id)
        
        genres_to_match = ['salsa', 'samba', 'tango']
        if any(genre in artist['genres'] for genre in genres_to_match):
            print(f"Adding {track['name']} by {track['artists'][0]['name']} to queue")
            sp.add_to_queue(track_uri)
        else:
            print(f"{track['name']} by {track['artists'][0]['name']} no coincide con ningún genero")
    else:
        print("NO se encontraron canciones con ese nombre.")

def is_spotify_running():
  """
  Chequea si el proceso "Spotify.exe" esta corriendo.
  """
  for process in psutil.process_iter():
    if process.name() == "Spotify.exe":
      return True
  return False

def open_spotify_if_not_running():
  """
  Abre Spotify si no esta abierto
  """
  if not is_spotify_running():
    spotify_path = r"C:\Users\Nico\Desktop\spotify.lnk"  #REEMPLAZAR CON LA UBICACIÓN DE TU SPOTIFY.LNK HAGAN UN ACCESO DIRECTO AL ESCRITORIO!!!
    subprocess.Popen([spotify_path], shell=True)  # Abrir spotify


def check_and_play_first_playlist(spotify):
    """
    Revisa si Spotify esta reproduciendo alguna música.
    Si no, empieza a reproducir la primera lista de reproducción del usuario.
    
    Args:
        spotify: un objeto spotify autorizado por el usuario de la cuenta.
    """
    try:
        # Check if something is currently playing
        current_track = spotify.current_user_playing_track()
        if current_track is None or not current_track['is_playing']:
            # No music is playing, get user's playlists
            playlists = spotify.user_playlists(user=spotify.current_user()["id"])
            if playlists["items"]:  # Check if there are any playlists
                first_playlist_id = playlists["items"][0]["id"]
                # Start playing the first playlist
                for _ in range(5):  # Try 5 times to find an active device
                    devices = spotify.devices()
                    if devices['devices']:
                        device_id = devices['devices'][0]['id']
                        spotify.start_playback(device_id=device_id, context_uri=f"spotify:playlist:{first_playlist_id}")
                        print("No hay música reproduciéndose. Reproduciendo la primera lista.")
                        break
                    else:
                        print("Dispositivo no encontrado. Reintentando en 5 segundos...")
                        time.sleep(5)
                else:
                    print("Falló en encontrar un dispositivo despues de 5 intentos, cerrando.")
        else:
            print("Ya hay música reproduciéndose.")
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 429:
            retry_after = int(e.headers.get('Retry-After', 1))
            print(f"Tasa límite excedida. Intentando despues de {retry_after} segundos.")
            time.sleep(retry_after)
            check_and_play_first_playlist(spotify)
        else:
            print(f"Spotify API error: {e}")

def resume_playback_if_paused(spotify):
    try:
        current_playback = spotify.current_playback()
        if current_playback and not current_playback['is_playing'] and current_playback['item']:
            spotify.start_playback()
            print("Música pausada. Resumiendo música.")
        elif current_playback is None:
            check_and_play_first_playlist(spotify)
    except spotipy.exceptions.SpotifyException as e:
        print(f"Spotify API error: {e}")





if __name__ == '__main__':
    auth_manager, spotify = create_spotify()
    playlist_started = False

    while True:
        auth_manager, spotify = refresh_spotify(auth_manager, spotify)
        
        if not is_spotify_running():
            print("Spotify no está abierto. Abierto Spotify y reproduciendo la primera lista de musica...")
            open_spotify_if_not_running()
            time.sleep(5)
            playlist_started = False  # Esta bandera se resetea, ya que si spotify no estaba abierto, no habia música reproduciéndose

        if not playlist_started:
            current_playback = spotify.current_playback()
            if current_playback is None or not current_playback['is_playing']:
                check_and_play_first_playlist(spotify)


        current_playback = spotify.current_playback()
        if current_playback and current_playback['is_playing']:
            add_song_to_queue_if_genre_matches(spotify)
        
        time.sleep(10)  # Tiempo entre loop, será borrado mas adelante
