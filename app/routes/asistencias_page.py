import streamlit as st
import cv2
import numpy as np
from datetime import datetime

def registrar_asistencias(service, db):
    st.header("📝 Registrar Asistencias - Reconocimiento Facial + QR")
    
    tab1, tab2 = st.tabs(["🎥 Sistema Combinado", "📊 Asistencias del Día"])
    
    with tab1:
        st.subheader("Sistema de Reconocimiento Dual")
        st.info("""
        **Funcionalidades:**
        - 👤 **Reconocimiento Facial**: Detecta rostros automáticamente
        - 📄 **Detección QR**: Escanea códigos QR de carnets
        - ⚡ **Registro Automático**: Ambos métodos registran asistencia
        
        **Instrucciones:**
        1. Los estudiantes pueden pasar frente a la cámara
        2. El sistema reconocerá sus rostros automáticamente
        3. Como respaldo, pueden mostrar su código QR del carnet
        4. La asistencia se registra automáticamente
        """)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 Iniciar Sistema Combinado", use_container_width=True, type="primary"):
                try:
                    service.iniciar_monitoreo_combinado()
                    st.success("Sistema de reconocimiento dual iniciado")
                except Exception as e:
                    st.error(f"Error al iniciar: {e}")
        
        with col2:
            if st.button("🔄 Recargar Modelos", use_container_width=True):
                service.cargar_encodings()
                st.success("Modelos recargados")
        
        with col3:
            if st.button("📊 Ver Estadísticas", use_container_width=True):
                mostrar_estadisticas(service)
    
    with tab2:
        mostrar_asistencias_del_dia(db)

def mostrar_estadisticas(service):
    """Muestra estadísticas del sistema"""
    encodings, nombres, ids = service.db.cargar_encodings_faciales()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Estudiantes con Rostro", len(set(ids)))
    with col2:
        st.metric("Total Encodings", len(encodings))
    with col3:
        st.metric("Sistema", "Activo")

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
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    with col1:
                        st.write(f"**{nombre} {apellido}**")
                        st.caption(f"DNI: {dni}")
                    with col2:
                        st.write(f"🕒 {hora}")
                        st.caption(f"Método: {metodo}")
                    with col3:
                        if confianza:
                            st.write(f"🔍 {confianza:.2f}")
                    with col4:
                        if metodo == 'rostro':
                            st.success("👤 Facial")
                        else:
                            st.info("📄 QR")
                    st.divider()
        else:
            st.info("📝 No hay asistencias registradas para hoy")
            
    except Exception as e:
        st.error(f"Error al cargar asistencias: {e}")
    finally:
        conn.close()