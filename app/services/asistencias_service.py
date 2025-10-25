import cv2
from datetime import datetime
from app.utils.camara_utils import CamaraManager

class AsistenciaService:
    def __init__(self, db_manager):
        self.db = db_manager
        self.camara = CamaraManager(db_manager)

    def iniciar_reconocimiento(self):
        """Inicia el reconocimiento facial desde una ventana externa."""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise Exception("No se pudo acceder a la cámara")

        print("🚀 Reconocimiento iniciado. Presiona 'q' para salir.")
        registrados = set()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            rostros = self.camara.detectar_rostros(frame)
            for (x, y, w, h) in rostros:
                nombre, estudiante_id, confianza = self.camara.reconocer_rostro(frame, x, y, w, h)
                if nombre and estudiante_id:
                    # Evitar múltiples registros de la misma persona en la sesión
                    if estudiante_id not in registrados:
                        registrado = self.db.registrar_asistencia(estudiante_id, "rostro", confianza)
                        if registrado:
                            registrados.add(estudiante_id)
                            print(f"✅ {nombre} registrado ({confianza:.2f})")
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
                    cv2.putText(frame, nombre, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

            cv2.imshow("Reconocimiento de Asistencias", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    def obtener_asistencias_del_dia(self):
        return self.db.obtener_asistencias_hoy()
