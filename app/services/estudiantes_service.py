class EstudianteService:
    def __init__(self, db_manager):
        self.db = db_manager

    def registrar(self, dni, nombre, apellido, fecha_nacimiento, genero, telefono, email, direccion, nombre_contacto_emergencia, telefono_contacto_emergencia, turno, año_escolar, seccion_id):
        return self.db.agregar_estudiante(dni, nombre, apellido, fecha_nacimiento, genero, telefono, email, direccion, nombre_contacto_emergencia, telefono_contacto_emergencia, turno, año_escolar, seccion_id)

    def obtener_todos(self):
        return self.db.obtener_estudiantes()

    def obtener_por_id(self, estudiante_id):
        return self.db.obtener_estudiante_por_id(estudiante_id)

    def actualizar(self, estudiante_id, dni, nombre, apellido, fecha_nacimiento, genero, telefono, email, direccion, nombre_contacto_emergencia, telefono_contacto_emergencia, turno, año_escolar, seccion_id):
        return self.db.actualizar_estudiante(estudiante_id, dni, nombre, apellido, fecha_nacimiento, genero, telefono, email, direccion, nombre_contacto_emergencia, telefono_contacto_emergencia, turno, año_escolar, seccion_id)
    
    def desactivar(self, estudiante_id):
        return self.db.desactivar_estudiante(estudiante_id)

    def obtener_activos(self):
        return self.db.obtener_estudiantes_activos()
    
    def reactivar(self, estudiante_id):
        return self.db.reactivar_estudiante(estudiante_id)

    def obtener_inactivos(self):
        return self.db.obtener_estudiantes_inactivos()
    
    def verificar_dni_existente(self, dni):
        return self.db.verificar_dni_existente(dni)

    def obtener_secciones_activas(self):
        return self.db.obtener_secciones_activas()

    def obtener_grados_activos(self):
        return self.db.obtener_grados()

    def obtener_niveles_activos(self):
        return self.db.obtener_niveles()