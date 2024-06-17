import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
import threading
import time
import os
import cv2
import face_recognition
import random
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
import psutil
import subprocess
import pandas as pd
from datetime import datetime
import psycopg2

class WelcomeDisplay:
    def __init__(self, root, logo_path, background_color):
        self.root = root
        self.logo_path = logo_path
        self.background_color = background_color
        self.client_welcomed = set()
        self.message_queue = []
        self.current_message = None
        self.stop_event = threading.Event()

        self.root.geometry("800x600")
        self.root.configure(bg=self.background_color)

        self.canvas = tk.Canvas(self.root, bg=self.background_color, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.logo_img = Image.open(self.logo_path)
        self.logo_frames = [ImageTk.PhotoImage(frame.convert("RGBA")) for frame in ImageSequence.Iterator(self.logo_img)]
        self.logo_item = self.canvas.create_image(self.root.winfo_width() // 2, self.root.winfo_height() // 2, anchor=tk.CENTER, image=self.logo_frames[0])

        self.root.bind("<Escape>", self.exit_fullscreen)
        self.root.bind("<Alt-Return>", self.toggle_fullscreen)
        self.root.bind("<Configure>", self.on_resize)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.animating = True
        self.animation_thread = threading.Thread(target=self.animate_logo)
        self.animation_thread.start()

    def animate_logo(self):
        frame_index = 0
        while not self.stop_event.is_set():
            if not self.canvas.winfo_exists():
                return
            frame = self.logo_frames[frame_index]
            self.canvas.itemconfig(self.logo_item, image=frame)
            frame_index = (frame_index + 1) % len(self.logo_frames)
            time.sleep(0.1)

    def on_resize(self, event):
        if not self.canvas.winfo_exists():
            return
        self.canvas.coords(self.logo_item, event.width // 2, event.height // 2)

    def toggle_fullscreen(self, event=None):
        if not self.root.winfo_exists():
            return
        is_fullscreen = self.root.attributes("-fullscreen")
        self.root.attributes("-fullscreen", not is_fullscreen)

    def exit_fullscreen(self, event=None):
        if not self.root.winfo_exists():
            return
        self.root.attributes("-fullscreen", False)
        self.root.destroy()

    def on_close(self):
        self.stop_event.set()
        self.animation_thread.join()
        self.root.destroy()

    def show_welcome_message(self, name, last_name, gender):
        if name not in self.client_welcomed:
            self.client_welcomed.add(name)
            message = self.generate_message(name, last_name, gender)
            self.message_queue.append(message)
            if not self.current_message:
                self.display_next_message()

    def generate_message(self, name, last_name, gender):
        if gender == 'masculino':
            return f"Bienvenido a nivel 80 {name} {last_name}! Un gusto tenerte con nosotros!"
        elif gender == 'femenino':
            return f"Bienvenida a nivel 80 {name} {last_name}! Un gusto tenerte con nosotros!"
        else:
            return f"Bienvenide a nivel 80 {name} {last_name}! Un gusto tenerte con nosotros!"

    def display_next_message(self):
        if self.message_queue:
            self.current_message = self.message_queue.pop(0)
            self.hide_logo()
            self.display_message_on_screen(self.current_message)
            self.root.after(10000, self.clear_message)

    def display_message_on_screen(self, message):
        if not self.canvas.winfo_exists():
            return
        self.message_item = self.canvas.create_text(self.root.winfo_width() // 2, self.root.winfo_height() // 2,
                                                    text=message, font=("Helvetica", 24, "bold"), fill="white",
                                                    anchor=tk.CENTER)

    def hide_logo(self):
        if not self.canvas.winfo_exists():
            return
        self.canvas.itemconfig(self.logo_item, state='hidden')

    def show_logo(self):
        if not self.canvas.winfo_exists():
            return
        self.canvas.itemconfig(self.logo_item, state='normal')

    def clear_message(self):
        if not self.canvas.winfo_exists():
            return
        self.canvas.delete(self.message_item)
        self.current_message = None
        self.show_logo()
        self.display_next_message()

class FaceRecognitionApp:
    def __init__(self, root, imageFacesPath):
        self.root = root
        self.root.title("Face Recognition App")
        self.root.geometry("1024x768")
        self.imageFacesPath = imageFacesPath
        self.cap = None
        self.stop_event = threading.Event()
        self.stop_spotify_event = threading.Event()
        self.recognition_thread = None
        self.spotify_thread = None
        self.auth_manager = None
        self.spotify = None
        self.playlist_started = False
        self.played_songs = []
        self.recognized_clients = {}  # Diccionario para almacenar clientes reconocidos

        self.conn = self.connect_to_db()
        if self.conn:
            self.cur = self.conn.cursor()
        else:
            self.cur = None

        self.start_button = tk.Button(root, text="Start Recognition", command=self.start_recognition)
        self.start_button.pack(pady=10)

        self.print_button = tk.Button(root, text="Generar listas", command=self.generar_listas, state=tk.DISABLED)
        self.print_button.pack(pady=10)

        self.spotify_start_button = tk.Button(root, text="Initialize Spotify", command=self.start_spotify)
        self.spotify_start_button.pack(pady=10)

        self.spotify_stop_button = tk.Button(root, text="Stop Spotify", command=self.stop_spotify, state=tk.DISABLED)
        self.spotify_stop_button.pack(pady=10)

        self.welcome_button = tk.Button(root, text="Mensajes de bienvenida", command=self.start_welcome_display)
        self.welcome_button.pack(pady=10)

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
        self.print_button.config(state=tk.NORMAL)
        self.stop_event.clear()
        self.recognition_thread = threading.Thread(target=self.reconocimiento_facial)
        self.recognition_thread.start()

    def stop_recognition(self):
        self.stop_event.set()
        if self.recognition_thread and self.recognition_thread.is_alive():
            self.recognition_thread.join()
        self.release_resources()
        self.start_button.config(state=tk.NORMAL)
        self.print_button.config(state=tk.DISABLED)

    def generar_listas(self):
        if self.recognized_clients:
            df_clients = pd.DataFrame(self.recognized_clients.values(), columns=["Nombre Cliente", "Apellidos Cliente", "Fecha de Reconocimiento"])
            current_time = datetime.now().strftime("%d-%m-%Y-%H_%M")
            filename_clients = f"lista_de_clientes_{current_time}.xlsx"
            df_clients.to_excel(filename_clients, index=False)
            print(f"Archivo '{filename_clients}' generado con éxito.")
        else:
            print("No hay clientes reconocidos para imprimir.")

        if self.played_songs:
            current_time = datetime.now().strftime("%d-%m-%Y-%H_%M")
            filename_songs = f"lista_de_canciones_{current_time}.xlsx"
            df_songs = pd.DataFrame(self.played_songs, columns=["Nombre Cancion", "Artista"])
            df_songs.to_excel(filename_songs, index=False)
            print(f"Archivo '{filename_songs}' generado con éxito.")
        else:
            print("No hay canciones reproducidas para imprimir.")

    def start_spotify(self):
        self.stop_spotify_event.clear()
        self.spotify_thread = threading.Thread(target=self.spotify_module)
        self.spotify_thread.start()
        self.spotify_start_button.config(state=tk.DISABLED)
        self.spotify_stop_button.config(state=tk.NORMAL)

    def stop_spotify(self):
        self.stop_spotify_event.set()
        if self.spotify_thread and self.spotify_thread.is_alive():
            self.spotify_thread.join()
        self.spotify_start_button.config(state=tk.NORMAL)
        self.spotify_stop_button.config(state=tk.DISABLED)

    def start_welcome_display(self):
        welcome_root = tk.Toplevel(self.root)
        logo_path = "3D-NIVEL-80-LIVE.gif"
        background_color = "#3F007F"
        welcome_display = WelcomeDisplay(welcome_root, logo_path, background_color)
        self.welcome_display = welcome_display

    def exit_app(self):
        self.stop_recognition()
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
            current_time = datetime.now().strftime("%d-%m-%Y-%H:%M")
            if client_id not in self.recognized_clients:
                self.recognized_clients[client_id] = (cliente[0][0], cliente[0][1], current_time)
            if self.spotify and self.playlist_started:
                self.try_add_client_song(cliente, client_id)
            # Llamar al método show_welcome_message del módulo WelcomeDisplay si está abierto
            if hasattr(self, 'welcome_display'):
                self.root.after(0, self.welcome_display.show_welcome_message, cliente[0][0], cliente[0][1], cliente[0][2])
        else:
            self.recognized_label.config(text="Recognized Client: Desconocido")

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
        if canciones_cliente:
            cancion_aleatoria = random.choice(canciones_cliente)
            self.add_song_to_queue(cancion_aleatoria, client_id)
        else:
            print("El cliente no tiene canciones registradas.")

    def add_song_to_queue(self, song_name=None, client_id=None):
        if self.spotify and self.playlist_started and song_name:
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
                    actual_face_encoding = face_recognition.face_encodings(face, known_face_locations=[(0, w, h, 0)])[0]
                    result = face_recognition.compare_faces(facesEncodings, actual_face_encoding)
                except IndexError:
                    continue

                if True in result:
                    index = result.index(True)
                    client_id = facesNames[index]
                    self.root.after(0, self.update_recognized_client_name, client_id)
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

            time.sleep(0.1)  # Optimización para reducir carga de CPU

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
                time.sleep(5)  # Espera 5 segundos para dar tiempo a Spotify para abrir

        def ensure_playback_started(spotify):
            while True:
                current_playback = spotify.current_playback()
                if current_playback and current_playback['is_playing']:
                    return True
                print("Esperando a que Spotify esté reproduciendo música...")
                devices = spotify.devices()
                if devices['devices']:
                    device_id = devices['devices'][0]['id']
                    playlists = spotify.user_playlists(user=spotify.current_user()["id"])
                    if playlists["items"]:
                        first_playlist_id = playlists["items"][0]["id"]
                        spotify.start_playback(device_id=device_id, context_uri=f"spotify:playlist:{first_playlist_id}")
                time.sleep(5)

        load_dotenv("credentials.env")
        client_id = os.getenv('SPOTIPY_CLIENT_ID')
        client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
        redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')
        scope = "playlist-read-private user-modify-playback-state playlist-read-collaborative user-read-currently-playing user-read-playback-state"

        self.auth_manager, self.spotify = create_spotify()

        if not is_spotify_running():
            open_spotify_if_not_running()

        while not self.stop_spotify_event.is_set():
            self.auth_manager, self.spotify = refresh_spotify(self.auth_manager, self.spotify)

            if not is_spotify_running():
                print("Spotify no está abierto. Abriendo Spotify y esperando 5 segundos para que esté listo...")
                open_spotify_if_not_running()

            if ensure_playback_started(self.spotify):
                self.playlist_started = True
                break

        while not self.stop_spotify_event.is_set():
            if self.playlist_started:
                time.sleep(5)

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
        if not self.playlist_started:
            print("Esperando a que Spotify comience a reproducir música antes de agregar canciones.")
            return None

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

if __name__ == "__main__":
    root = tk.Tk()
    app = FaceRecognitionApp(root, "faces")
    root.mainloop()
