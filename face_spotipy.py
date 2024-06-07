import psycopg2
import face_recognition
import cv2
import os
import random



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
        image = cv2.resize(image,(150,150))
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

    return cliente

# Si se encontró al cliente
def cancion_aleatoria(cliente):
    if cliente:
        nombre_cliente = cliente[0][0]  # Obtenemos el nombre del primer registro
        canciones_cliente = [c[3] for c in cliente if c[3] is not None]  # Ignoramos el nombre y obtenemos solo las canciones
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

reconocimiento_facial(imageFacesPath)
for recognized_user in reconocimiento_facial(imageFacesPath):
    cliente = buscar_cliente_por_id(recognized_user)
    cancion_aleatoria(cliente)
    