class GestionAcademicaService:
    def __init__(self, db_manager):
        self.db = db_manager

    # Métodos para secciones
    def obtener_secciones(self):
        return self.db.obtener_secciones()

    def obtener_seccion_por_id(self, seccion_id):
        return self.db.obtener_seccion_por_id(seccion_id)

    def agregar_seccion(self, grado_id, nombre, letra, capacidad=30):
        return self.db.agregar_seccion(grado_id, nombre, letra, capacidad)

    def actualizar_seccion(self, seccion_id, grado_id, nombre, letra, capacidad):
        # Necesitarás implementar este método en DatabaseManager
        pass

    def desactivar_seccion(self, seccion_id):
        # Necesitarás implementar este método en DatabaseManager
        pass

    # Métodos para grados
    def obtener_grados(self):
        return self.db.obtener_grados()

    def obtener_grados_por_nivel(self, nivel_id):
        return self.db.obtener_grados_por_nivel(nivel_id)

    # Métodos para niveles
    def obtener_niveles(self):
        return self.db.obtener_niveles()

    # Métodos para profesores
    def obtener_profesores(self):
        return self.db.obtener_profesores()

    def obtener_profesor_por_id(self, profesor_id):
        return self.db.obtener_profesor_por_id(profesor_id)

    def agregar_profesor(self, dni, nombre, apellido, email=None, telefono=None):
        return self.db.agregar_profesor(dni, nombre, apellido, email, telefono)

    def actualizar_profesor(self, profesor_id, dni, nombre, apellido, email, telefono):
        return self.db.actualizar_profesor(profesor_id, dni, nombre, apellido, email, telefono)

    def desactivar_profesor(self, profesor_id):
        return self.db.desactivar_profesor(profesor_id)

    def reactivar_profesor(self, profesor_id):
        return self.db.reactivar_profesor(profesor_id)

    def obtener_profesores_activos(self):
        return self.db.obtener_profesores_activos()

    def obtener_profesores_inactivos(self):
        return self.db.obtener_profesores_inactivos()

    def verificar_dni_profesor_existente(self, dni):
        return self.db.verificar_dni_profesor_existente(dni)