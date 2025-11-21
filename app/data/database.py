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
            -- Tabla de niveles educativos
            CREATE TABLE IF NOT EXISTS niveles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                descripcion TEXT,
                activo BOOLEAN DEFAULT 1
            );

            -- Tabla de grados
            CREATE TABLE IF NOT EXISTS grados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nivel_id INTEGER NOT NULL,
                nombre TEXT NOT NULL,
                numero INTEGER NOT NULL,
                activo BOOLEAN DEFAULT 1,
                FOREIGN KEY (nivel_id) REFERENCES niveles (id) ON DELETE CASCADE,
                UNIQUE(nivel_id, numero)
            );

            -- Tabla de secciones
            CREATE TABLE IF NOT EXISTS secciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grado_id INTEGER NOT NULL,
                nombre TEXT NOT NULL,
                letra TEXT NOT NULL,
                capacidad INTEGER DEFAULT 30,
                activo BOOLEAN DEFAULT 1,
                FOREIGN KEY (grado_id) REFERENCES grados (id) ON DELETE CASCADE,
                UNIQUE(grado_id, letra)
            );

            -- Tabla de estudiantes
            CREATE TABLE IF NOT EXISTS estudiantes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dni TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                fecha_nacimiento DATE NOT NULL,  -- CAMBIO: edad por fecha_nacimiento
                genero TEXT CHECK(genero IN ('M','F')),  -- NUEVO: género
                telefono TEXT,
                email TEXT,  -- NUEVO: email
                direccion TEXT,  -- NUEVO: dirección
                nombre_contacto_emergencia TEXT,  -- NUEVO: contacto emergencia
                telefono_contacto_emergencia TEXT,  -- NUEVO: teléfono emergencia
                turno TEXT CHECK(turno IN ('mañana','tarde','noche')),  -- NUEVO: turno
                año_escolar INTEGER,  -- NUEVO: año escolar
                seccion_id INTEGER,
                fecha_registro DATE DEFAULT CURRENT_DATE,
                activo BOOLEAN DEFAULT 1,
                qr_code TEXT UNIQUE,
                FOREIGN KEY (seccion_id) REFERENCES secciones (id)
            );

            -- Tabla de profesores
            CREATE TABLE IF NOT EXISTS profesores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dni TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                fecha_nacimiento DATE,  -- NUEVO: fecha nacimiento
                genero TEXT CHECK(genero IN ('M','F')),  -- NUEVO: género
                email TEXT,
                telefono TEXT,
                activo BOOLEAN DEFAULT 1,
                fecha_registro DATE DEFAULT CURRENT_DATE
            );

            -- Tabla de asignación de profesores a secciones
            CREATE TABLE IF NOT EXISTS profesor_seccion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profesor_id INTEGER NOT NULL,
                seccion_id INTEGER NOT NULL,
                asignatura TEXT,
                fecha_asignacion DATE DEFAULT CURRENT_DATE,
                activo BOOLEAN DEFAULT 1,
                FOREIGN KEY (profesor_id) REFERENCES profesores (id) ON DELETE CASCADE,
                FOREIGN KEY (seccion_id) REFERENCES secciones (id) ON DELETE CASCADE,
                UNIQUE(profesor_id, seccion_id, asignatura)
            );
            -- histórico de secciones de estudiantes        
            CREATE TABLE IF NOT EXISTS historico_secciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estudiante_id INTEGER NOT NULL,
                seccion_id INTEGER NOT NULL,
                fecha_inicio DATE NOT NULL,
                fecha_fin DATE,
                activo BOOLEAN DEFAULT 1,
                FOREIGN KEY (estudiante_id) REFERENCES estudiantes (id),
                FOREIGN KEY (seccion_id) REFERENCES secciones (id)
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
                seccion_id INTEGER,
                fecha DATE NOT NULL,
                hora TIME NOT NULL,
                metodo_deteccion TEXT CHECK(metodo_deteccion IN ('rostro','qr')),
                estado TEXT CHECK(estado IN ('presente','tardanza','ausente')),
                confianza REAL,
                FOREIGN KEY (estudiante_id) REFERENCES estudiantes (id),
                FOREIGN KEY (seccion_id) REFERENCES secciones (id)
            );
                             
            CREATE TABLE IF NOT EXISTS configuracion (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                hora_entrada TIME DEFAULT '08:00:00',
                tolerancia_minutos INTEGER DEFAULT 15,
                ultima_actualizacion TIMESTAMP
            );
        """)

        # Insertar datos básicos
        cursor.execute("""
            INSERT OR IGNORE INTO configuracion (id, hora_entrada, tolerancia_minutos, ultima_actualizacion)
            VALUES (1, '08:00:00', 15, CURRENT_TIMESTAMP);
        """)

        # 1. Insertar niveles educativos básicos
        niveles = [
            (1, 'Inicial', 'Educación Inicial'),
            (2, 'Primaria', 'Educación Primaria'),
            (3, 'Secundaria', 'Educación Secundaria')
        ]
        cursor.executemany("INSERT OR IGNORE INTO niveles (id, nombre, descripcion) VALUES (?, ?, ?)", niveles)
        
        # 2. Insertar GRADOS ÚNICOS ACTIVOS
        grados_unicos = [
            # nivel_id, nombre, numero, activo
            (1, 2, 'Primaria Única', 1, 1), 
            (2, 3, 'Secundaria Única', 1, 1) 
        ]
        cursor.executemany("INSERT OR IGNORE INTO grados (id, nivel_id, nombre, numero, activo) VALUES (?, ?, ?, ?, ?)", grados_unicos)
        
        # 3. Insertar SECCIONES ÚNICAS ACTIVAS
        secciones_unicas = [
            # id, grado_id, nombre, letra, capacidad, activo
            (1, 1, 'Sección Única Primaria', 'U', 30, 1), 
            (2, 2, 'Sección Única Secundaria', 'U', 30, 1) 
        ]
        cursor.executemany("INSERT OR IGNORE INTO secciones (id, grado_id, nombre, letra, capacidad, activo) VALUES (?, ?, ?, ?, ?, ?)", secciones_unicas)        
        conn.commit()
        conn.close()

    # ---------------- MÉTODOS PARA SECCIONES ---------------- #
    
    def obtener_secciones(self):
        """Obtiene todas las secciones con información de grado y nivel"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                s.id, 
                s.nombre, 
                s.letra,
                g.nombre as grado_nombre,
                n.nombre as nivel_nombre,
                s.capacidad,
                s.activo
            FROM secciones s
            JOIN grados g ON s.grado_id = g.id
            JOIN niveles n ON g.nivel_id = n.id
            ORDER BY n.id, g.numero, s.letra
        """)
        data = cursor.fetchall()
        conn.close()
        return data

    def obtener_seccion_por_id(self, seccion_id):
        """Obtiene una sección específica por ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                s.id, 
                s.nombre, 
                s.letra,
                g.nombre as grado_nombre,
                n.nombre as nivel_nombre,
                s.capacidad,
                s.activo
            FROM secciones s
            JOIN grados g ON s.grado_id = g.id
            JOIN niveles n ON g.nivel_id = n.id
            WHERE s.id = ?
        """, (seccion_id,))
        data = cursor.fetchone()
        conn.close()
        return data

    def obtener_secciones_activas(self):
        """Obtiene solo secciones activas"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                s.id, 
                s.nombre, 
                s.letra,
                g.nombre as grado_nombre,
                n.nombre as nivel_nombre
            FROM secciones s
            JOIN grados g ON s.grado_id = g.id
            JOIN niveles n ON g.nivel_id = n.id
            WHERE s.activo = 1
            ORDER BY n.id, g.numero, s.letra
        """)
        data = cursor.fetchall()
        conn.close()
        return data

    def agregar_seccion(self, grado_id, nombre, letra, capacidad=30, activo=1):
        """Agrega una nueva sección"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO secciones (grado_id, nombre, letra, capacidad, activo)
                VALUES (?, ?, ?, ?, ?)
            """, (grado_id, nombre, letra, capacidad, activo))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError("La sección ya existe")
        except Exception as e:
            print("❌ Error al agregar sección:", e)
            return None
        finally:
            conn.close()

    def actualizar_seccion(self, seccion_id, grado_id, nombre, letra, capacidad, activo):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE secciones 
                SET grado_id=?, nombre=?, letra=?, capacidad=?, activo=?
                WHERE id=?
            """, (grado_id, nombre, letra, capacidad, activo, seccion_id))
            conn.commit()
            return True
        except Exception as e:
            print("❌ Error al actualizar sección:", e)
            return False
        finally:
            conn.close()


    def desactivar_seccion(self, seccion_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE secciones SET activo = 0 WHERE id = ?", (seccion_id,))
            conn.commit()
            return True
        except Exception as e:
            print("❌ Error al desactivar sección:", e)
            return False
        finally:
            conn.close()

    def reactivar_seccion(self, seccion_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE secciones SET activo = 1 WHERE id = ?", (seccion_id,))
            conn.commit()
            return True
        except Exception as e:
            print("❌ Error al reactivar sección:", e)
            return False
        finally:
            conn.close()
            
    # ---------------- MÉTODOS PARA GRADOS ---------------- #
    
    def obtener_grados(self):
        """Obtiene todos los grados con información de nivel"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                g.id,
                g.nombre,
                g.numero,
                n.nombre as nivel_nombre,
                g.activo
            FROM grados g
            JOIN niveles n ON g.nivel_id = n.id
            ORDER BY n.id, g.numero
        """)
        data = cursor.fetchall()
        conn.close()
        return data

    def obtener_grados_por_nivel(self, nivel_id):
        """Obtiene grados por nivel específico"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nombre, numero
            FROM grados 
            WHERE nivel_id = ? AND activo = 1
            ORDER BY numero
        """, (nivel_id,))
        data = cursor.fetchall()
        conn.close()
        return data

    # ---------------- MÉTODOS PARA NIVELES ---------------- #
    
    def obtener_niveles(self):
        """Obtiene todos los niveles educativos"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, descripcion FROM niveles WHERE activo = 1 ORDER BY id")
        data = cursor.fetchall()
        conn.close()
        return data

    def obtener_nivel_por_id(self, nivel_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, descripcion FROM niveles WHERE id = ?", (nivel_id,))
        data = cursor.fetchone()
        conn.close()
        return data

    def actualizar_nivel(self, nivel_id, nombre, descripcion):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE niveles 
                SET nombre=?, descripcion=?
                WHERE id=?
            """, (nombre, descripcion, nivel_id))
            conn.commit()
            return True
        except Exception as e:
            print("❌ Error al actualizar nivel:", e)
            return False
        finally:
            conn.close()

    # ---------------- MÉTODOS PARA ESTUDIANTES ---------------- #

    def agregar_estudiante(self, dni, nombre, apellido, fecha_nacimiento, genero, telefono, email, direccion, nombre_contacto_emergencia, telefono_contacto_emergencia, turno, año_escolar, seccion_id=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO estudiantes (dni, nombre, apellido, fecha_nacimiento, genero, telefono, email, direccion, nombre_contacto_emergencia, telefono_contacto_emergencia, turno, año_escolar, seccion_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (dni, nombre, apellido, fecha_nacimiento, genero, telefono, email, direccion, nombre_contacto_emergencia, telefono_contacto_emergencia, turno, año_escolar, seccion_id))
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
        cursor.execute("""
            SELECT 
                e.id, 
                e.dni, 
                e.nombre, 
                e.apellido, 
                e.fecha_nacimiento,
                e.genero,
                e.telefono,
                e.email,
                s.nombre as seccion_nombre,
                e.fecha_registro
            FROM estudiantes e
            LEFT JOIN secciones s ON e.seccion_id = s.id
        """)
        data = cursor.fetchall()
        conn.close()
        return data
    
    def obtener_estudiante_por_id(self, estudiante_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                e.id, 
                e.dni, 
                e.nombre, 
                e.apellido, 
                e.fecha_nacimiento,
                e.genero,
                e.telefono,
                e.email,
                e.direccion,
                e.nombre_contacto_emergencia,
                e.telefono_contacto_emergencia,
                e.turno,
                e.año_escolar,
                e.seccion_id,
                s.nombre as seccion_nombre,
                e.fecha_registro, 
                e.activo, 
                e.qr_code
            FROM estudiantes e
            LEFT JOIN secciones s ON e.seccion_id = s.id
            WHERE e.id = ?
        """, (estudiante_id,))
        data = cursor.fetchone()
        conn.close()
        return data

    def actualizar_estudiante(self, estudiante_id, dni, nombre, apellido, fecha_nacimiento, genero, telefono, email, direccion, nombre_contacto_emergencia, telefono_contacto_emergencia, turno, año_escolar, seccion_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE estudiantes 
                SET dni=?, nombre=?, apellido=?, fecha_nacimiento=?, genero=?, telefono=?, email=?, direccion=?, nombre_contacto_emergencia=?, telefono_contacto_emergencia=?, turno=?, año_escolar=?, seccion_id=?
                WHERE id=?
            """, (dni, nombre, apellido, fecha_nacimiento, genero, telefono, email, direccion, nombre_contacto_emergencia, telefono_contacto_emergencia, turno, año_escolar, seccion_id, estudiante_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            raise ValueError("El DNI ya existe en la base de datos")
        except Exception as e:
            print("❌ Error al actualizar estudiante:", e)
            return False
        finally:
            conn.close()

    def obtener_estudiantes_por_seccion(self, seccion_id):
        """Obtiene estudiantes por sección específica"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                id, dni, nombre, apellido, fecha_nacimiento, genero, telefono, email, fecha_registro
            FROM estudiantes 
            WHERE seccion_id = ? AND activo = 1
            ORDER BY apellido, nombre
        """, (seccion_id,))
        data = cursor.fetchall()
        conn.close()
        return data

    # ---------------- MÉTODOS MODIFICADOS PARA ASISTENCIAS ---------------- #

    def registrar_asistencia(self, estudiante_id, metodo_deteccion, confianza):
        """Registrar una asistencia en la base de datos"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Obtener la sección del estudiante
            cursor.execute("SELECT seccion_id FROM estudiantes WHERE id = ?", (estudiante_id,))
            estudiante = cursor.fetchone()
            seccion_id = estudiante[0] if estudiante else None
            
            cursor.execute('''
                INSERT INTO asistencias (estudiante_id, seccion_id, fecha, hora, metodo_deteccion, estado, confianza)
                VALUES (?, ?, DATE('now'), TIME('now'), ?, 'presente', ?)
            ''', (estudiante_id, seccion_id, metodo_deteccion, confianza))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Error al registrar asistencia: {e}")
            return False
        finally:
            conn.close()

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
                s.nombre as seccion_nombre,
                a.hora, 
                a.metodo_deteccion, 
                a.confianza
            FROM asistencias a
            JOIN estudiantes e ON a.estudiante_id = e.id
            LEFT JOIN secciones s ON e.seccion_id = s.id
            WHERE a.fecha = ?
            ORDER BY a.hora DESC
        """, (fecha_actual,))
        
        asistencias = cursor.fetchall()
        conn.close()
        return asistencias

    def obtener_asistencias_por_seccion(self, seccion_id, fecha=None):
        """Obtiene asistencias por sección y fecha"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if fecha is None:
            fecha = datetime.now().date()
        
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
            WHERE a.seccion_id = ? AND a.fecha = ?
            ORDER BY a.hora DESC
        """, (seccion_id, fecha))
        
        asistencias = cursor.fetchall()
        conn.close()
        return asistencias

    # ---------------- MÉTODOS EXISTENTES ---------------- #

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
            SELECT 
                e.id, 
                e.dni, 
                e.nombre, 
                e.apellido, 
                e.fecha_nacimiento,  -- CAMBIAR: edad por fecha_nacimiento
                e.genero,
                e.telefono,
                e.email,
                s.nombre as seccion_nombre,
                e.fecha_registro 
            FROM estudiantes e
            LEFT JOIN secciones s ON e.seccion_id = s.id
            WHERE e.activo = 1
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
            SELECT 
                e.id, 
                e.dni, 
                e.nombre, 
                e.apellido, 
                e.fecha_nacimiento,  -- CAMBIAR: edad por fecha_nacimiento
                e.genero,
                e.telefono,
                e.email,
                s.nombre as seccion_nombre,
                e.fecha_registro 
            FROM estudiantes e
            LEFT JOIN secciones s ON e.seccion_id = s.id
            WHERE e.activo = 0
        """)
        data = cursor.fetchall()
        conn.close()
        return data

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
                SELECT 
                    e.id, 
                    e.dni, 
                    e.nombre, 
                    e.apellido, 
                    e.fecha_nacimiento,
                    e.seccion_id,
                    s.nombre as seccion_nombre
                FROM estudiantes e
                LEFT JOIN secciones s ON e.seccion_id = s.id
                WHERE e.qr_code = ? AND e.activo = 1
            """, (qr_data,))
            data = cursor.fetchone()
            return data
        except Exception as e:
            print(f"❌ Error obteniendo estudiante por QR: {e}")
            return None
        finally:
            conn.close()
   
    # -------------------------- PROFESORES -----------------------------   

    def desactivar_profesor(self, profesor_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE profesores SET activo = 0 WHERE id = ?", (profesor_id,))
            conn.commit()
            return True
        except Exception as e:
            print("❌ Error al desactivar profesor:", e)
            return False
        finally:
            conn.close()

    def reactivar_profesor(self, profesor_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE profesores SET activo = 1 WHERE id = ?", (profesor_id,))
            conn.commit()
            return True
        except Exception as e:
            print("❌ Error al reactivar profesor:", e)
            return False
        finally:
            conn.close()

    def obtener_profesores_activos(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, dni, nombre, apellido, email, telefono FROM profesores WHERE activo = 1")
        data = cursor.fetchall()
        conn.close()
        return data

    def obtener_profesores_inactivos(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, dni, nombre, apellido, email, telefono FROM profesores WHERE activo = 0")
        data = cursor.fetchall()
        conn.close()
        return data

    def verificar_dni_profesor_existente(self, dni):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM profesores WHERE dni = ?", (dni,))
            resultado = cursor.fetchone()
            return resultado is not None
        except Exception as e:
            print("❌ Error al verificar DNI de profesor:", e)
            return False
        finally:
            conn.close()

    def agregar_profesor(self, dni, nombre, apellido, fecha_nacimiento, genero, email=None, telefono=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO profesores (dni, nombre, apellido, fecha_nacimiento, genero, email, telefono)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (dni, nombre, apellido, fecha_nacimiento, genero, email, telefono))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError("El DNI ya existe en la base de datos")
        except Exception as e:
            print("❌ Error al agregar profesor:", e)
            return None
        finally:
            conn.close()

    def obtener_profesores(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, dni, nombre, apellido, fecha_nacimiento, genero, email, telefono, activo, fecha_registro 
            FROM profesores
        """)
        data = cursor.fetchall()
        conn.close()
        return data

    def obtener_profesor_por_id(self, profesor_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, dni, nombre, apellido, fecha_nacimiento, genero, email, telefono, activo 
            FROM profesores WHERE id = ?
        """, (profesor_id,))
        data = cursor.fetchone()
        conn.close()
        return data

    def actualizar_profesor(self, profesor_id, dni, nombre, apellido, fecha_nacimiento, genero, email, telefono):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE profesores 
                SET dni=?, nombre=?, apellido=?, fecha_nacimiento=?, genero=?, email=?, telefono=?
                WHERE id=?
            """, (dni, nombre, apellido, fecha_nacimiento, genero, email, telefono, profesor_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            raise ValueError("El DNI ya existe en la base de datos")
        except Exception as e:
            print("❌ Error al actualizar profesor:", e)
            return False
        finally:
            conn.close()

    # ---------------- MÉTODOS PARA GRADOS ---------------- #

    def agregar_grado(self, nivel_id, nombre, numero):
        """Agrega un nuevo grado"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO grados (nivel_id, nombre, numero)
                VALUES (?, ?, ?)
            """, (nivel_id, nombre, numero))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError("El grado ya existe para este nivel")
        except Exception as e:
            print("❌ Error al agregar grado:", e)
            return None
        finally:
            conn.close()

    def actualizar_grado(self,nivel_id, grado_id, nombre, numero, activo):
        """Actualiza un grado existente"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE grados 
                SET nivel_id=?, nombre=?, numero=?, activo=?
                WHERE id=?
            """, (nivel_id, nombre, numero, activo, grado_id))
            conn.commit()
            return True
        except Exception as e:
            print("❌ Error al actualizar grado:", e)
            return False
        finally:
            conn.close()

    def obtener_grado_por_id(self, grado_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nivel_id, nombre, numero, activo
            FROM grados 
            WHERE id = ?
        """, (grado_id,))
        data = cursor.fetchone()
        conn.close()
        return data

    def obtener_grados_activos(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                g.id,
                g.nombre,
                g.numero,
                n.nombre as nivel_nombre,
                g.activo
            FROM grados g
            JOIN niveles n ON g.nivel_id = n.id
            WHERE g.activo = 1
            ORDER BY n.id, g.numero
        """)
        data = cursor.fetchall()
        conn.close()
        return data

    def desactivar_grado(self, grado_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE grados SET activo = 0 WHERE id = ?", (grado_id,))
            conn.commit()
            return True
        except Exception as e:
            print("❌ Error al desactivar grado:", e)
            return False
        finally:
            conn.close()
            
    # ---------------- MÉTODOS PARA HISTÓRICO ---------------- #

    def registrar_cambio_seccion(self, estudiante_id, seccion_id):
        """Registra un cambio de sección en el histórico"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Primero, marcar como inactivo el registro anterior si existe
            cursor.execute("""
                UPDATE historico_secciones 
                SET fecha_fin = DATE('now'), activo = 0 
                WHERE estudiante_id = ? AND activo = 1
            """, (estudiante_id,))
            
            # Luego, crear nuevo registro
            cursor.execute("""
                INSERT INTO historico_secciones (estudiante_id, seccion_id, fecha_inicio)
                VALUES (?, ?, DATE('now'))
            """, (estudiante_id, seccion_id))
            
            conn.commit()
            return True
        except Exception as e:
            print("❌ Error al registrar cambio de sección:", e)
            return False
        finally:
            conn.close()

