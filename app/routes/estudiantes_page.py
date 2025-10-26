import streamlit as st
import pandas as pd
from datetime import datetime
from app.utils.camara_utils import CamaraManager

def gestion_estudiantes(service):
    st.header("👥 Gestión de Estudiantes")
    
    tab1, tab2, tab3, tab4, tab5, tab6= st.tabs([
        "📋 Lista de Estudiantes", 
        "➕ Registrar Nuevo",
        "✏️ Editar Estudiante",
        "🚫 Desactivar Estudiante",
        "🔄 Estudiantes Desactivados",
        "📷 Capturar Rostros"
    ])

    with tab1:
        mostrar_lista_estudiantes(service)

    with tab2:
        registrar_nuevo_estudiante(service)

    with tab3:
        editar_estudiante(service)

    with tab4:  
        desactivar_estudiante(service)

    with tab5:
        mostrar_estudiantes_desactivados(service)

    with tab6:
        capturar_rostros(service)


def mostrar_lista_estudiantes(service):
    st.subheader("📊 Lista de Estudiantes Registrados")
    estudiantes = service.obtener_todos()
    #estudiantes = service.obtener_activos()

    if estudiantes:
        df = pd.DataFrame(estudiantes, columns=['ID', 'DNI', 'Nombre', 'Apellido', 'Edad', 'Sección', 'Fecha Registro'])
        
        # Formatear la fecha para mejor visualización
        df['Fecha Registro'] = pd.to_datetime(df['Fecha Registro']).dt.strftime('%d/%m/%Y')
        
        st.dataframe(df, width='stretch', height=400)
        
        # Mostrar estadísticas rápidas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Estudiantes", len(estudiantes))
        with col2:
            st.metric("Edad Promedio", f"{df['Edad'].mean():.1f} años")
        with col3:
            secciones_unicas = df['Sección'].nunique()
            st.metric("Secciones", secciones_unicas)
    else:
        st.info("📝 No hay estudiantes registrados. Use la pestaña 'Registrar Nuevo' para agregar estudiantes.")

def registrar_nuevo_estudiante(service):
    st.subheader("🎓 Registrar Nuevo Estudiante")
    
    with st.form("nuevo_estudiante", clear_on_submit=True):
        # Título con mejor estilo
        st.markdown(
            '<div style="color: #1a1a1a; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; font-weight: 600; text-align: center;">'
            '📝 Información Personal'
            '</div>', 
            unsafe_allow_html=True
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            dni = st.text_input(
                "DNI*", 
                placeholder="72545117",
                help="Documento Nacional de Identidad (8 dígitos, obligatorio)",
                max_chars=8,
                key="dni_input"
            )
            nombre = st.text_input(
                "Nombre*", 
                placeholder="Juan",
                help="Nombre del estudiante (obligatorio)",
                key="nombre_input"
            )
            edad = st.number_input(
                "Edad*", 
                min_value=5, 
                max_value=30, 
                value=15,
                help="Edad del estudiante (obligatorio)",
                key="edad_input"
            )
            
        with col2:
            apellido = st.text_input(
                "Apellido*", 
                placeholder="Pérez",
                help="Apellido del estudiante (obligatorio)",
                key="apellido_input"
            )
            seccion = st.text_input(
                "Sección", 
                placeholder="3-A",
                help="Sección o grupo (opcional)",
                key="seccion_input"
            )
        
        # Mensaje de campos obligatorios mejorado
        st.markdown(
            '<div class="campos-obligatorios">* Campos obligatorios</div>',
            unsafe_allow_html=True
        )
        
        submitted = st.form_submit_button(
            "📝 Registrar Estudiante", 
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            # Validaciones
            errores = []
            
            # Validar campos obligatorios
            if not dni:
                errores.append("El DNI es obligatorio")
            if not nombre:
                errores.append("El nombre es obligatorio")
            if not apellido:
                errores.append("El apellido es obligatorio")
            if not edad:
                errores.append("La edad es obligatoria")
            
            # Validaciones específicas del DNI
            if dni:
                if not dni.isdigit():
                    errores.append("El DNI debe contener solo números")
                elif len(dni) != 8:
                    errores.append("El DNI debe tener exactamente 8 dígitos")
                else:
                    # Verificar si el DNI ya existe
                    try:
                        if service.verificar_dni_existente(dni):
                            errores.append("El DNI ya está registrado en el sistema")
                    except Exception as e:
                        errores.append(f"Error al verificar DNI: {e}")
            
            # Mostrar errores o proceder con el registro
            if errores:
                for error in errores:
                    st.error(f"❌ {error}")
            else:
                try:
                    estudiante_id = service.registrar(dni, nombre, apellido, edad, seccion)
                    if estudiante_id:
                        st.success(f"✅ Estudiante **{nombre} {apellido}** registrado correctamente con ID: {estudiante_id}")
                        # Limpiar el formulario
                        st.rerun()
                    else:
                        st.error("❌ Error al registrar el estudiante")
                except ValueError as e:
                    st.error(f"❌ {e}")
                except Exception as e:
                    st.error(f"❌ Error inesperado: {e}")

def editar_estudiante(service):
    st.subheader("✏️ Editar Información de Estudiante")
    
    estudiantes = service.obtener_activos()  # Solo mostrar activos
    if not estudiantes:
        st.info("📝 No hay estudiantes activos para editar.")
        return

    # Crear opciones más descriptivas
    opciones = [f"ID: {e[0]} - {e[2]} {e[3]} (DNI: {e[1]})" for e in estudiantes]
    seleccionado = st.selectbox("Seleccionar Estudiante a Editar", opciones, key="editar_estudiante")
    
    if seleccionado:
        estudiante_id = estudiantes[opciones.index(seleccionado)][0]
        datos = service.obtener_por_id(estudiante_id)
        
        if datos:
            with st.form("editar_estudiante"):
                st.markdown('<div class="form-title">📝 Editar Información del Estudiante</div>', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    dni = st.text_input(
                        "DNI *", 
                        value=datos[1],
                        placeholder="Ej: 12345678",
                        help="Documento Nacional de Identidad"
                    )
                    nombre = st.text_input(
                        "Nombre *", 
                        value=datos[2],
                        placeholder="Ej: Juan",
                        help="Nombre del estudiante"
                    )
                    edad = st.number_input(
                        "Edad *", 
                        min_value=5, 
                        max_value=30, 
                        value=datos[4],
                        help="Edad del estudiante"
                    )
                    
                with col2:
                    apellido = st.text_input(
                        "Apellido *", 
                        value=datos[3],
                        placeholder="Ej: Pérez",
                        help="Apellido del estudiante"
                    )
                    seccion = st.text_input(
                        "Sección", 
                        value=datos[5] or "",
                        placeholder="Ej: A-101",
                        help="Sección o grupo del estudiante"
                    )
                
                st.markdown("**\* Campos obligatorios**")
                
                if st.form_submit_button("💾 Guardar Cambios", use_container_width=True, type="primary"):
                    if dni and nombre and apellido and edad:
                        try:
                            if not dni.isdigit() or len(dni) < 8:
                                st.error("❌ El DNI debe contener solo números y tener al menos 8 dígitos")
                            else:
                                if service.actualizar(estudiante_id, dni, nombre, apellido, edad, seccion):
                                    st.success("✅ Información del estudiante actualizada correctamente")
                                    st.rerun()
                                else:
                                    st.error("❌ Error al actualizar la información")
                        except ValueError as e:
                            st.error(f"❌ {e}")
                    else:
                        st.error("❌ Por favor complete todos los campos obligatorios")
                        
def capturar_rostros(service):
    st.subheader("📷 Captura de Rostros para Reconocimiento Facial")
    
    estudiantes = service.obtener_todos()
    if not estudiantes:
        st.warning("⚠️ No hay estudiantes activos. Registra o reactiva un estudiante primero.")
        return
    
    st.info("""
    **Instrucciones para la captura:**
    1. Selecciona un estudiante de la lista
    2. Haz clic en 'Iniciar Captura de Rostros'
    3. Se abrirá una ventana con la cámara
    4. **Presiona ESPACIO** para capturar cada imagen (se capturarán 5 imágenes)
    5. **Presiona ESC** para cancelar en cualquier momento
    6. Asegúrate de tener buena iluminación y que el rostro sea visible
    """)
    
    # Selector de estudiante para la captura
    opciones = [f"ID: {e[0]} - {e[2]} {e[3]} (DNI: {e[1]})" for e in estudiantes]
    estudiante_seleccionado = st.selectbox("Seleccionar Estudiante para Captura", opciones, key="capturar_rostros")
    
    if estudiante_seleccionado:
        estudiante_index = opciones.index(estudiante_seleccionado)
        estudiante_id = estudiantes[estudiante_index][0]
        nombre = estudiantes[estudiante_index][2]
        apellido = estudiantes[estudiante_index][3]
        
        st.write(f"**Estudiante seleccionado:** {nombre} {apellido}")
        
        # Mostrar información del estudiante
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**ID:** {estudiante_id}")
        with col2:
            st.info(f"**Nombre:** {nombre}")
        with col3:
            st.info(f"**Apellido:** {apellido}")
        
        # Botón para iniciar captura
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("📸 Iniciar Captura de Rostros", type="primary", use_container_width=True):
                st.info("🟢 Iniciando cámara... Por favor, permite el acceso a la cámara.")
                st.warning("⚠️ La ventana de la cámara puede abrirse detrás de esta ventana. Busca la ventana 'Captura de Rostros'.")
                
                # Llamar a la función de captura
                try:
                    exito = CamaraManager.capturar_rostros_interactivo(
                        estudiante_id=estudiante_id,
                        nombre=nombre,
                        apellido=apellido,
                        db=service.db,
                        num_capturas=5
                    )
                    
                    if exito:
                        st.success("✅ ¡Captura de rostros completada exitosamente!")
                        st.balloons()
                    else:
                        st.error("❌ La captura de rostros no se completó. Intenta nuevamente.")
                        
                except Exception as e:
                    st.error(f"❌ Error durante la captura: {str(e)}")
                    st.info("💡 Asegúrate de tener una cámara conectada y los permisos adecuados.")
        
        with col2:
            # Mostrar estadísticas de encodings existentes
            try:
                encodings, nombres, ids = service.db.cargar_encodings_faciales()
                encodings_estudiante = sum(1 for id in ids if id == estudiante_id)
                st.write(f"**Encodings guardados para este estudiante:** {encodings_estudiante}")
            except:
                st.write("**Encodings guardados:** 0")

def desactivar_estudiante(service):
    st.subheader("🚫 Desactivar Estudiante")
    st.warning("⚠️ La desactivación oculta al estudiante pero mantiene su historial.")
    
    estudiantes = service.obtener_activos()  # Solo mostrar activos para desactivar
    if not estudiantes:
        st.info("📝 No hay estudiantes activos para desactivar.")
        return

    opciones = [f"ID: {e[0]} - {e[2]} {e[3]} (DNI: {e[1]})" for e in estudiantes]
    seleccionado = st.selectbox("Seleccionar Estudiante a Desactivar", opciones, key="desactivar_estudiante")
    
    if seleccionado:
        estudiante_id = estudiantes[opciones.index(seleccionado)][0]
        estudiante_nombre = f"{estudiantes[opciones.index(seleccionado)][2]} {estudiantes[opciones.index(seleccionado)][3]}"
        
        st.error(f"¿Estás seguro de que deseas desactivar a **{estudiante_nombre}**?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirmar Desactivación", use_container_width=True, type="primary"):
                if service.desactivar(estudiante_id):
                    st.success(f"✅ Estudiante **{estudiante_nombre}** desactivado correctamente")
                    st.rerun()
                else:
                    st.error("❌ Error al desactivar el estudiante")
        
        with col2:
            if st.button("❌ Cancelar", use_container_width=True):
                st.info("Operación cancelada")

def mostrar_estudiantes_desactivados(service):
    st.subheader("🔄 Estudiantes Desactivados")
    
    estudiantes = service.obtener_inactivos()
    if not estudiantes:
        st.info("📝 No hay estudiantes desactivados.")
        return

    st.warning(f"Se encontraron {len(estudiantes)} estudiante(s) desactivado(s)")
    
    for estudiante in estudiantes:
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{estudiante[2]} {estudiante[3]}**")
                st.caption(f"DNI: {estudiante[1]} | Edad: {estudiante[4]} | Sección: {estudiante[5]}")
            with col2:
                st.write(f"ID: {estudiante[0]}")
            with col3:
                if st.button("🔄 Reactivar", key=f"reactivar_{estudiante[0]}"):
                    if service.reactivar(estudiante[0]):
                        st.success(f"✅ Estudiante reactivado correctamente")
                        st.rerun()
                    else:
                        st.error("❌ Error al reactivar el estudiante")
            st.divider()








