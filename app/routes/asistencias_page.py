import streamlit as st
import cv2
import numpy as np
from datetime import datetime

def registrar_asistencias(service, db):
    st.header("📝 Registrar Asistencias")
    
    tab1, tab2 = st.tabs(["🎥 Reconocimiento Facial", "📊 Asistencias del Día"])
    
    with tab1:
        st.subheader("Sistema de Reconocimiento Facial")
        st.info("""
        **Instrucciones:**
        - Asegúrate de tener buena iluminación
        - El estudiante debe estar frente a la cámara
        - El sistema registrará automáticamente la asistencia
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 Iniciar Reconocimiento Facial", use_container_width=True):
                try:
                    service.iniciar_monitoreo_mejorado()
                    st.success("Sistema de reconocimiento iniciado")
                except Exception as e:
                    st.error(f"Error al iniciar la cámara: {e}")
        
        with col2:
            if st.button("🔄 Recargar Modelos", use_container_width=True):
                service.cargar_encodings()
                st.success("Modelos de reconocimiento recargados")
    
    with tab2:
        st.subheader("Asistencias Registradas Hoy")
        mostrar_asistencias_del_dia(db)

def mostrar_asistencias_del_dia(db):
    hoy = datetime.now().date()
    
    try:
        conn = db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT e.nombre, e.apellido, e.dni, a.hora, a.metodo_deteccion, a.confianza
            FROM asistencias a
            JOIN estudiantes e ON a.estudiante_id = e.id
            WHERE a.fecha = ?
            ORDER BY a.hora DESC
        ''', (hoy,))
        
        asistencias = cursor.fetchall()
        
        if asistencias:
            st.success(f"✅ {len(asistencias)} asistencias registradas hoy")
            
            for nombre, apellido, dni, hora, metodo, confianza in asistencias:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.write(f"**{nombre} {apellido}**")
                        st.caption(f"DNI: {dni}")
                    with col2:
                        st.write(f"🕒 {hora}")
                        st.caption(f"Método: {metodo}")
                    with col3:
                        if confianza:
                            st.write(f"🔍 {confianza:.2f}")
                        st.success("✅ Presente")
                    st.divider()
        else:
            st.info("📝 No hay asistencias registradas para hoy")
            
    except Exception as e:
        st.error(f"Error al cargar asistencias: {e}")
    finally:
        conn.close()