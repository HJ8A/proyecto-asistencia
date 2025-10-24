# app/services/estudiantes_service.py
class EstudianteService:
    def __init__(self, db_manager):
        self.db = db_manager

    def registrar(self, dni, nombre, apellido, edad, seccion):
        return self.db.agregar_estudiante(dni, nombre, apellido, edad, seccion)

    def obtener_todos(self):
        return self.db.obtener_estudiantes()

    def obtener_por_id(self, estudiante_id):
        return self.db.obtener_estudiante_por_id(estudiante_id)

    def actualizar(self, estudiante_id, dni, nombre, apellido, edad, seccion):
        return self.db.actualizar_estudiante(estudiante_id, dni, nombre, apellido, edad, seccion)
    
    def desactivar(self, estudiante_id):
        return self.db.desactivar_estudiante(estudiante_id)

    def obtener_activos(self):
        return self.db.obtener_estudiantes_activos()
    
    def reactivar(self, estudiante_id):
        return self.db.reactivar_estudiante(estudiante_id)

    def obtener_inactivos(self):
        return self.db.obtener_estudiantes_inactivos()