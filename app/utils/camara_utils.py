# camara_utils.py
import cv2
import face_recognition
import time
import os
import numpy as np

class CamaraManager:
    def __init__(self, db_manager):
        self.cap = None
        self.db = db_manager
        self.encodings = []
        self.nombres = []
        self.ids = []
        self.cargar_encodings()
    
    def cargar_encodings(self):
        """Carga encodings desde la base de datos."""
        try:
            self.encodings, self.nombres, self.ids = self.db.cargar_encodings_faciales()
            print(f"✅ {len(self.encodings)} rostros cargados en memoria")
        except Exception as e:
            print(f"❌ Error al cargar encodings: {e}")
        
    def inicializar_camara(self):
        """Inicializar cámara con configuración optimizada"""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            return False
            
        # Configuración optimizada para mejor performance
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reducir buffer para menos delay
        
        return True
    
    def capturar_frame(self):
        """Capturar frame con manejo de errores"""
        if not self.cap:
            return None, False
            
        # Leer frame
        ret, frame = self.cap.read()
        if not ret:
            return None, False
            
        return frame, True
    
    def liberar_camara(self):
        """Liberar recursos de la cámara"""
        if self.cap:
            self.cap.release()
            cv2.destroyAllWindows()

    def capturar_rostros_interactivo(self, estudiante_id, nombre, apellido, num_capturas=5):
        """Función mejorada para captura de rostros"""
        print(f"📸 Capturando {num_capturas} imágenes para: {nombre} {apellido}")
        print("Presiona ESPACIO para capturar, ESC para cancelar")
        
        if not self.inicializar_camara():
            print("❌ No se puede acceder a la cámara")
            return False
        
        # Crear carpeta de imágenes si no existe
        carpeta_imagenes = "app/assets/imagenes_estudiantes"
        os.makedirs(carpeta_imagenes, exist_ok=True)

        capturas_exitosas = 0
        encoding_count = 0
        
        try:
            while capturas_exitosas < num_capturas:
                frame, success = self.capturar_frame()
                if not success:
                    print("❌ Error al capturar frame")
                    break
                
                # Mostrar instrucciones en el frame
                cv2.putText(frame, f"Capturando: {nombre} {apellido}", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"Imagen {capturas_exitosas + 1}/{num_capturas}", (10, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                cv2.putText(frame, "ESPACIO: Capturar | ESC: Cancelar", (10, 90), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                
                # Detectar rostros
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_frame, model="hog")
                
                # Dibujar rectángulo si se detecta rostro
                rostro_detectado = len(face_locations) > 0
                for top, right, bottom, left in face_locations:
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.putText(frame, "ROSTRO DETECTADO", (left, top-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                cv2.imshow('Captura de Rostros', frame)
                
                # MEJORA: Usar waitKey más largo y verificar tecla presionada
                key = cv2.waitKey(50) & 0xFF  # 50ms para mejor respuesta
                
                if key == 32:  # Tecla ESPACIO
                    if rostro_detectado:
                        try:
                            # Guardar imagen
                            timestamp = int(time.time())
                            filename = f"{carpeta_imagenes}/{estudiante_id}_{nombre}_{apellido}_{timestamp}_{capturas_exitosas + 1}.jpg"
                            cv2.imwrite(filename, frame)
                            
                            # Extraer encoding
                            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                            if face_encodings:
                                encoding = face_encodings[0]
                                # ✅ CORREGIDO: Usamos self.db en lugar del parámetro db
                                self.db.guardar_encoding_facial(estudiante_id, encoding, filename)
                                encoding_count += 1
                                capturas_exitosas += 1
                                print(f"✅ Imagen {capturas_exitosas} capturada y guardada")
                                
                                # Feedback visual
                                for _ in range(10):  # Mostrar tick verde por 0.5 segundos
                                    frame_feedback = frame.copy()
                                    cv2.putText(frame_feedback, "✅ CAPTURADO", (50, 120), 
                                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                                    cv2.imshow('Captura de Rostros', frame_feedback)
                                    cv2.waitKey(50)
                            else:
                                print("❌ No se pudo extraer encoding facial")
                        except Exception as e:
                            print(f"❌ Error al guardar: {e}")
                    else:
                        print("❌ No se detectó rostro. Posiciónate frente a la cámara.")
                        
                elif key == 27:  # Tecla ESC
                    print("⏹️ Captura cancelada por el usuario")
                    break
                    
        except Exception as e:
            print(f"❌ Error durante la captura: {e}")
        finally:
            self.liberar_camara()
        
        print(f"📊 Resumen: {capturas_exitosas}/{num_capturas} imágenes capturadas, {encoding_count} encodings guardados")
        return capturas_exitosas > 0

    def detectar_rostros(self, frame):
        """Detecta rostros utilizando face_recognition y devuelve bounding boxes (x, y, w, h)."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame, model="hog")

        rostros = []
        for top, right, bottom, left in face_locations:
            x, y, w, h = left, top, right - left, bottom - top
            rostros.append((x, y, w, h))

        return rostros
    
    '''
    def reconocer_estudiante(rostro_img):
        rgb = cv2.cvtColor(rostro_img, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb)
        if not encodings:
            return None, None

        face_encoding = encodings[0]
        matches = face_recognition.compare_faces(data["encodings"], face_encoding)
        face_distances = face_recognition.face_distance(data["encodings"], face_encoding)

        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            nombre = data["names"][best_match_index]
            confianza = 1 - face_distances[best_match_index]
            return nombre, confianza

        return None, None
        '''

    def reconocer_rostro(self, frame, x, y, w, h):
        """Reconoce un rostro específico dentro del frame."""
        rostro_img = frame[y:y+h, x:x+w]
        rgb = cv2.cvtColor(rostro_img, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb)
        if not encodings:
            return None, None, None

        face_encoding = encodings[0]
        matches = face_recognition.compare_faces(self.encodings, face_encoding)
        face_distances = face_recognition.face_distance(self.encodings, face_encoding)

        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            nombre = self.nombres[best_match_index]
            estudiante_id = self.ids[best_match_index]
            confianza = 1 - face_distances[best_match_index]
            return nombre, estudiante_id, confianza

        return None, None, None