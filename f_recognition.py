import cv2
import os
import face_recognition
import subprocess

# Codificar los rostros extraidos
imageFacesPath = "faces"
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
cancion_reproducida = {nombre: False for nombre in facesNames}

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
               #print(result)
               if True in result:
                    index = result.index(True)
                    name = facesNames[index]
                    color = (125, 220, 0)
               else:
                    name = "Desconocido"
                    color = (50, 50, 255)               
               if name != "Desconocido" and not cancion_reproducida[name]:
                    mp3_file = os.path.join("musica", f"{name}.mp3")
                    subprocess.Popen(["start", "", mp3_file], shell=True)
                    cancion_reproducida[name] = True
               cv2.rectangle(frame, (x, y + h), (x + w, y + h + 30), color, -1)
               cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
               cv2.putText(frame, name, (x, y + h + 25), 2, 1, (255, 255, 255), 2, cv2.LINE_AA)
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