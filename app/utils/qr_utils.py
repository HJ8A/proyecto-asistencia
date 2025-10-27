import cv2
import numpy as np
import qrcode
from pyzbar.pyzbar import decode
import io
from PIL import Image

class QRManager:
    def __init__(self):
        pass
    
    def generar_qr_imagen(self, data, size=200):
        """Genera una imagen QR a partir de datos"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize((size, size))
        
        return qr_img
    
    def detectar_qr_en_frame(self, frame):
        """Detecta y decodifica códigos QR en un frame de cámara"""
        try:
            # Convertir frame de OpenCV a formato PIL
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detectar QR codes
            decoded_objects = decode(gray)
            
            qr_datos = []
            for obj in decoded_objects:
                if obj.type == 'QRCODE':
                    qr_data = obj.data.decode('utf-8')
                    qr_datos.append({
                        'data': qr_data,
                        'polygon': obj.polygon,
                        'rect': obj.rect
                    })
            
            return qr_datos
        except Exception as e:
            print(f"❌ Error detectando QR: {e}")
            return []
    
    def dibujar_qr_detectado(self, frame, qr_datos):
        """Dibuja rectángulos alrededor de los QR detectados"""
        for qr in qr_datos:
            points = qr['polygon']
            rect = qr['rect']
            
            # Dibujar polígono alrededor del QR
            if len(points) == 4:
                pts = np.array(points, np.int32)
                pts = pts.reshape((-1, 1, 2))
                cv2.polylines(frame, [pts], True, (255, 0, 255), 3)
            
            # Dibujar texto con los datos (truncado para no saturar)
            texto = f"QR: {qr['data'][:15]}..."
            cv2.putText(frame, texto, (rect.left, rect.top - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
        
        return frame

# Instancia global para fácil acceso
qr_manager = QRManager()