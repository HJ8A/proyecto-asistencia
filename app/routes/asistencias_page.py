import streamlit as st
import cv2
import numpy as np
import pandas as pd
from datetime import datetime
import plotly.express as px

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
    """Muestra las asistencias del día actual con información completa"""
    
    try:
        # Obtener resumen completo del día
        resumen = service.obtener_resumen_completo_dia()
        estadisticas = resumen.get('estadisticas', {})
        asistencias = resumen.get('asistencias', [])
        fecha_actual = resumen.get('fecha_actual', 'Fecha no disponible')
        
        st.header(f"📊 Asistencias del Día - {fecha_actual}")
        
        # Asegurarse de que las estadísticas tengan valores por defecto
        estadisticas_default = {
            'total_asistencias': 0,
            'estudiantes_unicos': 0,
            'presentes': 0,
            'tardanzas': 0,
            'por_rostro': 0,
            'por_qr': 0
        }
        
        # Combinar con estadísticas reales
        estadisticas_completas = {**estadisticas_default, **estadisticas}
        
        # Mostrar estadísticas en tarjetas
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Total Asistencias", 
                estadisticas_completas['total_asistencias'],
                help="Total de registros de asistencia hoy"
            )
        
        with col2:
            st.metric(
                "Estudiantes Únicos", 
                estadisticas_completas['estudiantes_unicos'],
                help="Estudiantes diferentes que han marcado asistencia"
            )
        
        with col3:
            st.metric(
                "Presentes", 
                estadisticas_completas['presentes'],
                help="Asistencias en horario puntual"
            )
        
        with col4:
            st.metric(
                "Tardanzas", 
                estadisticas_completas['tardanzas'],
                help="Asistencias registradas después del horario límite"
            )
        
        with col5:
            total_metodos = estadisticas_completas['por_rostro'] + estadisticas_completas['por_qr']
            if total_metodos > 0:
                porcentaje_rostro = (estadisticas_completas['por_rostro'] / total_metodos) * 100
                porcentaje_qr = (estadisticas_completas['por_qr'] / total_metodos) * 100
                st.metric(
                    "Métodos", 
                    f"👤 {porcentaje_rostro:.0f}%",
                    delta=f"📄 {porcentaje_qr:.0f}%",
                    help="Distribución por método de detección"
                )
            else:
                st.metric("Métodos", "N/A")
        
        # Resto del código sin cambios...
        st.subheader("📋 Lista de Asistencias Registradas")
        
        if asistencias:
            # Crear DataFrame con información completa
            datos = []
            for asistencia in asistencias:
                # Estructura de la tupla: (id, nombre, apellido, dni, seccion_nombre, hora, metodo_deteccion, confianza, estado)
                datos.append({
                    'ID': asistencia[0],
                    'Nombre': asistencia[1],
                    'Apellido': asistencia[2],
                    'DNI': asistencia[3],
                    'Sección': asistencia[4] or 'No asignada',
                    'Hora': asistencia[5],
                    'Método': '👤 Rostro' if asistencia[6] == 'rostro' else '📄 QR',
                    'Confianza': f"{asistencia[7]:.2f}" if asistencia[7] is not None else 'N/A',
                    'Estado': '🟢 Puntual' if asistencia[8] == 'presente' else '🟡 Tardanza'
                })
            
            df = pd.DataFrame(datos)
            
            # Mostrar tabla con estilo
            st.dataframe(
                df,
                use_container_width=True,
                height=400,
                hide_index=True,
                column_config={
                    'ID': st.column_config.NumberColumn('ID', width='small'),
                    'Nombre': st.column_config.TextColumn('Nombre', width='medium'),
                    'Apellido': st.column_config.TextColumn('Apellido', width='medium'),
                    'DNI': st.column_config.TextColumn('DNI', width='small'),
                    'Sección': st.column_config.TextColumn('Sección', width='medium'),
                    'Hora': st.column_config.TextColumn('Hora', width='small'),
                    'Método': st.column_config.TextColumn('Método', width='small'),
                    'Confianza': st.column_config.TextColumn('Confianza', width='small'),
                    'Estado': st.column_config.TextColumn('Estado', width='small')
                }
            )
            
            st.subheader("🔍 Detalle de Asistencias")
            
            for asistencia in asistencias:
                id_asist, nombre, apellido, dni, seccion, hora, metodo, confianza, estado = asistencia
                
                with st.expander(f"{nombre} {apellido} - {hora}", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write("**👤 Información Personal**")
                        st.write(f"**Nombre:** {nombre} {apellido}")
                        st.write(f"**DNI:** {dni}")
                        st.write(f"**Sección:** {seccion or 'No asignada'}")
                    
                    with col2:
                        st.write("**📊 Datos de Asistencia**")
                        st.write(f"**Hora:** {hora}")
                        st.write(f"**Método:** {metodo}")
                        st.write(f"**Estado:** {estado}")
                    
                    with col3:
                        st.write("**🎯 Detalles Técnicos**")
                        if confianza is not None:
                            st.write(f"**Confianza:** {confianza:.2f}")
                        
                        # Mostrar icono según método
                        if metodo == 'rostro':
                            st.success("👤 Reconocimiento Facial")
                            if confianza is not None:
                                # Barra de progreso para confianza
                                st.progress(float(confianza), text=f"Confianza: {confianza:.0%}")
                        else:
                            st.info("📄 Código QR")
                            st.success("✅ QR Válido")
                    
                    # Separador visual
                    st.markdown("---")
        
        else:
            # No hay asistencias hoy
            st.info("📝 No hay asistencias registradas para el día de hoy")
            
            # Mostrar mensaje amigable
            st.markdown("""
            <div style='text-align: center; padding: 20px; background-color: #f0f2f6; border-radius: 10px;'>
                <h3 style='color: #666;'>No se han registrado asistencias hoy</h3>
                <p style='color: #888;'>Las asistencias aparecerán aquí automáticamente cuando los estudiantes sean detectados por rostro o QR.</p>
            </div>
            """, unsafe_allow_html=True)

        if asistencias and len(asistencias) > 0:
            with st.expander("📈 Visualizaciones"):
                col1, col2 = st.columns(2)
                
                with col1:
                    # Gráfico de métodos de detección
                    metodos_count = {
                        'Rostro': len([a for a in asistencias if a[6] == 'rostro']),
                        'QR': len([a for a in asistencias if a[6] == 'qr'])
                    }
                    
                    if metodos_count['Rostro'] > 0 or metodos_count['QR'] > 0:
                        fig_metodos = px.pie(
                            values=list(metodos_count.values()),
                            names=list(metodos_count.keys()),
                            title="Distribución por Método de Detección",
                            color=list(metodos_count.keys()),
                            color_discrete_map={'Rostro': '#1f77b4', 'QR': '#ff7f0e'}
                        )
                        st.plotly_chart(fig_metodos, use_container_width=True)
                
                with col2:
                    # Gráfico de estados
                    estados_count = {
                        'Puntual': len([a for a in asistencias if a[8] == 'presente']),
                        'Tardanza': len([a for a in asistencias if a[8] == 'tardanza'])
                    }
                    
                    if estados_count['Puntual'] > 0 or estados_count['Tardanza'] > 0:
                        fig_estados = px.bar(
                            x=list(estados_count.keys()),
                            y=list(estados_count.values()),
                            title="Distribución por Estado",
                            color=list(estados_count.keys()),
                            color_discrete_map={'Puntual': '#2ecc71', 'Tardanza': '#f39c12'}
                        )
                        st.plotly_chart(fig_estados, use_container_width=True)
    
    except Exception as e:
        st.error(f"❌ Error al cargar las asistencias: {str(e)}")
        st.info("💡 Si el problema persiste, verifica que la base de datos esté correctamente configurada.")

def mostrar_consultas_avanzadas(service):
    """Para futuras consultas avanzadas (lo mencionaste para después)"""
    st.header("🔍 Consultas Avanzadas de Asistencias")
    st.info("Esta funcionalidad estará disponible próximamente")

