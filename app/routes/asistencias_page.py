import streamlit as st
import cv2
import numpy as np
import pandas as pd
from datetime import datetime

def registrar_asistencias(service, db):
    st.header("📝 Registrar Asistencias - Reconocimiento Facial + QR")
    
    tab1, tab2, tab3 = st.tabs(["🎥 Sistema Combinado", "📊 Asistencias del Día", "🔧 Diagnóstico"])
    
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
            if st.button("🚀 Iniciar Sistema Combinado", width='stretch', type="primary"):
                try:
                    service.iniciar_monitoreo_combinado()
                    st.success("Sistema de reconocimiento dual iniciado")
                except Exception as e:
                    st.error(f"Error al iniciar: {e}")
        
        with col2:
            if st.button("🔄 Recargar Modelos", width='stretch'):
                service.cargar_encodings()
                service.cargar_registros_del_dia()
                st.success("Modelos y registros recargados")
        
        with col3:
            if st.button("📊 Ver Estadísticas", width='stretch'):
                mostrar_estadisticas(service)
    
    with tab2:
        mostrar_asistencias_del_dia(service)
        
    with tab3:
        st.subheader("🔧 Diagnóstico del Sistema")
        if st.button("🔍 Ejecutar Diagnóstico QR", width='stretch'):
            diagnosticar_qr(service)
        if st.button("🔧 Verificar Métodos DB", width='stretch'):
            verificar_metodos_db(db)

def diagnosticar_qr(service):
    """Función para diagnosticar problemas con QR"""
    import cv2
    
    st.info("🔍 INICIANDO DIAGNÓSTICO DE QR...")
    
    # 1. Verificar cámara
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        st.error("❌ No se puede acceder a la cámara")
        return
    
    st.success("✅ Cámara accesible")
    
    # 2. Tomar frame de prueba
    ret, frame = cap.read()
    if not ret:
        st.error("❌ No se puede leer frame de la cámara")
        cap.release()
        return
    
    st.success("✅ Frame capturado correctamente")
    
    # 3. Probar detección de QR
    try:
        from app.utils.qr_utils import qr_manager
        qr_datos = qr_manager.detectar_qr_en_frame(frame)
        st.success(f"✅ QR Manager funcionando. QR detectados: {len(qr_datos)}")
        
        for i, qr in enumerate(qr_datos):
            st.write(f"QR {i+1}: {qr['data']}")
            
            # Verificar si el QR existe en la base de datos
            estudiante = service.db.obtener_estudiante_por_qr(qr['data'])
            if estudiante:
                st.success(f"✅ Estudiante encontrado: {estudiante[2]} {estudiante[3]}")
            else:
                st.error(f"❌ No se encontró estudiante para este QR")
                
    except Exception as e:
        st.error(f"❌ Error en QR Manager: {e}")
    
    cap.release()
    st.success("🔍 DIAGNÓSTICO COMPLETADO")

def verificar_metodos_db(db):
    """Verifica que todos los métodos necesarios estén disponibles"""
    st.info("🔍 Verificando métodos de base de datos...")
    
    metodos_requeridos = [
        'obtener_asistencias_del_dia',
        'obtener_asistencias_completas_del_dia', 
        'obtener_estadisticas_del_dia',
        'obtener_estudiantes_sin_qr',
        'obtener_estudiante_por_qr',
        'cargar_encodings_faciales'
    ]
    
    for metodo in metodos_requeridos:
        if hasattr(db, metodo):
            st.success(f"✅ {metodo} - DISPONIBLE")
        else:
            st.error(f"❌ {metodo} - FALTANTE")

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

def mostrar_asistencias_del_dia(service):
    """Muestra las asistencias del día actual"""
    st.subheader("📊 Asistencias del Día")
    
    try:
        # Obtener asistencias del día usando el servicio
        asistencias = service.obtener_asistencias_del_dia()
        
        if asistencias:
            st.success(f"✅ {len(asistencias)} asistencias registradas hoy")
            
            # Mostrar en formato de tabla usando pandas
            df = pd.DataFrame(asistencias, columns=[
                'Nombre', 'Apellido', 'DNI', 'Hora', 'Método', 'Confianza', 'Sección'
            ])
            
            # Formatear confianza
            if 'Confianza' in df.columns:
                df['Confianza'] = df['Confianza'].apply(
                    lambda x: f"{float(x):.2%}" if x and str(x).replace('.', '').isdigit() else "N/A"
                )
            
            st.dataframe(df, use_container_width=True, height=400)
            
            # Mostrar también en formato de tarjetas
            st.subheader("📋 Detalle de Asistencias")
            for asistencia in asistencias:
                nombre, apellido, dni, hora, metodo, confianza, seccion = asistencia
                
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    with col1:
                        st.write(f"**{nombre} {apellido}**")
                        st.caption(f"DNI: {dni} | Sección: {seccion or 'N/A'}")
                    with col2:
                        st.write(f"🕒 {hora}")
                        st.caption(f"Método: {metodo}")
                    with col3:
                        if confianza and str(confianza).replace('.', '').isdigit():
                            st.write(f"🔍 {float(confianza):.2f}")
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
        
        # Fallback: intentar obtener asistencias directamente de la base de datos
        try:
            hoy = datetime.now().date()
            conn = service.db._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT e.nombre, e.apellido, e.dni, a.hora, a.metodo_deteccion, a.confianza
                FROM asistencias a
                JOIN estudiantes e ON a.estudiante_id = e.id
                WHERE a.fecha = ?
                ORDER BY a.hora DESC
            ''', (hoy,))
            
            asistencias_fallback = cursor.fetchall()
            conn.close()
            
            if asistencias_fallback:
                st.warning("Usando método alternativo para cargar asistencias")
                for nombre, apellido, dni, hora, metodo, confianza in asistencias_fallback:
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
        except Exception as e2:
            st.error(f"Error en método alternativo: {e2}")