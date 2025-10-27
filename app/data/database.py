# app/data/database.py
import sqlite3
import os
from datetime import datetime
import qrcode
import io
import base64
import uuid

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
DB_PATH = os.path.join(BASE_DIR, "asistencias.db")

class DatabaseManager:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._init_database()

    def _get_connection(self):
        return sqlite3.connect(DB_PATH)

    def _init_database(self):
        """Crea las tablas si no existen"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS estudiantes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dni TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                edad INTEGER NOT NULL,
                seccion TEXT,
                fecha_registro DATE DEFAULT CURRENT_DATE,
                activo BOOLEAN DEFAULT 1,
                qr_code TEXT UNIQUE
            );

            CREATE TABLE IF NOT EXISTS encodings_faciales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estudiante_id INTEGER,
                encoding_data BLOB,
                imagen_path TEXT,
                fecha_creacion DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (estudiante_id) REFERENCES estudiantes (id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS asistencias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estudiante_id INTEGER,
                fecha DATE NOT NULL,
                hora TIME NOT NULL,
                metodo_deteccion TEXT CHECK(metodo_deteccion IN ('rostro','qr')),
                estado TEXT CHECK(estado IN ('presente','tardanza','ausente')),
                confianza REAL,
                FOREIGN KEY (estudiante_id) REFERENCES estudiantes (id)
            );

            CREATE TABLE IF NOT EXISTS configuracion (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                hora_entrada TIME DEFAULT '08:00:00',
                tolerancia_minutos INTEGER DEFAULT 15,
                ultima_actualizacion TIMESTAMP
            );
        """)

        cursor.execute("""
            INSERT OR IGNORE INTO configuracion (id, hora_entrada, tolerancia_minutos, ultima_actualizacion)
            VALUES (1, '08:00:00', 15, CURRENT_TIMESTAMP);
        """)

        conn.commit()
        conn.close()

    # ---------------- MÉTODOS DE OPERACIONES ---------------- #
    def generar_qr_estudiante(self, estudiante_id, dni, nombre, apellido):
        """Genera un código QR único para el estudiante"""
        # Crear un identificador único
        qr_data = f"EST_{estudiante_id}_{dni}_{uuid.uuid4().hex[:8]}"
        
        # Generar QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Crear imagen QR
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        return qr_data, qr_img


    def agregar_estudiante(self, dni, nombre, apellido, edad, seccion=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO estudiantes (dni, nombre, apellido, edad, seccion)
                VALUES (?, ?, ?, ?, ?)
            """, (dni, nombre, apellido, edad, seccion))
            estudiante_id = cursor.lastrowid
            
            # Generar y guardar QR
            qr_data, qr_img = self.generar_qr_estudiante(estudiante_id, dni, nombre, apellido)
            cursor.execute("UPDATE estudiantes SET qr_code = ? WHERE id = ?", (qr_data, estudiante_id))
            
            conn.commit()
            return estudiante_id
        except sqlite3.IntegrityError:
            raise ValueError("El DNI ya existe en la base de datos")
        except Exception as e:
            print("❌ Error al agregar estudiante:", e)
            return None
        finally:
            conn.close()

    def obtener_estudiantes(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, dni, nombre, apellido, edad, seccion, fecha_registro FROM estudiantes")
        data = cursor.fetchall()
        conn.close()
        return data

    def obtener_estudiante_por_id(self, estudiante_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, dni, nombre, apellido, edad, seccion, fecha_registro, activo, qr_code 
            FROM estudiantes WHERE id = ?
        """, (estudiante_id,))
        data = cursor.fetchone()
        conn.close()
        return data

    def actualizar_estudiante(self, estudiante_id, dni, nombre, apellido, edad, seccion):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE estudiantes 
                SET dni=?, nombre=?, apellido=?, edad=?, seccion=?
                WHERE id=?
            """, (dni, nombre, apellido, edad, seccion, estudiante_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            raise ValueError("El DNI ya existe en la base de datos")
        except Exception as e:
            print("❌ Error al actualizar estudiante:", e)
            return False
        finally:
            conn.close()

    def guardar_encoding_facial(self, estudiante_id, encoding, imagen_path):
        import pickle
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO encodings_faciales (estudiante_id, encoding_data, imagen_path)
                VALUES (?, ?, ?)
            """, (estudiante_id, pickle.dumps(encoding), imagen_path))
            conn.commit()
            print(f"✅ Encoding facial guardado para estudiante {estudiante_id}")
        except Exception as e:
            print("⚠️ Error guardando encoding facial:", e)
        finally:
            conn.close()

    def cargar_encodings_faciales(self):
        import pickle
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.nombre, ef.encoding_data, ef.estudiante_id
            FROM encodings_faciales ef
            JOIN estudiantes e ON ef.estudiante_id = e.id
        """)
        data = cursor.fetchall()
        conn.close()

        nombres, encodings, ids = [], [], []
        for nombre, enc, eid in data:
            nombres.append(nombre)
            ids.append(eid)
            encodings.append(pickle.loads(enc))
        return encodings, nombres, ids
    
    def registrar_asistencia(self, estudiante_id, metodo_deteccion, confianza):
        """Registrar una asistencia en la base de datos"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO asistencias (estudiante_id, fecha, hora, metodo_deteccion, estado, confianza)
                VALUES (?, DATE('now'), TIME('now'), ?, 'presente', ?)
            ''', (estudiante_id, metodo_deteccion, confianza))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Error al registrar asistencia: {e}")
            return False
        finally:
            conn.close()

    def desactivar_estudiante(self, estudiante_id):
        """Desactiva un estudiante (eliminación lógica)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE estudiantes SET activo = 0 WHERE id = ?", (estudiante_id,))
            conn.commit()
            return True
        except Exception as e:
            print("❌ Error al desactivar estudiante:", e)
            return False
        finally:
            conn.close()

    def obtener_estudiantes_activos(self):
        """Obtiene solo estudiantes activos"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, dni, nombre, apellido, edad, seccion, fecha_registro 
            FROM estudiantes 
            WHERE activo = 1
        """)
        data = cursor.fetchall()
        conn.close()
        return data
    
    def reactivar_estudiante(self, estudiante_id):
        """Reactiva un estudiante"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE estudiantes SET activo = 1 WHERE id = ?", (estudiante_id,))
            conn.commit()
            return True
        except Exception as e:
            print("❌ Error al reactivar estudiante:", e)
            return False
        finally:
            conn.close()

    def obtener_estudiantes_inactivos(self):

        """Obtiene estudiantes inactivos"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, dni, nombre, apellido, edad, seccion, fecha_registro 
            FROM estudiantes 
            WHERE activo = 0
        """)
        data = cursor.fetchall()
        conn.close()
        return data
    
    def obtener_asistencias_hoy(self):
        """Obtiene todas las asistencias registradas en la fecha actual"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        fecha_actual = datetime.now().date()
        
        cursor.execute("""
            SELECT 
                e.nombre, 
                e.apellido, 
                e.dni, 
                a.hora, 
                a.metodo_deteccion, 
                a.confianza
            FROM asistencias a
            JOIN estudiantes e ON a.estudiante_id = e.id
            WHERE a.fecha = ?
            ORDER BY a.hora DESC
        """, (fecha_actual,))
        
        asistencias = cursor.fetchall()
        conn.close()
        return asistencias

    def verificar_dni_existente(self, dni):
        """Verifica si un DNI ya existe en la base de datos"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM estudiantes WHERE dni = ?", (dni,))
            resultado = cursor.fetchone()
            return resultado is not None
        except Exception as e:
            print("❌ Error al verificar DNI:", e)
            return False
        finally:
            conn.close()

    def obtener_estudiante_por_qr(self, qr_data):
        """Obtiene estudiante por código QR"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, dni, nombre, apellido, edad, seccion 
                FROM estudiantes 
                WHERE qr_code = ? AND activo = 1
            """, (qr_data,))
            data = cursor.fetchone()
            return data
        except Exception as e:
            print(f"❌ Error obteniendo estudiante por QR: {e}")
            return None
        finally:
            conn.close()


