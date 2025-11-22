import cv2
import face_recognition
import numpy as np
from datetime import datetime, time
import time
from app.utils.qr_utils import qr_manager

class AsistenciaService:
    def __init__(self, db_manager):
        self.db = db_manager
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        self.cargar_encodings()
        
        # Control de frames separado para rostro y QR
        self.frame_skip_facial = 2  # Procesar rostro cada 2 frames
        self.frame_skip_qr = 1      # Procesar QR cada frame
        self.frame_count = 0
        
        # Control de detecciones recientes
        self.estudiantes_registrados_hoy = set()
        self.cargar_registros_del_dia()
        
        # Control de QR
        self.ultimo_qr_detectado = None
        self.tiempo_ultimo_qr = 0
        self.qr_cooldown = 3  # segundos entre detecciones del mismo QR
        
        # Historial para suavizado
        self.detection_history = {}
        self.history_length = 3

    def cargar_registros_del_dia(self):
        """Cargar estudiantes ya registrados hoy para evitar duplicados"""
        try:
            registros = self.db.obtener_asistencias_del_dia()
            self.estudiantes_registrados_hoy = set(registros)
            print(f"📊 {len(self.estudiantes_registrados_hoy)} estudiantes ya registrados hoy")
        except Exception as e:
            print(f"❌ Error cargando registros del día: {e}")
            self.estudiantes_registrados_hoy = set()

    def obtener_asistencias_del_dia(self):
        """Obtiene las asistencias del día actual con información completa"""
        return self.db.obtener_asistencias_completas_del_dia()

    def obtener_estadisticas_del_dia(self):
        """Obtiene estadísticas de asistencias del día"""
        return self.db.obtener_estadisticas_del_dia()  
    
    def cargar_encodings(self):
        """Cargar encodings faciales desde la base de datos"""
        try:
            self.known_face_encodings, self.known_face_names, self.known_face_ids = self.db.cargar_encodings_faciales()
            print(f"🔍 Sistema listo con {len(self.known_face_encodings)} encodings de {len(set(self.known_face_ids))} estudiantes")
        except Exception as e:
            print(f"❌ Error cargando encodings: {e}")
            self.known_face_encodings, self.known_face_names, self.known_face_ids = [], [], []

        
    def cargar_encodings(self):
        """Cargar encodings faciales desde la base de datos"""
        try:
            self.known_face_encodings, self.known_face_names, self.known_face_ids = self.db.cargar_encodings_faciales()
            print(f"🔍 Sistema listo con {len(self.known_face_encodings)} encodings de {len(set(self.known_face_ids))} estudiantes")
        except Exception as e:
            print(f"❌ Error cargando encodings: {e}")
            self.known_face_encodings, self.known_face_names, self.known_face_ids = [], [], []

    def procesar_frame_combinado(self, frame):
            """Procesa frame para detección facial Y de QR de forma optimizada"""
            self.frame_count += 1
            
            # Siempre procesar QR (es menos costoso)
            qr_estudiantes = self.procesar_qr(frame)
            
            # Procesar rostro solo cada X frames
            if self.frame_count % self.frame_skip_facial == 0:
                face_locations, face_names, face_ids, confianzas = self.procesar_rostros(frame)
                face_locations, face_names, face_ids, confianzas = self.aplicar_suavizado(
                    face_locations, face_names, face_ids, confianzas
                )
            else:
                face_locations, face_names, face_ids, confianzas = [], [], [], []
            
            return face_locations, face_names, face_ids, confianzas, qr_estudiantes

    def procesar_rostros(self, frame):
        """Procesa detección facial optimizada"""
        # Reducir tamaño para mejor performance
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # DETECCIÓN FACIAL
        face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        
        face_names = []
        face_ids = []
        confianzas = []
        
        for face_encoding in face_encodings:
            if len(self.known_face_encodings) == 0:
                face_names.append("Desconocido")
                face_ids.append(None)
                confianzas.append(0.0)
                continue
                
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            best_distance = face_distances[best_match_index]
            confianza = 1 - best_distance
            
            if best_distance < 0.6:  # Threshold de reconocimiento
                name = self.known_face_names[best_match_index]
                estudiante_id = self.known_face_ids[best_match_index]
                
                # Registrar solo si no se ha registrado hoy
                if estudiante_id not in self.estudiantes_registrados_hoy:
                    if self.registrar_asistencia(estudiante_id, confianza, 'rostro'):
                        self.estudiantes_registrados_hoy.add(estudiante_id)
                        print(f"✅ Asistencia registrada: {name} por rostro (conf: {confianza:.2f})")
            else:
                name = "Desconocido"
                estudiante_id = None
                confianza = best_distance
            
            face_names.append(name)
            face_ids.append(estudiante_id)
            confianzas.append(confianza)
        
        # Escalar coordenadas faciales de vuelta al tamaño original
        face_locations = [(top * 2, right * 2, bottom * 2, left * 2) 
                         for (top, right, bottom, left) in face_locations]
        
        return face_locations, face_names, face_ids, confianzas
    
    def procesar_qr(self, frame):
        """Procesa detección de QR optimizada"""
        qr_estudiantes = []
        
        try:
            qr_datos = qr_manager.detectar_qr_en_frame(frame)
            
            for qr in qr_datos:
                qr_data = qr['data']
                
                # Evitar múltiples registros del mismo QR
                tiempo_actual = time.time()
                if (self.ultimo_qr_detectado == qr_data and 
                    tiempo_actual - self.tiempo_ultimo_qr < self.qr_cooldown):
                    continue
                
                # Buscar estudiante por QR
                estudiante = self.db.obtener_estudiante_por_qr(qr_data)
                if estudiante:
                    estudiante_id = estudiante[0]
                    nombre = f"{estudiante[2]} {estudiante[3]}"
                    
                    # Registrar solo si no se ha registrado hoy
                    if estudiante_id not in self.estudiantes_registrados_hoy:
                        if self.registrar_asistencia(estudiante_id, 1.0, 'qr'):
                            self.estudiantes_registrados_hoy.add(estudiante_id)
                            print(f"✅ Asistencia registrada: {nombre} por QR")
                    
                    qr_estudiantes.append({
                        'id': estudiante_id,
                        'nombre': nombre,
                        'qr_data': qr_data,
                        'rect': qr['rect']
                    })
                    
                    self.ultimo_qr_detectado = qr_data
                    self.tiempo_ultimo_qr = tiempo_actual
                    
        except Exception as e:
            print(f"❌ Error en detección QR: {e}")
        
        return qr_estudiantes

    def aplicar_suavizado(self, face_locations, face_names, face_ids, confianzas):
        """Suavizado mejorado que combina historial y detecciones actuales"""
        current_time = time.time()
        
        # Limpiar historial antiguo
        self.detection_history = {
            k: v for k, v in self.detection_history.items() 
            if current_time - v['timestamp'] < 2.0
        }
        
        # Actualizar historial con detecciones actuales
        for i, (location, name, face_id, confianza) in enumerate(zip(face_locations, face_names, face_ids, confianzas)):
            if face_id and name != "Desconocido":
                key = str(face_id)
                
                if key not in self.detection_history:
                    self.detection_history[key] = {
                        'locations': [],
                        'names': [],
                        'confianzas': [],
                        'timestamp': current_time
                    }
                
                self.detection_history[key]['locations'].append(location)
                self.detection_history[key]['names'].append(name)
                self.detection_history[key]['confianzas'].append(confianza)
                self.detection_history[key]['timestamp'] = current_time
                
                # Mantener tamaño del historial
                if len(self.detection_history[key]['locations']) > self.history_length:
                    self.detection_history[key]['locations'].pop(0)
                    self.detection_history[key]['names'].pop(0)
                    self.detection_history[key]['confianzas'].pop(0)
        
        # Combinar detecciones actuales con historial
        final_locations = []
        final_names = []
        final_ids = []
        final_confianzas = []
        
        # Primero agregar detecciones actuales
        for loc, name, fid, conf in zip(face_locations, face_names, face_ids, confianzas):
            if name != "Desconocido":
                final_locations.append(loc)
                final_names.append(name)
                final_ids.append(fid)
                final_confianzas.append(conf)
        
        # Luego agregar del historial si no están en las actuales
        current_ids = set(final_ids)
        for key, history in self.detection_history.items():
            if key not in current_ids and len(history['locations']) > 0:
                # Usar el promedio del historial
                avg_location = (
                    int(np.mean([loc[0] for loc in history['locations']])),
                    int(np.mean([loc[1] for loc in history['locations']])),
                    int(np.mean([loc[2] for loc in history['locations']])),
                    int(np.mean([loc[3] for loc in history['locations']]))
                )
                final_locations.append(avg_location)
                final_names.append(max(set(history['names']), key=history['names'].count))
                final_ids.append(int(key))
                final_confianzas.append(np.mean(history['confianzas']))
        
        return final_locations, final_names, final_ids, final_confianzas

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
    
    def registrar_asistencia(self, estudiante_id, confianza, metodo):
        """Registrar asistencia en la base de datos"""
        try:
            conn = self.db._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO asistencias (estudiante_id, fecha, hora, metodo_deteccion, estado, confianza)
                VALUES (?, DATE('now'), TIME('now'), ?, 'presente', ?)
            ''', (estudiante_id, metodo, confianza))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error registrando asistencia: {e}")
            return False
        
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