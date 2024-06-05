import cv2
import os
import psycopg2

try:
    conn = psycopg2.connect(host="localhost",dbname="salsia", user="postgres", password="nicolas_asdf1", port="5432")
    print("Conexión exitosa")
except Exception as ex:
    print(ex)
       
cur = conn.cursor()

# Obtener el id_cliente más alto
cur.execute("SELECT COALESCE(MAX(id_cliente), 0) FROM Cliente")
max_id_cliente = cur.fetchone()[0]
print(f"ID de cliente más alto en la base de datos: {max_id_cliente}")

# Cerrar la conexión a la base de datos
cur.close()
conn.close()

# Configurar los caminos y crear la carpeta "faces" si no existe
imagesPath = "input_images"
outputPath = "faces"

if not os.path.exists(outputPath):
    os.makedirs(outputPath)
    print("Nueva carpeta: faces")

# Detector facial
faceClassif = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Inicializar el contador de IDs de clientes
current_id_cliente = max_id_cliente + 1

# Procesar las imágenes
for imageName in os.listdir(imagesPath):
    imagePath = os.path.join(imagesPath, imageName)
    print(f"Procesando {imageName}")
    image = cv2.imread(imagePath)
    if image is None:
        print(f"Error al leer la imagen: {imageName}")
        continue

    faces = faceClassif.detectMultiScale(image, 1.1, 5)
    
    # Verificar el número de rostros detectados
    if len(faces) == 0:
        print(f"No se detectaron rostros en {imageName}")
    elif len(faces) > 1:
        print(f"Error: Se detectaron múltiples rostros en {imageName}. No se extraerá ningún rostro.")
    else:
        # Si se detecta solo un rostro
        for (x, y, w, h) in faces:
            face = image[y:y + h, x:x + w]
            face = cv2.resize(face, (150, 150))

            # Guardar la imagen de la cara con el nuevo ID del cliente
            face_filename = os.path.join(outputPath, f"{current_id_cliente}.jpg")
            cv2.imwrite(face_filename, face)
            print(f"Guardada la cara con ID {current_id_cliente} como {face_filename}")

            # Incrementar el ID del cliente para la siguiente imagen
            current_id_cliente += 1

    # Eliminar la imagen original una vez procesada
    os.remove(imagePath)
    print(f"Imagen original {imageName} eliminada")

print("Procesamiento completado.")