import tkinter as tk
import threading
import cv2
import face_recognition
import os
import random
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
import psutil
import subprocess
import pandas as pd
from datetime import datetime
import psycopg2
import time

class FaceRecognitionApp:
    def __init__(self, root, imageFacesPath):
        self.root = root
        self.root.title("Face Recognition App")
        self.root.geometry("800x600")
        self.imageFacesPath = imageFacesPath
        self.cap = None
        self.stop_event = threading.Event()
        self.recognition_thread = None
        self.spotify_thread = None
        self.auth_manager = None
        self.spotify = None
        self.playlist_started = False
        self.played_songs = []
        self.recognized_client_name = None
        self.lock = threading.Lock()
        self.client_attempts = {}

        self.conn = self.connect_to_db()
        if self.conn:
            self.cur = self.conn.cursor()
        else:
            self.cur = None

        self.start_button = tk.Button(root, text="Start Recognition", command=self.start_recognition)
        self.start_button.pack(pady=10)

        self.stop_button = tk.Button(root, text="Stop Recognition", command=self.stop_recognition, state=tk.DISABLED)
        self.stop_button.pack(pady=10)

        self.spotify_start_button = tk.Button(root, text="Initialize Spotify", command=self.start_spotify)
        self.spotify_start_button.pack(pady=10)

        self.spotify_stop_button = tk.Button(root, text="Stop Spotify", command=self.stop_spotify, state=tk.DISABLED)
        self.spotify_stop_button.pack(pady=10)

        self.exit_button = tk.Button(root, text="Exit", command=self.exit_app)
        self.exit_button.pack(pady=10)

        self.recognized_label = tk.Label(root, text="Recognized Client: None")
        self.recognized_label.pack(pady=10)

        self.notification_label = tk.Label(root, text="", fg="red")
        self.notification_label.pack(pady=10)

    def connect_to_db(self):
        try:
            conn = psycopg2.connect(
                host="localhost",
                dbname="salsia",
                user="postgres",
                password="nicolas_asdf1",
                port="5432"
            )
            print("Conexión exitosa")
            return conn
        except Exception as ex:
            print(f"Error de conexión a la base de datos: {ex}")
            return None

    def start_recognition(self):
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.stop_event.clear()
        self.recognition_thread = threading.Thread(target=self.reconocimiento_facial)
        self.recognition_thread.start()

    def stop_recognition(self):
        self.stop_event.set()
        if self.recognition_thread and self.recognition_thread.is_alive():
            self.recognition_thread.join()
        self.release_resources()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def start_spotify(self):
        self.stop_event.clear()
        self.spotify_thread = threading.Thread(target=self.spotify_module)
        self.spotify_thread.start()
        self.spotify_start_button.config(state=tk.DISABLED)
        self.spotify_stop_button.config(state=tk.NORMAL)

    def stop_spotify(self):
        self.stop_event.set()
        if self.spotify_thread and self.spotify_thread.is_alive():
            self.spotify_thread.join()
        self.write_played_songs_to_file()
        self.spotify_start_button.config(state=tk.NORMAL)
        self.spotify_stop_button.config(state=tk.DISABLED)

    def exit_app(self):
        if self.recognition_thread and self.recognition_thread.is_alive():
            self.stop_recognition()
        if self.spotify_thread and self.spotify_thread.is_alive():
            self.stop_spotify()
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
        self.root.quit()

    def update_recognized_client_name(self, client_id):
        cliente = self.buscar_cliente_por_id(client_id)
        if cliente:
            nombre_completo = f"{cliente[0][0]} {cliente[0][1]}"
            self.recognized_label.config(text=f"Recognized Client: {nombre_completo}")
            if self.spotify:
                if client_id not in self.client_attempts:
                    self.client_attempts[client_id] = 0
                self.try_add_client_song(cliente, client_id)
        else:
            self.recognized_label.config(text="Recognized Client: Desconocido")
        
        with self.lock:
            self.recognized_client_name = nombre_completo

    def buscar_cliente_por_id(self, id_cliente):
        if self.cur:
            try:
                self.cur.execute("""
                    SELECT Cliente.nombre, Cliente.apellidos, Cliente.genero, Cancion.nombre 
                    FROM Cliente 
                    LEFT JOIN Lista_cancion ON Cliente.id_cliente = Lista_cancion.id_cliente 
                    LEFT JOIN Cancion ON Lista_cancion.id_cancion = Cancion.id_cancion 
                    WHERE Cliente.id_cliente = %s
                """, (id_cliente,))
                cliente = self.cur.fetchall()
                return cliente
            except Exception as ex:
                print(f"Error ejecutando la consulta: {ex}")
                return None
        else:
            print("Cursor no disponible")
            return None

    def try_add_client_song(self, cliente, client_id):
        canciones_cliente = [c[3] for c in cliente if c[3] is not None]
        if canciones_cliente and self.client_attempts[client_id] < 3:
            cancion_aleatoria = random.choice(canciones_cliente)
            self.client_attempts[client_id] += 1
            self.add_song_to_queue(cancion_aleatoria, client_id)
        else:
            print("El cliente no tiene canciones registradas o se han agotado los intentos.")

    def add_song_to_queue(self, song_name=None, client_id=None):
        if self.spotify and song_name:
            song_data = self.get_first_song_name(song_name)
            if song_data:
                song_name, artist_name = song_data
                if song_name not in [song[0] for song in self.played_songs]:
                    result = self.add_song_to_queue_if_genre_matches(song_name, artist_name)
                    if result and client_id:
                        self.client_attempts[client_id] = 3
                else:
                    self.notification_label.config(text=f"Canción '{song_name}' ya está en la lista.")
            else:
                self.notification_label.config(text="Canción no encontrada.")

    def reconocimiento_facial(self):
        facesEncodings = []
        facesNames = []
        for file_name in os.listdir(self.imageFacesPath):
            image = cv2.imread(self.imageFacesPath + "/" + file_name)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            f_coding = face_recognition.face_encodings(image, known_face_locations=[(0, 150, 150, 0)])[0]
            facesEncodings.append(f_coding)
            facesNames.append(file_name.split(".")[0])

        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        faceClassif = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

        while not self.stop_event.is_set():
            ret, frame = self.cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            orig = frame.copy()
            faces = faceClassif.detectMultiScale(frame, 1.1, 5)

            for (x, y, w, h) in faces:
                face = orig[y:y + h, x:x + w]
                face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)

                try:
                    with self.lock:
                        actual_face_encoding = face_recognition.face_encodings(face, known_face_locations=[(0, w, h, 0)])[0]
                        result = face_recognition.compare_faces(facesEncodings, actual_face_encoding)
                except IndexError:
                    continue

                if True in result:
                    index = result.index(True)
                    client_id = facesNames[index]
                    self.update_recognized_client_name(client_id)
                    color = (125, 220, 0)
                    print(f"Recognized user: {client_id}")
                else:
                    color = (50, 50, 255)

                cv2.rectangle(frame, (x, y + h), (x + w, y + h), color, -1)
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

            cv2.imshow("Frame", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                self.stop_event.set()
                break

        self.release_resources()

    def release_resources(self):
        try:
            if self.cap:
                self.cap.release()
            cv2.destroyAllWindows()
        except Exception as e:
            print(f"Error releasing resources: {e}")

    def spotify_module(self):
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
                print("No hay token en el cache, necesita autorización inicial.")
                return auth_manager, spotify
            if token_info:
                if auth_manager.is_token_expired(token_info):
                    auth_manager, spotify = create_spotify()
            return auth_manager, spotify

        def is_spotify_running():
            for process in psutil.process_iter():
                if process.name() == "Spotify.exe":
                    return True
            return False

        def open_spotify_if_not_running():
            if not is_spotify_running():
                spotify_path = r"C:\Users\Nico\Desktop\spotify.lnk"
                subprocess.Popen([spotify_path], shell=True)

        def check_and_play_first_playlist(spotify):
            try:
                current_track = spotify.current_user_playing_track()
                if current_track is None or not current_track['is_playing']:
                    playlists = spotify.user_playlists(user=spotify.current_user()["id"])
                    if playlists["items"]:
                        first_playlist_id = playlists["items"][0]["id"]
                        for _ in range(5):
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
                            print("Falló en encontrar un dispositivo después de 5 intentos, cerrando.")
                else:
                    print("Ya hay música reproduciéndose.")
            except spotipy.exceptions.SpotifyException as e:
                if e.http_status == 429:
                    retry_after = int(e.headers.get('Retry-After', 1))
                    print(f"Tasa límite excedida. Intentando después de {retry_after} segundos.")
                    time.sleep(retry_after)
                    check_and_play_first_playlist(spotify)
                else:
                    print(f"Spotify API error: {e}")

        load_dotenv("credentials.env")
        client_id = os.getenv('SPOTIPY_CLIENT_ID')
        client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
        redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')
        scope = "playlist-read-private user-modify-playback-state playlist-read-collaborative user-read-currently-playing user-read-playback-state"

        self.auth_manager, self.spotify = create_spotify()
        
        while not self.stop_event.is_set():
            self.auth_manager, self.spotify = refresh_spotify(self.auth_manager, self.spotify)

            if not is_spotify_running():
                print("Spotify no está abierto. Abriendo Spotify y reproduciendo la primera lista de música...")
                open_spotify_if_not_running()
                time.sleep(5)
                self.playlist_started = False

            if not self.playlist_started:
                current_playback = self.spotify.current_playback()
                if current_playback is None or not current_playback['is_playing']:
                    check_and_play_first_playlist(self.spotify)
                    time.sleep(2)

            current_playback = self.spotify.current_playback()
            if current_playback and current_playback['is_playing']:
                time.sleep(5)

        self.write_played_songs_to_file()

    def get_first_song_name(self, song_name):
        try:
            results = self.spotify.search(q=song_name, limit=1)
            if results['tracks']['items']:
                track = results['tracks']['items'][0]
                return track['name'], track['artists'][0]['name']
            else:
                return None
        except Exception as e:
            print(f"Error searching for song: {e}")
            return None

    def add_song_to_queue_if_genre_matches(self, song_name, artist_name):
        if not song_name or not song_name.strip():
            print("No se ingresó un nombre de canción válido.")
            return None
        try:
            results = self.spotify.search(q=song_name, limit=1)
        except Exception as e:
            print(f"Error buscando canción: {e}")
            return None
        if not results['tracks']['items']:
            print("No se encontraron canciones con ese nombre.")
            return None
        track = results['tracks']['items'][0]
        track_uri = track['uri']
        artist_id = track['artists'][0]['id']
        try:
            artist = self.spotify.artist(artist_id)
        except Exception as e:
            print(f"Error obteniendo información del artista: {e}")
            return None
        genres_to_match = ['salsa', 'samba', 'tango', 'cumbia chilena', 'latin alternative', 'salsa puertorriquena', 'tropical', 'latin pop']
        if any(genre in artist['genres'] for genre in genres_to_match):
            print(f"Agregando {track['name']} por {track['artists'][0]['name']} a la lista")
            try:
                self.spotify.add_to_queue(track_uri)
                self.played_songs.append((track['name'], artist_name))
                self.notification_label.config(text=f"Canción '{track['name']}' agregada a la lista.")
                return track['name']
            except Exception as e:
                print(f"Error agregando canción a la lista: {e}")
                self.notification_label.config(text=f"Error agregando canción '{track['name']}' a la lista.")
                return None
        else:
            print(f"{track['name']} by {track['artists'][0]['name']} no coincide con ningún género")
            self.notification_label.config(text=f"{track['name']} no coincide con ningún género.")
            return None

    def write_played_songs_to_file(self):
        current_time = datetime.now().strftime("%d-%m-%Y-%H_%M")
        filename = f"lista_de_canciones_{current_time}.xlsx"
        df = pd.DataFrame(self.played_songs, columns=["Nombre Cancion", "Artista"])
        df.to_excel(filename, index=False)
        print(f"Archivo '{filename}' generado con éxito.")

if __name__ == "__main__":
    root = tk.Tk()
    app = FaceRecognitionApp(root, "faces")
    root.mainloop()
