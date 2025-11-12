import cv2
import face_recognition
import numpy as np
from datetime import datetime
import time
from app.utils.qr_utils import qr_manager

class AsistenciaService:
    def __init__(self, db_manager):
        self.db = db_manager
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        self.cargar_encodings()
        
        # Control de frames
        self.frame_skip = 2
        self.frame_count = 0
        
        # Suavizado para detecciones
        self.detection_history = {}
        self.history_length = 5
        
        # Control de QR para evitar múltiples registros
        self.ultimo_qr_detectado = None
        self.tiempo_ultimo_qr = 0
        
    def cargar_encodings(self):
        """Cargar encodings faciales desde la base de datos"""
        try:
            self.known_face_encodings, self.known_face_names, self.known_face_ids = self.db.cargar_encodings_faciales()
            print(f"🔍 Sistema listo con {len(self.known_face_encodings)} encodings de {len(set(self.known_face_ids))} estudiantes")
        except Exception as e:
            print(f"❌ Error cargando encodings: {e}")
            self.known_face_encodings, self.known_face_names, self.known_face_ids = [], [], []
    
    def procesar_frame_combinado(self, frame):
        """Procesa frame para detección facial Y de QR"""
        self.frame_count += 1
        
        # Procesar solo cada X frames
        if self.frame_count % self.frame_skip != 0:
            return [], [], [], [], []
        
        # Reducir tamaño para mejor performance
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # DETECCIÓN FACIAL
        face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        
        face_names = []
        face_ids = []
        confianzas = []
        estudiantes_registrados_este_frame = []
        
        for face_encoding in face_encodings:
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                best_distance = face_distances[best_match_index]
                confianza = 1 - best_distance
                
                if best_distance < 0.6:
                    name = self.known_face_names[best_match_index]
                    estudiante_id = self.known_face_ids[best_match_index]
                    
                    if confianza > 0.6 and estudiante_id not in estudiantes_registrados_este_frame:
                        self.registrar_asistencia_unica(estudiante_id, confianza, 'rostro')
                        estudiantes_registrados_este_frame.append(estudiante_id)
                else:
                    name = "Desconocido"
                    estudiante_id = None
                    confianza = best_distance
            else:
                name = "Desconocido"
                estudiante_id = None
                confianza = 0.0
            
            face_names.append(name)
            face_ids.append(estudiante_id)
            confianzas.append(confianza)
        
        # Escalar coordenadas faciales
        face_locations = [(top * 2, right * 2, bottom * 2, left * 2) 
                        for (top, right, bottom, left) in face_locations]
        
        # DETECCIÓN DE QR
        qr_datos = qr_manager.detectar_qr_en_frame(frame)
        qr_estudiantes = []
        
        for qr in qr_datos:
            qr_data = qr['data']
            
            # Evitar múltiples registros del mismo QR (esperar 5 segundos)
            tiempo_actual = time.time()
            if (self.ultimo_qr_detectado != qr_data or 
                tiempo_actual - self.tiempo_ultimo_qr > 5):
                
                # Buscar estudiante por QR
                estudiante = self.db.obtener_estudiante_por_qr(qr_data)
                if estudiante:
                    estudiante_id = estudiante[0]
                    nombre = f"{estudiante[2]} {estudiante[3]}"
                    
                    if estudiante_id not in estudiantes_registrados_este_frame:
                        self.registrar_asistencia_unica(estudiante_id, 1.0, 'qr')
                        estudiantes_registrados_este_frame.append(estudiante_id)
                        
                        qr_estudiantes.append({
                            'id': estudiante_id,
                            'nombre': nombre,
                            'qr_data': qr_data,
                            'rect': qr['rect']
                        })
                    
                    self.ultimo_qr_detectado = qr_data
                    self.tiempo_ultimo_qr = tiempo_actual
        
        # Aplicar suavizado a detecciones faciales
        face_locations, face_names, face_ids, confianzas = self.aplicar_suavizado(
            face_locations, face_names, face_ids, confianzas
        )
        
        return face_locations, face_names, face_ids, confianzas, qr_estudiantes
    
    def aplicar_suavizado(self, face_locations, face_names, face_ids, confianzas):
        """Aplicar suavizado mejorado para reducir parpadeo"""
        current_time = time.time()
        
        # Limpiar detecciones antiguas
        to_remove = []
        for key in self.detection_history:
            if current_time - self.detection_history[key]['timestamp'] > 3.0:
                to_remove.append(key)
        
        for key in to_remove:
            del self.detection_history[key]
        
        # Actualizar historial con detecciones actuales
        for i, (location, name, face_id, confianza) in enumerate(zip(face_locations, face_names, face_ids, confianzas)):
            if face_id and name != "Desconocido":
                key = f"{face_id}"
                if key not in self.detection_history:
                    self.detection_history[key] = {
                        'locations': [],
                        'names': [],
                        'confianzas': [],
                        'timestamp': current_time,
                        'count': 0
                    }
                
                self.detection_history[key]['locations'].append(location)
                self.detection_history[key]['names'].append(name)
                self.detection_history[key]['confianzas'].append(confianza)
                self.detection_history[key]['count'] += 1
                self.detection_history[key]['timestamp'] = current_time
                
                # Mantener solo el historial reciente
                if len(self.detection_history[key]['locations']) > self.history_length:
                    self.detection_history[key]['locations'].pop(0)
                    self.detection_history[key]['names'].pop(0)
                    self.detection_history[key]['confianzas'].pop(0)
        
        # Usar historial para estabilizar detecciones actuales
        stabilized_locations = []
        stabilized_names = []
        stabilized_ids = []
        stabilized_confianzas = []
        
        for key, history in self.detection_history.items():
            if history['count'] >= 2:
                if len(history['locations']) > 0:
                    # Usar la ubicación promedio del historial
                    avg_location = (
                        int(np.mean([loc[0] for loc in history['locations']])),
                        int(np.mean([loc[1] for loc in history['locations']])),
                        int(np.mean([loc[2] for loc in history['locations']])),
                        int(np.mean([loc[3] for loc in history['locations']]))
                    )
                    avg_name = max(set(history['names']), key=history['names'].count)
                    avg_confianza = np.mean(history['confianzas'])
                    
                    face_id = int(key) if key.isdigit() else None
                    
                    stabilized_locations.append(avg_location)
                    stabilized_names.append(avg_name)
                    stabilized_ids.append(face_id)
                    stabilized_confianzas.append(avg_confianza)
        
        # Si hay detecciones actuales, priorizarlas sobre el historial
        if face_locations:
            return face_locations, face_names, face_ids, confianzas
        else:
            return stabilized_locations, stabilized_names, stabilized_ids, stabilized_confianzas
    
    def dibujar_resultados_combinados(self, frame, face_locations, face_names, confianzas, qr_estudiantes):
        """Dibuja resultados de detección facial y QR"""
        # Dibujar detecciones faciales
        for (top, right, bottom, left), name, confianza in zip(face_locations, face_names, confianzas):
            if name == "Desconocido":
                color = (0, 0, 255)
                texto_confianza = f"{confianza:.2f}"
            else:
                if confianza > 0.7:
                    color = (0, 255, 0)
                elif confianza > 0.5:
                    color = (0, 255, 255)
                else:
                    color = (0, 165, 255)
                texto_confianza = f"{confianza:.2f}"
            
            cv2.rectangle(frame, (left, top), (right, bottom), color, 3)
            label_height = 30
            cv2.rectangle(frame, (left, bottom - label_height), (right, bottom), color, cv2.FILLED)
            
            font = cv2.FONT_HERSHEY_DUPLEX
            texto = f"{name} ({texto_confianza})"
            cv2.putText(frame, texto, (left + 6, bottom - 6), font, 0.5, (255, 255, 255), 1)
        
        # Dibujar detecciones QR
        for qr_est in qr_estudiantes:
            rect = qr_est['rect']
            cv2.rectangle(frame, (rect.left, rect.top), 
                         (rect.left + rect.width, rect.top + rect.height), 
                         (255, 0, 255), 3)
            
            texto = f"QR: {qr_est['nombre']}"
            cv2.putText(frame, texto, (rect.left, rect.top - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
        
        # Estadísticas
        rostros_totales = len(face_locations)
        rostros_reconocidos = sum(1 for name in face_names if name != "Desconocido")
        qr_detectados = len(qr_estudiantes)
        
        cv2.putText(frame, f"Rostros: {rostros_reconocidos}/{rostros_totales}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"QR: {qr_detectados}", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return frame
    
    def registrar_asistencia_unica(self, estudiante_id, confianza, metodo):
        """Registrar asistencia solo si no se ha registrado hoy"""
        hoy = datetime.now().date()
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id FROM asistencias 
            WHERE estudiante_id = ? AND fecha = ? AND metodo_deteccion = ?
        ''', (estudiante_id, hoy, metodo))
        
        if cursor.fetchone() is None:
            self.registrar_asistencia_db(estudiante_id, metodo, confianza)
            print(f"✅ Asistencia registrada: Estudiante {estudiante_id} por {metodo}")
        
        conn.close()
    
    def registrar_asistencia_db(self, estudiante_id, metodo_deteccion, confianza):
        """Método para registrar asistencia en la base de datos"""
        conn = self.db._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO asistencias (estudiante_id, fecha, hora, metodo_deteccion, estado, confianza)
                VALUES (?, DATE('now'), TIME('now'), ?, 'presente', ?)
            ''', (estudiante_id, metodo_deteccion, confianza))
            conn.commit()
        except Exception as e:
            print(f"❌ Error al registrar asistencia: {e}")
        finally:
            conn.close()
    
    def iniciar_monitoreo_combinado(self):
        """Inicia el sistema combinado de reconocimiento facial + QR"""
        print("🚀 INICIANDO SISTEMA COMBINADO (Rostro + QR)")
        print("Presiona 'q' para salir")
        print("Presiona 'r' para recargar encodings")
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ No se puede acceder a la cámara")
            return
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("❌ Error al capturar frame")
                    break
                
                # Procesar frame combinado
                face_locations, face_names, face_ids, confianzas, qr_estudiantes = self.procesar_frame_combinado(frame)
                
                # Dibujar resultados combinados
                frame = self.dibujar_resultados_combinados(frame, face_locations, face_names, confianzas, qr_estudiantes)
                
                # Mostrar frame
                cv2.imshow('Sistema de Asistencias - Rostro + QR', frame)
                
                # Controles
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    self.cargar_encodings()
                    print("✅ Encodings recargados")
                    
        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("✅ Sistema combinado detenido")
    
    def obtener_asistencias_del_dia(self):
        """Obtiene las asistencias del día actual"""
        hoy = datetime.now().date()
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT e.nombre, e.apellido, e.dni, a.hora, a.metodo_deteccion, a.confianza
                FROM asistencias a
                JOIN estudiantes e ON a.estudiante_id = e.id
                WHERE a.fecha = ?
                ORDER BY a.hora DESC
            ''', (hoy,))
            
            return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error obteniendo asistencias: {e}")
            return []
        finally:
            conn.close()