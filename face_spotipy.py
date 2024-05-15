import psycopg2
import face_recognition
import spotipy
import random

# Configuración de Spotipy (debes obtener tus credenciales de desarrollador de Spotify)
sp = spotipy.Spotify(
    client_credentials_manager=spotipy.SpotifyClientCredentials())

# Conexión a la base de datos (una sola vez al inicio del programa)
try:
    conn = psycopg2.connect(
        host="localhost",
        dbname="salsia",
        user="postgres",
        password="nicolas_asdf1",
        port="5432"
    )
    print("Conexión exitosa a la base de datos")
    cur = conn.cursor()  # Cursor para ejecutar consultas
except Exception as ex:
    print(f"Error de conexión a la base de datos: {ex}")
    exit()  # Salir si no se puede conectar

# Función para buscar cliente y sus canciones por ID


def buscar_cliente_y_canciones(id_cliente):
    cur.execute("""
        SELECT Cliente.nombre, canciones.nombre, canciones.uri
        FROM Cliente 
        LEFT JOIN Cliente_Cancion ON Cliente.id = Cliente_Cancion.id_cliente 
        LEFT JOIN canciones ON Cliente_Cancion.id_cancion = canciones.id 
        WHERE Cliente.id = %s
    """, (id_cliente,))
    return cur.fetchall()  # Devolvemos todos los resultados de la consulta

# Función para reconocimiento facial (usando face_recognition)


def reconocimiento_facial(imagen_path):
    imagen = face_recognition.load_image_file(imagen_path)
    encodings_cara = face_recognition.face_encodings(imagen)

    # Debes tener una base de datos de rostros conocidos para comparar
    # Ejemplo:
    rostros_conocidos = {
        "encoding_cliente1": "123",  # Encoding y ID del cliente 1
        "encoding_cliente2": "456",  # Encoding y ID del cliente 2
        # ... más clientes
    }

    for encoding_conocido, id_cliente in rostros_conocidos.items():
        resultados = face_recognition.compare_faces(
            encodings_cara, encoding_conocido)
        if True in resultados:
            return id_cliente  # Devolvemos el ID del cliente si hay coincidencia

    return None  # Si no se reconoce la cara

# Función para reproducir canción aleatoria en Spotify


def reproducir_cancion_aleatoria(uri_cancion):
    # Usamos la API de Spotipy para reproducir la canción
    # (Necesitarás configurar un dispositivo de reproducción en Spotify)
    sp.start_playback(uris=[uri_cancion])


# Ruta de la imagen para el reconocimiento facial
ruta_imagen = "imagen.jpg"  # Reemplaza con la ruta real de tu imagen

# Obtener el ID del cliente mediante reconocimiento facial
id_cliente = reconocimiento_facial(ruta_imagen)

if id_cliente:
    cliente_y_canciones = buscar_cliente_y_canciones(id_cliente)
    if cliente_y_canciones:
        nombre_cliente = cliente_y_canciones[0][0]
        # Filtramos canciones con URI válido
        canciones = [c[1:] for c in cliente_y_canciones if c[2]]
        if canciones:
            cancion_aleatoria = random.choice(canciones)
            print(f"Cliente: {nombre_cliente}")
            print(f"Reproduciendo canción aleatoria: {cancion_aleatoria[0]}")
            reproducir_cancion_aleatoria(
                cancion_aleatoria[1])  # Reproducimos la canción
        else:
            print("El cliente no tiene canciones favoritas registradas en Spotify.")
    else:
        print("Cliente no encontrado en la base de datos.")
else:
    print("No se pudo reconocer la cara en la imagen.")

# Cerrar la conexión a la base de datos al final del programa
conn.close()

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
