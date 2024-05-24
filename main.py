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
import openpyxl

##################### SECCIÓN DE SPOTIFY ###########################
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
      El nobmre entero del primero resultado, None si no se encuentra cancion o da error.
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

def add_song_to_queue_if_genre_matches(sp, song_name):
  """
  Busca una canción por su nombre, chequea su genero y agrega la lista de reproducción actual solamente si tiene al menos uno de los generos en la lista
  Maneja mas errores

  Args:
      sp: Objeto cliente spotify
      song_name:Nombre de cancion

  Returns:
      Nombre de canción si se agregó exitosamente
  """
  # Error handling (check for empty song name or None)
  if not song_name or not song_name.strip():
      print("No se ingresó un nombre de canción válido.")
      return None
  # Search for the song
  try:
      results = sp.search(q=song_name, limit=1)
  except Exception as e:
      print(f"Error buscando canción: {e}")
      return None
  # Check if song was found
  if not results['tracks']['items']:
      print("No se encontraron canciones con ese nombre.")
      return None
  # Extract song details
  track = results['tracks']['items'][0]
  track_uri = track['uri']
  artist_id = track['artists'][0]['id']
  # Get artist information
  try:
      artist = sp.artist(artist_id)
  except Exception as e:
      print(f"Error obteniendo información del artista: {e}")
      return None
  # Check for genres and add song to queue if there's a match
  genres_to_match = ['salsa', 'samba', 'tango']
  if any(genre in artist['genres'] for genre in genres_to_match):
      print(f"Agregando {track['name']} por {track['artists'][0]['name']} a la lista")
      try:
          sp.add_to_queue(track_uri)
          return track['name']  # Return song name if successful
      except Exception as e:
          print(f"Error agregando canción a la lista: {e}")
          return None
  else:
      print(f"{track['name']} by {track['artists'][0]['name']} no coincide con ningún genero")
      return None

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

#########################SECCIÓN FACE RECOGNITION#########################################
imageFacesPath = "faces"
def reconocimiento_facial(imageFacesPath):
    facesEncodings = []
    facesNames = []
    for file_name in os.listdir(imageFacesPath):
        image = cv2.imread(imageFacesPath + "/" + file_name)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        f_coding = face_recognition.face_encodings(image, known_face_locations=[(0, 150, 150, 0)])[0]
        facesEncodings.append(f_coding)
        facesNames.append(file_name.split(".")[0])

    ##############################################
    # LEYENDO VIDEO
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    # Detector facial
    faceClassif = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    total_frame_count = 0
    interval_frame_count = 0
    interval_length = 10  # Número de frames para detectar
    wait_frames = 30  # Número de frames para esperar antes de iniciar el siguiente intervalo

    while True:
        ret, frame = cap.read()
        if ret == False:
            break

        frame = cv2.flip(frame, 1)
        orig = frame.copy()
        faces = faceClassif.detectMultiScale(frame, 1.1, 5)

        total_frame_count += 1
        interval_frame_count += 1

        if interval_frame_count <= interval_length:  # Procesar solo durante el intervalo de detección
            for (x, y, w, h) in faces:
                face = orig[y:y + h, x:x + w]
                face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
                actual_face_encoding = face_recognition.face_encodings(face, known_face_locations=[(0, w, h, 0)])[0]
                result = face_recognition.compare_faces(facesEncodings, actual_face_encoding)

                if True in result:
                        index = result.index(True)
                        client_name = facesNames[index]
                        color = (125, 220, 0)
                        yield client_name
                else:

                        color = (50, 50, 255)
                        
                cv2.rectangle(frame, (x, y + h), (x + w, y + h), color, -1)
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

        else:
            interval_frame_count = 0  # Reiniciar el contador de frames del intervalo
            if total_frame_count % wait_frames == 0:  # Esperar antes de iniciar el siguiente intervalo
                interval_frame_count = 1  # Comenzar un nuevo intervalo

        # Apretar Escape para cerrar ventana
        cv2.imshow("Frame", frame)
        k = cv2.waitKey(1) & 0xFF
        if k == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

# reconocimiento_facial(imageFacesPath)
# for recognized_user in reconocimiento_facial(imageFacesPath):
#     print(f"Recognized user: {recognized_user}")  # Continuously print recognized user IDs

# Función para buscar cliente y sus canciones por ID
cur = conn.cursor()
def buscar_cliente_por_id(id_cliente):
    # Ejecutar la consulta para obtener los datos del cliente por su ID
    cur.execute("""
        SELECT Cliente.nombre,Cliente.apellidos,Cliente.genero, Cancion.nombre 
        FROM Cliente 
        LEFT JOIN Lista_cancion ON Cliente.id_cliente = Lista_cancion.id_cliente 
        LEFT JOIN Cancion ON Lista_cancion.id_cancion = Cancion.id_cancion 
        WHERE Cliente.id_cliente = %s
    """, (id_cliente,))
    cliente = cur.fetchall()
    # Cerrar la conexión y devolver los datos del cliente
    cur.close()
    return cliente

# Si se encontró al cliente
def cancion_aleatoria(cliente):
    if cliente:
        nombre_cliente = cliente[0][0]  # Obtenemos el nombre del primer registro
        canciones_cliente = [c[1] for c in cliente if c[1] is not None]  # Ignoramos el nombre y obtenemos solo las canciones
        # Obtener una canción aleatoria del cliente si hay canciones registradas
        if canciones_cliente:
            cancion_aleatoria = random.choice(canciones_cliente)
            print("Cliente:", nombre_cliente)
            print("Canción Aleatoria:", cancion_aleatoria)
            return cancion_aleatoria
        else:
            print("El cliente no tiene canciones registradas.")
    else:
        print("Cliente no encontrado en la base de datos.")
# Cerrar la conexión a la base de datos al final del programa

#################################################################################################################
if __name__ == '__main__':
    auth_manager, spotify = create_spotify()  # Initialize as None
    # Check if authentication objects are already created
    playlist_started = False
    played_songs = set()
    try:
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
                cancion=input("Ingrese cancion:")
                cancion_corregida=get_first_song_name(spotify, cancion)
                if cancion_corregida not in played_songs:
                    added_song_name = add_song_to_queue_if_genre_matches(spotify,cancion_corregida)
            # Check if song is added and not yet tracked
                if added_song_name is not None and added_song_name not in played_songs:
                    played_songs.add(added_song_name)  # Track added song name
                else:
                    print("Canción ya agregada, ignorando...")
            time.sleep(5)  # Tiempo entre loop, será borrado mas adelante
    except KeyboardInterrupt:
        pass
with open('played_songs.txt', 'w') as file:
    for song_id in played_songs:

        file.write(f"{song_id}\n")
        
        
