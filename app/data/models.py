# app/data/models.py
from datetime import datetime
import numpy as np
from app.data.database import get_connection

class EstudianteModel:
    @staticmethod
    def agregar(nombre, apellido, edad=None, seccion=None, codigo=None, qr_code=None):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            if not codigo:
                cursor.execute("SELECT COALESCE(MAX(CAST(codigo AS INTEGER)), 0) FROM estudiantes WHERE codigo GLOB '[0-9]*'")
                max_codigo = cursor.fetchone()[0]
                codigo = str(int(max_codigo) + 1)

            cursor.execute("""
                INSERT INTO estudiantes (codigo, nombre, apellido, edad, seccion, fecha_registro, qr_code)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (codigo, nombre, apellido, edad, seccion, datetime.now().date(), qr_code))
            conn.commit()
            return cursor.lastrowid, codigo
        except Exception as e:
            print("❌ Error al agregar estudiante:", e)
            return None, None
        finally:
            conn.close()

    @staticmethod
    def listar():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, codigo, nombre, apellido, edad, seccion, fecha_registro
            FROM estudiantes
            WHERE activo = 1
            ORDER BY nombre, apellido
        """)
        data = cursor.fetchall()
        conn.close()
        return data

    @staticmethod
    def buscar_por_codigo(codigo):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nombre, apellido FROM estudiantes WHERE codigo = ? AND activo = 1
        """, (codigo,))
        result = cursor.fetchone()
        conn.close()
        return result


class EncodingFacialModel:
    @staticmethod
    def guardar(estudiante_id, encoding):
        conn = get_connection()
        cursor = conn.cursor()
        encoding_bytes = encoding.tobytes()
        cursor.execute("""
            INSERT INTO encodings_faciales (estudiante_id, encoding_data, fecha_creacion)
            VALUES (?, ?, ?)
        """, (estudiante_id, encoding_bytes, datetime.now().date()))
        conn.commit()
        conn.close()

    @staticmethod
    def cargar_todos():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.estudiante_id, est.nombre, est.apellido, e.encoding_data
            FROM encodings_faciales e
            JOIN estudiantes est ON e.estudiante_id = est.id
            WHERE est.activo = 1
        """)
        encodings, nombres, ids = [], [], []
        for row in cursor.fetchall():
            estudiante_id, nombre, apellido, encoding_bytes = row
            encodings.append(np.frombuffer(encoding_bytes, dtype=np.float64))
            nombres.append(f"{nombre} {apellido}")
            ids.append(estudiante_id)
        conn.close()
        return encodings, nombres, ids


class AsistenciaModel:
    @staticmethod
    def registrar(estudiante_id, metodo_deteccion, confianza=1.0):
        conn = get_connection()
        cursor = conn.cursor()
        ahora = datetime.now()
        fecha, hora = ahora.date(), ahora.strftime('%H:%M:%S')

        cursor.execute('SELECT hora_entrada, tolerancia_minutos FROM configuracion WHERE id = 1')
        config = cursor.fetchone()
        if config:
            hora_entrada, tolerancia = config
            hora_limite = datetime.strptime(hora_entrada, '%H:%M:%S')
            hora_limite = hora_limite.replace(minute=hora_limite.minute + tolerancia)
            estado = 'tardanza' if ahora.time() > hora_limite.time() else 'presente'
        else:
            estado = 'presente'

        cursor.execute("""
            INSERT INTO asistencias (estudiante_id, fecha, hora, metodo_deteccion, estado, confianza)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (estudiante_id, fecha, hora, metodo_deteccion, estado, confianza))
        conn.commit()
        conn.close()
        return estado
