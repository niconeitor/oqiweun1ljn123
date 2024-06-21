import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

# Cargar variables de entorno desde un archivo .env
load_dotenv("credentials.env")

# Obtener las variables de entorno
client_id = os.getenv("SPOTIPY_CLIENT_ID")
client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")

if not client_id or not client_secret or not redirect_uri:
    raise Exception("Las variables de entorno SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET y SPOTIPY_REDIRECT_URI deben estar definidas")

# Configuración de Spotipy
scope = "playlist-read-private user-modify-playback-state playlist-read-collaborative user-read-currently-playing user-read-playback-state"

def create_spotify():
    sp_oauth = SpotifyOAuth(client_id=client_id,
                            client_secret=client_secret,
                            redirect_uri=redirect_uri,
                            scope=scope)
    spotify = spotipy.Spotify(auth_manager=sp_oauth)
    return sp_oauth, spotify

def refresh_spotify(auth_manager, spotify):
    try:
        token_info = auth_manager.cache_handler.get_cached_token()
    except:
        # Error por cache vacío sin token creado
        print("No hay token en el cache, necesita autorización inicial.")
        return auth_manager, spotify
    if token_info:
        if auth_manager.is_token_expired(token_info):
            auth_manager, spotify = create_spotify()
    else:
        # No cached token found (handled in try-except)
        pass
    return auth_manager, spotify

def get_first_song_name(sp, song_name):
    """
    Busca cancion y entrega el nombre entero

    Args:
        sp: The Spotipy client object.
        song_name: The name of the song to search.

    Returns:
        El nombre entero del primer resultado, None si no se encuentra cancion o da error.
    """
    try:
        results = sp.search(q=song_name, limit=1)
        if results['tracks']['items']:
            # Extract song name from the first result
            track = results['tracks']['items'][0]
            return track['name']
        else:
            return None  # No song found
    except Exception as e:
        print(f"Error searching for song: {e}")
        return None

def get_artist_genres(sp, song_name):
    """
    Obtiene los géneros de la canción buscada por nombre.

    Args:
        sp: The Spotipy client object.
        song_name: The name of the song to search.

    Returns:
        Una lista de géneros del artista de la canción, None si no se encuentra canción o da error.
    """
    try:
        results = sp.search(q=song_name, limit=1)
        if results['tracks']['items']:
            track = results['tracks']['items'][0]
            artist_id = track['artists'][0]['id']
            artist_info = sp.artist(artist_id)
            return artist_info['genres']
        else:
            return None  # No song found
    except Exception as e:
        print(f"Error getting artist genres: {e}")
        return None

# Ejemplo de uso
sp_oauth, spotify = create_spotify()

# Nombre de la canción que quieres buscar
song_name = "me va extrañar yiyo sarante"

# Obtener el nombre completo de la primera canción encontrada
full_song_name = get_first_song_name(spotify, song_name)
print(f"Nombre completo de la canción: {full_song_name}")

# Obtener los géneros del artista de la canción
genres = get_artist_genres(spotify, song_name)
if genres:
    print(f"Los géneros del artista son: {genres}")
else:
    print("No se encontraron géneros para la canción o no se encontró la canción.")

