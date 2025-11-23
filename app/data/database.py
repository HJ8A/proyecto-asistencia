import sqlite3
import os
import qrcode
from datetime import datetime, date, time, timedelta

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
            # PRIMERO verificar si el DNI ya existe
            cursor.execute("SELECT id FROM estudiantes WHERE dni = ?", (dni,))
            if cursor.fetchone():
                raise ValueError("El DNI ya existe en la base de datos")
            
            # Insertar estudiante
            cursor.execute("""
                INSERT INTO estudiantes (dni, nombre, apellido, fecha_nacimiento, genero, telefono, email, direccion, nombre_contacto_emergencia, telefono_contacto_emergencia, turno, año_escolar, seccion_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (dni, nombre, apellido, fecha_nacimiento, genero, telefono, email, direccion, nombre_contacto_emergencia, telefono_contacto_emergencia, turno, año_escolar, seccion_id))
            
            estudiante_id = cursor.lastrowid
            
            # Generar y guardar QR único
            qr_data, qr_img = self.generar_qr_estudiante(estudiante_id, dni, nombre, apellido)
            
            if qr_data:
                cursor.execute("UPDATE estudiantes SET qr_code = ? WHERE id = ?", (qr_data, estudiante_id))
                print(f"✅ QR guardado para estudiante {estudiante_id}: {qr_data}")
            else:
                print(f"⚠️ No se pudo generar QR para estudiante {estudiante_id}")
                # No hacemos rollback, el estudiante se crea igual pero sin QR
            
            conn.commit()
            return estudiante_id
            
        except sqlite3.IntegrityError as e:
            conn.rollback()
            if "dni" in str(e).lower():
                raise ValueError("El DNI ya existe en la base de datos")
            elif "qr_code" in str(e).lower():
                # Colisión de QR, intentar nuevamente
                print("🔄 Colisión de QR, regenerando...")
                if 'estudiante_id' in locals():
                    qr_data, qr_img = self.generar_qr_estudiante(estudiante_id, dni, nombre, apellido)
                    if qr_data:
                        cursor.execute("UPDATE estudiantes SET qr_code = ? WHERE id = ?", (qr_data, estudiante_id))
                        conn.commit()
                        return estudiante_id
                raise ValueError("Error al generar código QR único")
            else:
                raise ValueError(f"Error de integridad en la base de datos: {e}")
        except Exception as e:
            conn.rollback()
            print(f"❌ Error al agregar estudiante: {e}")
            raise ValueError(f"Error al agregar estudiante: {e}")
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
    
    def obtener_estudiantes_sin_qr(self):
        """Obtiene estudiantes que no tienen código QR"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, dni, nombre, apellido 
                FROM estudiantes 
                WHERE (qr_code IS NULL OR qr_code = '') AND activo = 1
            """)
            return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error obteniendo estudiantes sin QR: {e}")
            return []
        finally:
            conn.close()
    # ---------------- MÉTODOS MODIFICADOS PARA ASISTENCIAS ---------------- #
    def registrar_asistencia(self, estudiante_id, metodo_deteccion, confianza=None):
        """Registra una asistencia con todos los campos necesarios"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. Obtener datos del estudiante y sección
            cursor.execute("""
                SELECT e.seccion_id, s.nombre as seccion_nombre
                FROM estudiantes e
                LEFT JOIN secciones s ON e.seccion_id = s.id
                WHERE e.id = ? AND e.activo = 1
            """, (estudiante_id,))
            
            estudiante_data = cursor.fetchone()
            if not estudiante_data:
                print(f"❌ Estudiante {estudiante_id} no encontrado o inactivo")
                return False
                
            seccion_id = estudiante_data[0]
            
            # 2. Verificar si ya se registró hoy (para evitar duplicados)
            hoy = date.today()
            cursor.execute("""
                SELECT id FROM asistencias 
                WHERE estudiante_id = ? AND fecha = ? AND metodo_deteccion = ?
            """, (estudiante_id, hoy, metodo_deteccion))
            
            if cursor.fetchone():
                print(f"⚠️ Asistencia ya registrada hoy para estudiante {estudiante_id}")
                return True  # O False si quieres evitar duplicados completamente
            
            # 3. Determinar estado (presente/tardanza) según configuración
            cursor.execute("SELECT hora_entrada, tolerancia_minutos FROM configuracion WHERE id=1")
            config = cursor.fetchone()
            hora_entrada_str = config[0] if config else '08:00:00'
            tolerancia = config[1] if config else 15
            
            # Convertir y calcular tiempos
            hora_entrada = datetime.strptime(hora_entrada_str, '%H:%M:%S').time()
            hora_actual = datetime.now().time()
            estado = 'presente'
            
            # Calcular hora límite para tardanza
            hora_limite = self._calcular_hora_limite(hora_entrada, tolerancia)
            if hora_actual > hora_limite:
                estado = 'tardanza'
            
            # 4. Registrar asistencia
            cursor.execute("""
                INSERT INTO asistencias 
                (estudiante_id, seccion_id, fecha, hora, metodo_deteccion, estado, confianza)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                estudiante_id,
                seccion_id,
                hoy,
                hora_actual,
                metodo_deteccion,
                estado,
                confianza
            ))
            
            # 5. Obtener nombre del estudiante para el log
            cursor.execute("SELECT nombre, apellido FROM estudiantes WHERE id = ?", (estudiante_id,))
            estudiante_info = cursor.fetchone()
            nombre_completo = f"{estudiante_info[0]} {estudiante_info[1]}" if estudiante_info else "Desconocido"
            
            conn.commit()
            print(f"✅ Asistencia registrada: {nombre_completo} - {metodo_deteccion} - {estado}")
            return True
            
        except sqlite3.Error as e:
            print(f"❌ Error al registrar asistencia: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def _calcular_hora_limite(self, hora_entrada, tolerancia_minutos):
        """Calcula la hora límite para considerar tardanza"""
        hora_limite = datetime.combine(date.today(), hora_entrada)
        hora_limite += timedelta(minutes=tolerancia_minutos)
        return hora_limite.time()

    def consultar_asistencias_por_fecha(fecha_consulta=None, seccion_id=None):
        """Consulta asistencias por fecha y opcionalmente por sección"""
        conn = sqlite3.connect('tu_base_de_datos.db')
        cursor = conn.cursor()
        
        try:
            if fecha_consulta is None:
                fecha_consulta = date.today()
            
            query = """
                SELECT 
                    a.fecha,
                    a.hora,
                    e.nombre || ' ' || e.apellido as estudiante,
                    e.dni,
                    s.nombre as seccion,
                    g.nombre as grado,
                    n.nombre as nivel,
                    a.metodo_deteccion,
                    a.estado,
                    a.confianza
                FROM asistencias a
                JOIN estudiantes e ON a.estudiante_id = e.id
                LEFT JOIN secciones s ON a.seccion_id = s.id
                LEFT JOIN grados g ON s.grado_id = g.id
                LEFT JOIN niveles n ON g.nivel_id = n.id
                WHERE a.fecha = ?
            """
            
            params = [fecha_consulta]
            
            if seccion_id:
                query += " AND a.seccion_id = ?"
                params.append(seccion_id)
                
            query += " ORDER BY a.hora ASC"
            
            cursor.execute(query, params)
            asistencias = cursor.fetchall()
            
            return asistencias
            
        except sqlite3.Error as e:
            print(f"❌ Error en consulta: {e}")
            return []
        finally:
            conn.close()

    def obtener_asistencias_hoy(self):
        """Obtiene todas las asistencias del día actual con información completa"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            fecha_actual = date.today()
            
            cursor.execute("""
                SELECT 
                    a.id,
                    e.nombre,
                    e.apellido, 
                    e.dni,
                    s.nombre as seccion_nombre,
                    a.hora,
                    a.metodo_deteccion,
                    a.confianza,
                    a.estado
                FROM asistencias a
                JOIN estudiantes e ON a.estudiante_id = e.id
                LEFT JOIN secciones s ON a.seccion_id = s.id
                WHERE a.fecha = ?
                ORDER BY a.hora DESC
            """, (fecha_actual,))
            
            return cursor.fetchall()
            
        except Exception as e:
            print(f"❌ Error obteniendo asistencias de hoy: {e}")
            return []
        finally:
            conn.close()

    def obtener_estadisticas_hoy(self):
        """Obtiene estadísticas de asistencias del día actual"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            fecha_actual = date.today()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_asistencias,
                    COUNT(DISTINCT estudiante_id) as estudiantes_unicos,
                    SUM(CASE WHEN estado = 'presente' THEN 1 ELSE 0 END) as presentes,
                    SUM(CASE WHEN estado = 'tardanza' THEN 1 ELSE 0 END) as tardanzas,
                    SUM(CASE WHEN metodo_deteccion = 'rostro' THEN 1 ELSE 0 END) as por_rostro,
                    SUM(CASE WHEN metodo_deteccion = 'qr' THEN 1 ELSE 0 END) as por_qr
                FROM asistencias 
                WHERE fecha = ?
            """, (fecha_actual,))
            
            stats = cursor.fetchone()
            return {
                'total_asistencias': stats[0] if stats else 0,
                'estudiantes_unicos': stats[1] if stats else 0,
                'presentes': stats[2] if stats else 0,
                'tardanzas': stats[3] if stats else 0,
                'por_rostro': stats[4] if stats else 0,
                'por_qr': stats[5] if stats else 0,
                'fecha': fecha_actual
            }
            
        except Exception as e:
            print(f"❌ Error obteniendo estadísticas: {e}")
            return {}
        finally:
            conn.close()

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

    def obtener_asistencias_por_fecha(self, fecha_consulta=None, seccion_id=None):
        """Consulta asistencias por fecha y opcionalmente por sección"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if fecha_consulta is None:
                fecha_consulta = date.today()
            
            query = """
                SELECT 
                    a.fecha,
                    a.hora,
                    e.nombre,
                    e.apellido,
                    e.dni,
                    s.nombre as seccion,
                    g.nombre as grado,
                    n.nombre as nivel,
                    a.metodo_deteccion,
                    a.estado,
                    a.confianza
                FROM asistencias a
                JOIN estudiantes e ON a.estudiante_id = e.id
                LEFT JOIN secciones s ON a.seccion_id = s.id
                LEFT JOIN grados g ON s.grado_id = g.id
                LEFT JOIN niveles n ON g.nivel_id = n.id
                WHERE a.fecha = ?
            """
            
            params = [fecha_consulta]
            
            if seccion_id:
                query += " AND a.seccion_id = ?"
                params.append(seccion_id)
                
            query += " ORDER BY a.hora DESC"
            
            cursor.execute(query, params)
            return cursor.fetchall()
            
        except Exception as e:
            print(f"❌ Error en consulta por fecha: {e}")
            return []
        finally:
            conn.close()
    
    def obtener_asistencias_por_rango_fechas(self, fecha_inicio, fecha_fin, seccion_id=None):
        """Obtiene asistencias por rango de fechas"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT 
                    a.fecha,
                    a.hora,
                    e.nombre,
                    e.apellido,
                    e.dni,
                    s.nombre as seccion,
                    g.nombre as grado,
                    n.nombre as nivel,
                    a.metodo_deteccion,
                    a.estado,
                    a.confianza
                FROM asistencias a
                JOIN estudiantes e ON a.estudiante_id = e.id
                LEFT JOIN secciones s ON a.seccion_id = s.id
                LEFT JOIN grados g ON s.grado_id = g.id
                LEFT JOIN niveles n ON g.nivel_id = n.id
                WHERE a.fecha BETWEEN ? AND ?
            """
            
            params = [fecha_inicio, fecha_fin]
            
            if seccion_id:
                query += " AND a.seccion_id = ?"
                params.append(seccion_id)
                
            query += " ORDER BY a.fecha DESC, a.hora DESC"
            
            cursor.execute(query, params)
            return cursor.fetchall()
            
        except Exception as e:
            print(f"❌ Error en consulta por rango: {e}")
            return []
        finally:
            conn.close()
    
    def obtener_asistencias_por_estudiante(self, estudiante_id, fecha_inicio=None, fecha_fin=None):
        """Obtiene asistencias de un estudiante específico"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if fecha_inicio is None:
                fecha_inicio = date.today() - timedelta(days=30)  # Últimos 30 días por defecto
            
            if fecha_fin is None:
                fecha_fin = date.today()
            
            cursor.execute("""
                SELECT 
                    a.fecha,
                    a.hora,
                    s.nombre as seccion,
                    a.metodo_deteccion,
                    a.estado,
                    a.confianza
                FROM asistencias a
                LEFT JOIN secciones s ON a.seccion_id = s.id
                WHERE a.estudiante_id = ? AND a.fecha BETWEEN ? AND ?
                ORDER BY a.fecha DESC, a.hora DESC
            """, (estudiante_id, fecha_inicio, fecha_fin))
            
            return cursor.fetchall()
            
        except Exception as e:
            print(f"❌ Error obteniendo asistencias por estudiante: {e}")
            return []
        finally:
            conn.close()
    
    def obtener_resumen_asistencias_por_seccion(self, fecha_consulta=None):
        """Obtiene resumen de asistencias por sección para una fecha"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if fecha_consulta is None:
                fecha_consulta = date.today()
            
            cursor.execute("""
                SELECT 
                    s.nombre as seccion,
                    COUNT(*) as total_asistencias,
                    COUNT(DISTINCT a.estudiante_id) as estudiantes_unicos,
                    SUM(CASE WHEN a.estado = 'presente' THEN 1 ELSE 0 END) as presentes,
                    SUM(CASE WHEN a.estado = 'tardanza' THEN 1 ELSE 0 END) as tardanzas
                FROM asistencias a
                JOIN secciones s ON a.seccion_id = s.id
                WHERE a.fecha = ?
                GROUP BY s.nombre
                ORDER BY s.nombre
            """, (fecha_consulta,))
            
            return cursor.fetchall()
            
        except Exception as e:
            print(f"❌ Error obteniendo resumen por sección: {e}")
            return []
        finally:
            conn.close()
    
    def obtener_estudiantes_sin_asistencia_hoy(self):
        """Obtiene estudiantes que NO han registrado asistencia hoy"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            fecha_actual = date.today()
            
            cursor.execute("""
                SELECT 
                    e.id,
                    e.nombre,
                    e.apellido,
                    e.dni,
                    s.nombre as seccion_nombre
                FROM estudiantes e
                LEFT JOIN secciones s ON e.seccion_id = s.id
                WHERE e.activo = 1 
                AND e.id NOT IN (
                    SELECT estudiante_id 
                    FROM asistencias 
                    WHERE fecha = ?
                )
                ORDER BY e.apellido, e.nombre
            """, (fecha_actual,))
            
            return cursor.fetchall()
            
        except Exception as e:
            print(f"❌ Error obteniendo estudiantes sin asistencia: {e}")
            return []
        finally:
            conn.close()
    
    # ---------------- MÉTODOS EXISTENTES ---------------- #
    
    def generar_qr_estudiante(self, estudiante_id, dni, nombre, apellido, intento=0):
        """Genera un código QR único para el estudiante"""
        try:
            # Limitar intentos para evitar recursión infinita
            if intento > 5:
                print(f"❌ No se pudo generar QR único para estudiante {estudiante_id} después de 5 intentos")
                return None, None
                
            # Crear datos únicos combinando múltiples elementos
            import time
            import hashlib
            import random
            
            timestamp = int(time.time())
            random_salt = random.randint(1000, 9999)
            
            unique_string = f"EST{estudiante_id:04d}-{dni}-{timestamp}-{random_salt}"
            hash_unique = hashlib.md5(unique_string.encode()).hexdigest()[:8]
            
            # Formato final del QR
            qr_data = f"EDU-{estudiante_id:04d}-{hash_unique}"
            
            # Verificar que este QR no exista ya en la base de datos
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM estudiantes WHERE qr_code = ? AND id != ?", (qr_data, estudiante_id))
            existing = cursor.fetchone()
            conn.close()
            
            # Si ya existe, generar uno nuevo
            if existing:
                print(f"🔄 QR duplicado detectado, regenerando... (intento {intento + 1})")
                return self.generar_qr_estudiante(estudiante_id, dni, nombre, apellido, intento + 1)
            
            # Crear código QR
            import qrcode
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            print(f"✅ QR generado para {nombre} {apellido}: {qr_data}")
            return qr_data, qr_img
            
        except Exception as e:
            print(f"❌ Error generando QR para estudiante {estudiante_id}: {e}")
            return None, None

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
    
    def obtener_asistencias_del_dia(self):
        """Obtiene las asistencias del día actual (solo los IDs de estudiantes)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            from datetime import datetime
            hoy = datetime.now().date()
            
            cursor.execute('''
                SELECT estudiante_id 
                FROM asistencias 
                WHERE fecha = ?
            ''', (hoy,))
            
            data = cursor.fetchall()
            # Devolver una lista de IDs de estudiantes
            return [row[0] for row in data]
        except Exception as e:
            print(f"❌ Error obteniendo asistencias del día: {e}")
            return []
        finally:
            conn.close()

    def obtener_asistencias_completas_del_dia(self):
        """Obtiene todas las asistencias del día con información completa"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            from datetime import datetime
            hoy = datetime.now().date()
            
            cursor.execute('''
                SELECT 
                    e.nombre, 
                    e.apellido, 
                    e.dni, 
                    a.hora, 
                    a.metodo_deteccion, 
                    a.confianza,
                    s.nombre as seccion_nombre
                FROM asistencias a
                JOIN estudiantes e ON a.estudiante_id = e.id
                LEFT JOIN secciones s ON e.seccion_id = s.id
                WHERE a.fecha = ?
                ORDER BY a.hora DESC
            ''', (hoy,))
            
            return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error obteniendo asistencias completas del día: {e}")
            return []
        finally:
            conn.close()

    def obtener_estadisticas_del_dia(self):
        """Obtiene estadísticas de asistencias del día"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            from datetime import datetime
            hoy = datetime.now().date()
            
            # Total asistencias
            cursor.execute('SELECT COUNT(*) FROM asistencias WHERE fecha = ?', (hoy,))
            total_asistencias = cursor.fetchone()[0]
            
            # Por método de detección
            cursor.execute('''
                SELECT metodo_deteccion, COUNT(*) 
                FROM asistencias 
                WHERE fecha = ? 
                GROUP BY metodo_deteccion
            ''', (hoy,))
            por_metodo = dict(cursor.fetchall())
            
            # Por sección
            cursor.execute('''
                SELECT s.nombre, COUNT(*) 
                FROM asistencias a
                JOIN estudiantes e ON a.estudiante_id = e.id
                LEFT JOIN secciones s ON e.seccion_id = s.id
                WHERE a.fecha = ?
                GROUP BY s.nombre
            ''', (hoy,))
            por_seccion = dict(cursor.fetchall())
            
            return {
                'total_asistencias': total_asistencias,
                'por_metodo': por_metodo,
                'por_seccion': por_seccion
            }
        except Exception as e:
            print(f"❌ Error obteniendo estadísticas del día: {e}")
            return {'total_asistencias': 0, 'por_metodo': {}, 'por_seccion': {}}
        finally:
            conn.close()

    def verificar_y_corregir_qr_duplicados(self):
        """Verifica y corrige códigos QR duplicados en la base de datos"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Encontrar QR duplicados
            cursor.execute("""
                SELECT qr_code, COUNT(*) as count 
                FROM estudiantes 
                WHERE qr_code IS NOT NULL 
                GROUP BY qr_code 
                HAVING COUNT(*) > 1
            """)
            duplicados = cursor.fetchall()
            
            if not duplicados:
                print("✅ No se encontraron QR duplicados")
                return
            
            print(f"🔧 Encontrados {len(duplicados)} QR duplicados, corrigiendo...")
            
            for qr_code, count in duplicados:
                # Obtener todos los estudiantes con este QR
                cursor.execute("""
                    SELECT id, dni, nombre, apellido 
                    FROM estudiantes 
                    WHERE qr_code = ? 
                    ORDER BY id
                """, (qr_code,))
                estudiantes = cursor.fetchall()
                
                # Mantener el primer estudiante con este QR, regenerar los demás
                for i, (est_id, dni, nombre, apellido) in enumerate(estudiantes):
                    if i == 0:
                        continue  # Mantener el primero
                    
                    # Generar nuevo QR único
                    nuevo_qr_data, nuevo_qr_img = self.generar_qr_estudiante(est_id, dni, nombre, apellido)
                    if nuevo_qr_data:
                        cursor.execute("UPDATE estudiantes SET qr_code = ? WHERE id = ?", (nuevo_qr_data, est_id))
                        print(f"✅ QR corregido para {nombre} {apellido}: {nuevo_qr_data}")
            
            conn.commit()
            print("✅ Corrección de QR duplicados completada")
            
        except Exception as e:
            print(f"❌ Error corrigiendo QR duplicados: {e}")
            conn.rollback()
        finally:
            conn.close()

    def obtener_estudiantes_con_qr(self):
        """Obtiene estudiantes que tienen QR generado"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT e.id, e.nombre, e.apellido, e.dni, e.qr_code, s.nombre as seccion
                FROM estudiantes e
                LEFT JOIN secciones s ON e.seccion_id = s.id
                WHERE e.qr_code IS NOT NULL AND e.activo = 1
                ORDER BY e.apellido, e.nombre
            """)
            return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error obteniendo estudiantes con QR: {e}")
            return []
        finally:
            conn.close()

    def obtener_qr_imagen(self, estudiante_id):
        """Regenera la imagen QR para un estudiante existente"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT qr_code, dni, nombre, apellido FROM estudiantes WHERE id = ?", (estudiante_id,))
            result = cursor.fetchone()
            
            if not result or not result[0]:
                return None
                
            qr_data, dni, nombre, apellido = result
            
            # Regenerar imagen QR
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            return qr.make_image(fill_color="black", back_color="white")
            
        except Exception as e:
            print(f"❌ Error generando imagen QR: {e}")
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

