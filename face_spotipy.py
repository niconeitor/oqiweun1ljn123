import psycopg2
import face_recognition
import cv2
import os
import random
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth


load_dotenv()
# Access environment variables
client_id = os.getenv('SPOTIPY_CLIENT_ID')
client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')

# Configuración de Spotipy (debes obtener tus credenciales de desarrollador de Spotify)

scope = "playlist-read-private user-modify-playback-state playlist-red-collaborative"  # Adjust scopes as needed

sp_oauth = SpotifyOAuth(client_id=client_id,
                        client_secret=client_secret,
                        redirect_uri=redirect_uri,
                        scope=scope)



try:
    conn = psycopg2.connect(host="localhost",dbname="salsia", user="postgres", password="nicolas_asdf1", port="5432")
    print("Conexión exitosa")
except Exception as ex:
    print(f"Error de conexión a la base de datos: {ex}")



imageFacesPath = "faces"
# Función para reconocimiento facial (usando face_recognition)
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

reconocimiento_facial(imageFacesPath)
for recognized_user in reconocimiento_facial(imageFacesPath):
    print(f"Recognized user: {recognized_user}")  # Continuously print recognized user IDs

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
    conn.close()
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
        else:
            print("El cliente no tiene canciones registradas.")
    else:
        print("Cliente no encontrado en la base de datos.")
# Cerrar la conexión a la base de datos al final del programa
conn.close()

# Función para reproducir canción aleatoria en Spotify
# def reproducir_cancion_aleatoria(uri_cancion):
#     for encoding_conocido, id_cliente in rostros_conocidos.items():
#         resultados = face_recognition.compare_faces(
#             encodings_cara, encoding_conocido)
#         if True in resultados:
#             return id_cliente  # Devolvemos el ID del cliente si hay coincidencia

#     return None  # Si no se reconoce la cara





'''
Consideraciones importantes:

Credenciales de Spotify: Asegúrate de tener tus credenciales de desarrollador 
de Spotify y configurar correctamente la variable sp.

Base de datos de rostros: Debes crear tu propia base de datos 
de rostros conocidos (en el ejemplo, rostros_conocidos) con los encodings 
faciales de tus clientes y sus respectivos IDs.

Dispositivo de reproducción: Necesitarás configurar un dispositivo de reproducción 
en Spotify para que la función reproducir_cancion_aleatoria 
pueda enviar la canción a ese dispositivo.

'''
