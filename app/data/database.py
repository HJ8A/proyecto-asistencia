# app/data/database.py
import sqlite3
import os
from datetime import datetime

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
                codigo TEXT UNIQUE,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                edad INTEGER,
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

    def agregar_estudiante(self, nombre, apellido, edad=None, seccion=None, codigo=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            if not codigo:
                codigo = f"{nombre[0]}{apellido[0]}{int(datetime.now().timestamp())}"

            cursor.execute("""
                INSERT INTO estudiantes (codigo, nombre, apellido, edad, seccion)
                VALUES (?, ?, ?, ?, ?)
            """, (codigo, nombre, apellido, edad, seccion))
            conn.commit()
            return cursor.lastrowid, codigo
        except Exception as e:
            print("❌ Error al agregar estudiante:", e)
            return None, None
        finally:
            conn.close()

    def obtener_estudiantes(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, codigo, nombre, apellido, edad, seccion, fecha_registro FROM estudiantes")
        data = cursor.fetchall()
        conn.close()
        return data

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
