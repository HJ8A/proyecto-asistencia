import streamlit as st
from app.routes import (
    dashboard_page,
    estudiantes_page,
    asistencias_page,
    reportes_page,
    configuracion_page,
    gestion_academica_page
)
from app.data.database import DatabaseManager
from app.services.estudiantes_service import EstudianteService
from app.services.asistencias_service import AsistenciaService
from app.services.gestion_academica_service import GestionAcademicaService

# Configurar la página
st.set_page_config(
    page_title="Sistema de Asistencias Escolares",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("🎓 Sistema de Control de Asistencias Escolares")
    st.markdown("---")

    # Instanciar servicios
    db = DatabaseManager()
    estudiantes_service = EstudianteService(db)
    asistencias_service = AsistenciaService(db)
    gestion_academica_service = GestionAcademicaService(db)

    # Sidebar de navegación
    st.sidebar.title("Navegación")
    opcion = st.sidebar.radio(
        "Selecciona una opción:",
        [
            "📊 Dashboard",
            "👥 Estudiantes",
            "🏫 Académico",
            "📝 Registrar Asistencias",
            #"📈 Reportes-Estadísticas",
            "⚙️ Configuración"
        ]
    )

    # Rutas
    if opcion == "📊 Dashboard":
        dashboard_page.mostrar_dashboard(db)

    elif opcion == "👥 Estudiantes":
        estudiantes_page.gestion_estudiantes(estudiantes_service)

    elif opcion == "📝 Registrar Asistencias":
        asistencias_page.registrar_asistencias(asistencias_service , db)

    elif opcion == "🏫 Académico":  # Nueva ruta
        gestion_academica_page.gestion_academica(gestion_academica_service)

    #elif opcion == "📈 Reportes-Estadísticas":
    #    reportes_page.mostrar_reportes(db)

    elif opcion == "⚙️ Configuración":
        configuracion_page.mostrar_configuracion(db)

if __name__ == "__main__":
    main()