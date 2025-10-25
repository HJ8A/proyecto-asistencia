import streamlit as st
from datetime import datetime

def registrar_asistencias(asistencia_service):
    st.header("📝 Registrar Asistencias")
    
    tab1, tab2 = st.tabs(["🎥 Reconocimiento Facial", "📊 Asistencias del Día"])

    with tab1:
        st.subheader("Sistema de Reconocimiento Facial")
        st.info("Presiona el botón para iniciar el reconocimiento en una ventana externa.")

        if st.button("🚀 Iniciar reconocimiento facial"):
            try:
                asistencia_service.iniciar_reconocimiento()
            except Exception as e:
                st.error(f"Error al iniciar la cámara: {e}")

    with tab2:
        asistencias = asistencia_service.obtener_asistencias_del_dia()
        if asistencias:
            st.success(f"✅ {len(asistencias)} asistencias registradas hoy")
            for nombre, apellido, dni, hora, metodo, confianza in asistencias:
                st.write(f"**{nombre} {apellido}** — 🕒 {hora} — {confianza:.2f}")
        else:
            st.info("No hay asistencias registradas hoy.")
