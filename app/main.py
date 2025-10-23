# app/main.py
import streamlit as st
from app.routes import dashboard_page, estudiantes_page, asistencias_page, reportes_page, configuracion_page

PAGES = {
    "📊 Dashboard": dashboard_page,
    "👥 Gestión de Estudiantes": estudiantes_page,
    "📝 Registrar Asistencias": asistencias_page,
    "📈 Reportes y Estadísticas": reportes_page,
    "⚙️ Configuración": configuracion_page,
}

st.set_page_config(page_title="Sistema de Asistencias Escolares", page_icon="🎓", layout="wide")

st.sidebar.title("Navegación")
opcion = st.sidebar.radio("Selecciona una opción:", list(PAGES.keys()))
PAGES[opcion].render()
