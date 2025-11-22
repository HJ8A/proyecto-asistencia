import io
import qrcode
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
        "🚫 Estudiante Activos",
        "📷 Capturar Rostros",
        "📄 Descargar QR"
    ])

    with tab1:
        mostrar_lista_estudiantes(service)

    with tab2:
        registrar_nuevo_estudiante(service)

    with tab3:
        editar_estudiante(service)

    with tab4:  
        gestion_estado_estudiantes(service)

    with tab5:
        capturar_rostros(service)

    with tab6:
        descargar_qr_estudiantes(service)
# ------------------------------------------------------------

def mostrar_lista_estudiantes(service):
    st.subheader("📊 Lista de Estudiantes Registrados")
    estudiantes = service.obtener_todos()

    if estudiantes:
        # Crear DataFrame con todos los datos
        df = pd.DataFrame(estudiantes, columns=[
            'ID', 'DNI', 'Nombre', 'Apellido', 'Fecha Nacimiento', 
            'Género', 'Teléfono', 'Email', 'Sección', 'Fecha Registro'
        ])
        
        # Calcular edad a partir de la fecha de nacimiento
        from datetime import date
        hoy = date.today()
        
        def calcular_edad(fecha_nac):
            if pd.isna(fecha_nac):
                return None
            try:
                # Convertir a datetime si es string
                if isinstance(fecha_nac, str):
                    fecha_nac = pd.to_datetime(fecha_nac)
                # Calcular edad
                return hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
            except:
                return None
        
        df['Edad'] = df['Fecha Nacimiento'].apply(calcular_edad)
        
        df_display = df[[
            'DNI', 'Nombre', 'Apellido', 'Edad', 'Género', 
            'Teléfono', 'Email', 'Sección'
        ]]
        
        df_display = df_display.copy()
        df_display['Edad'] = df_display['Edad'].apply(lambda x: f"{int(x)} años" if pd.notna(x) else "N/A") 

        st.dataframe(df_display, width='stretch', height=400)
        
        # Mostrar estadísticas actualizadas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Estudiantes", len(estudiantes))
        with col2:
            if not df['Edad'].empty:
                edad_promedio = df['Edad'].mean()
                st.metric("Edad Promedio", f"{edad_promedio:.1f} años")
        with col3:
            secciones_unicas = df['Sección'].nunique()
            st.metric("Secciones", secciones_unicas)
    else:
        st.info("📝 No hay estudiantes registrados. Use la pestaña 'Registrar Nuevo' para agregar estudiantes.")

def registrar_nuevo_estudiante(service):
    st.subheader("🎓 Registrar Nuevo Estudiante")
    
    # Obtener secciones activas para el selector
    secciones = service.obtener_secciones_activas()
    opciones_secciones = [("", "Seleccionar sección...")] + [(s[0], f"{s[4]} - {s[3]} - {s[1]}") for s in secciones]
    
    # Inicializar el estado de sesión para los campos del formulario
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {
            'nombre': '', 'apellido': '', 'dni': '', 'fecha_nacimiento': datetime(2005, 1, 1).date(),
            'genero': '', 'email': '', 'telefono': '', 'direccion': '', 
            'nombre_contacto_emergencia': '', 'telefono_contacto_emergencia': '',
            'turno': 'mañana', 'año_escolar': 1, 'seccion_seleccionada': opciones_secciones[0]
        }
    
    with st.form("nuevo_estudiante", clear_on_submit=False):
        st.markdown(
            '<div style="color: #1a1a1a; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; font-weight: 600; text-align: center;">'
            '📝 Información Personal'
            '</div>', 
            unsafe_allow_html=True
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input(
                "Nombre*", 
                value=st.session_state.form_data['nombre'],
                placeholder="Juan",
                help="Nombre del estudiante (obligatorio)",
                key="nombre_input"
            )
            dni = st.text_input(
                "DNI*", 
                value=st.session_state.form_data['dni'],
                placeholder="72545117",
                help="Documento Nacional de Identidad (8 dígitos, obligatorio)",
                max_chars=8,
                key="dni_input"
            )
            fecha_nacimiento = st.date_input(
                "Fecha de Nacimiento*",
                value=st.session_state.form_data['fecha_nacimiento'],
                min_value=datetime(1990, 1, 1).date(),
                max_value=datetime.now().date(),
                help="Fecha de nacimiento del estudiante"
            )
            
        with col2:
            apellido = st.text_input(
                "Apellido*", 
                value=st.session_state.form_data['apellido'],
                placeholder="Pérez",
                help="Apellido del estudiante (obligatorio)",
                key="apellido_input"
            )
            genero = st.selectbox(
                "Género*",
                options=["", "M", "F"],
                index=0 if st.session_state.form_data['genero'] == "" else 1 if st.session_state.form_data['genero'] == "M" else 2,
                format_func=lambda x: "Seleccionar..." if x == "" else "Masculino" if x == "M" else "Femenino",
                help="Género del estudiante"
            )
            # Selector de sección
            seccion_seleccionada = st.selectbox(
                "Sección*",
                options=opciones_secciones,
                index=opciones_secciones.index(st.session_state.form_data['seccion_seleccionada']) if st.session_state.form_data['seccion_seleccionada'] in opciones_secciones else 0,
                format_func=lambda x: x[1],
                help="Seleccione la sección del estudiante",
                key="seccion_select"
            )
        
        # Campos adicionales
        col3, col4 = st.columns(2)
        with col3:
            email = st.text_input(
                "Email", 
                value=st.session_state.form_data['email'],
                placeholder="juan@example.com",
                help="Email del estudiante (opcional)",
                key="email_input"
            )
            telefono = st.text_input(
                "Teléfono", 
                value=st.session_state.form_data['telefono'],
                placeholder="987654321",
                help="Teléfono del estudiante (opcional)",
                key="telefono_input"
            )
            turno = st.selectbox(
                "Turno",
                options=["", "mañana", "tarde", "noche"],
                index=["", "mañana", "tarde", "noche"].index(st.session_state.form_data['turno']),
                format_func=lambda x: "Seleccionar..." if x == "" else x.capitalize(),
                help="Turno del estudiante (opcional)"
            )
        with col4:
            direccion = st.text_input(
                "Dirección", 
                value=st.session_state.form_data['direccion'],
                placeholder="Av. Principal 123",
                help="Dirección del estudiante (opcional)",
                key="direccion_input"
            )
            telefono_contacto_emergencia = st.text_input(
                "Teléfono de Emergencia", 
                value=st.session_state.form_data['telefono_contacto_emergencia'],
                placeholder="987654321",
                help="Teléfono del contacto de emergencia (opcional)",
                key="telefono_emergencia_input"
            )
            año_escolar = st.number_input(
                "Año Escolar", 
                min_value=1, 
                max_value=12, 
                value=st.session_state.form_data['año_escolar'],
                help="Año escolar del estudiante (opcional)",
                key="año_escolar_input"
            )
        
        # Este campo queda fuera de las columnas como solicitaste
        nombre_contacto_emergencia = st.text_input(
            "Contacto de Emergencia", 
            value=st.session_state.form_data['nombre_contacto_emergencia'],
            placeholder="María Pérez",
            help="Nombre del contacto de emergencia (opcional)",
            key="contacto_emergencia_input"
        )
        
        # Obtener el ID de la sección seleccionada
        seccion_id = seccion_seleccionada[0] if seccion_seleccionada[0] != "" else None
        
        st.markdown(
            '<div class="campos-obligatorios">* Campos obligatorios</div>',
            unsafe_allow_html=True
        )
        
        submitted = st.form_submit_button(
            "📝 Registrar Estudiante", 
            width='stretch',
            type="primary"
        )
        
        if submitted:
            # Actualizar el estado de sesión con los valores actuales
            st.session_state.form_data.update({
                'nombre': nombre,
                'apellido': apellido,
                'dni': dni,
                'fecha_nacimiento': fecha_nacimiento,
                'genero': genero,
                'email': email,
                'telefono': telefono,
                'direccion': direccion,
                'nombre_contacto_emergencia': nombre_contacto_emergencia,
                'telefono_contacto_emergencia': telefono_contacto_emergencia,
                'turno': turno,
                'año_escolar': año_escolar,
                'seccion_seleccionada': seccion_seleccionada
            })
            
            # Validaciones
            errores = []
            
            # Validar campos obligatorios
            if not dni:
                errores.append("El DNI es obligatorio")
            if not nombre:
                errores.append("El nombre es obligatorio")
            if not apellido:
                errores.append("El apellido es obligatorio")
            if not fecha_nacimiento:
                errores.append("La fecha de nacimiento es obligatoria")
            if not genero:
                errores.append("El género es obligatorio")
            if not seccion_id:
                errores.append("La sección es obligatoria")
            
            # Validaciones específicas del DNI
            if dni:
                if not dni.isdigit():
                    errores.append("El DNI debe contener solo números")
                elif len(dni) != 8:
                    errores.append("El DNI debe tener exactamente 8 dígitos")
                else:
                    try:
                        if service.verificar_dni_existente(dni):
                            errores.append("El DNI ya está registrado en el sistema")
                    except Exception as e:
                        errores.append(f"Error al verificar DNI: {e}")
            
            if errores:
                for error in errores:
                    st.error(f"❌ {error}")
            else:
                try:
                    # Convertir fecha_nacimiento a string para la base de datos
                    fecha_nacimiento_str = fecha_nacimiento.strftime('%Y-%m-%d')
                    
                    # Registrar estudiante usando el método del servicio que incluye generación de QR
                    estudiante_id = service.agregar_estudiante(
                        dni, nombre, apellido, fecha_nacimiento_str, genero,
                        telefono, email, direccion, nombre_contacto_emergencia,
                        telefono_contacto_emergencia, turno, año_escolar, seccion_id
                    )
                    
                    if estudiante_id:
                        st.success(f"✅ Estudiante **{nombre} {apellido}** registrado correctamente con ID: {estudiante_id}")
                        st.success("📱 Código QR generado automáticamente")
                        
                        # Limpiar el formulario después de un registro exitoso
                        st.session_state.form_data = {
                            'nombre': '', 'apellido': '', 'dni': '', 'fecha_nacimiento': datetime(2005, 1, 1).date(),
                            'genero': '', 'email': '', 'telefono': '', 'direccion': '', 
                            'nombre_contacto_emergencia': '', 'telefono_contacto_emergencia': '',
                            'turno': 'mañana', 'año_escolar': 1, 'seccion_seleccionada': opciones_secciones[0]
                        }
                        st.rerun()
                    else:
                        st.error("❌ Error al registrar el estudiante")
                except ValueError as e:
                    st.error(f"❌ {e}")
                except Exception as e:
                    st.error(f"❌ Error inesperado: {e}")

def editar_estudiante(service):
    st.subheader("✏️ Editar Información de Estudiante")
    
    estudiantes = service.obtener_activos()
    if not estudiantes:
        st.info("📝 No hay estudiantes activos para editar.")
        return

    # Obtener secciones para el selector
    secciones = service.obtener_secciones_activas()
    opciones_secciones = [("", "Seleccionar sección...")] + [(s[0], f"{s[4]} - {s[3]} - {s[1]}") for s in secciones]

    opciones = [f"ID: {e[0]} - {e[2]} {e[3]} (DNI: {e[1]})" for e in estudiantes]
    seleccionado = st.selectbox("Seleccionar Estudiante a Editar", opciones, key="editar_estudiante")
    
    if seleccionado:
        estudiante_id = estudiantes[opciones.index(seleccionado)][0]
        datos = service.obtener_por_id(estudiante_id)
        
        if datos:
            # Encontrar la sección actual del estudiante
            seccion_actual_id = datos[13]  # seccion_id está en índice 13
            seccion_actual_index = 0
            for i, (id_seccion, _) in enumerate(opciones_secciones):
                if id_seccion == seccion_actual_id:
                    seccion_actual_index = i
                    break
            
            with st.form("editar_estudiante"):                
                col1, col2 = st.columns(2)
                
                with col1:
                    nombre = st.text_input(
                        "Nombre *", 
                        value=datos[2],
                        placeholder="Ej: Juan",
                        help="Nombre del estudiante"
                    )
                    dni = st.text_input(
                        "DNI *", 
                        value=datos[1],
                        placeholder="Ej: 12345678",
                        help="Documento Nacional de Identidad"
                    )
                    # Convertir fecha de nacimiento string a date
                    fecha_nacimiento_actual = datetime.strptime(datos[4], '%Y-%m-%d').date() if datos[4] else datetime(2005, 1, 1).date()
                    fecha_nacimiento = st.date_input(
                        "Fecha de Nacimiento *",
                        value=fecha_nacimiento_actual,
                        min_value=datetime(1990, 1, 1).date(),
                        max_value=datetime.now().date(),
                        help="Fecha de nacimiento del estudiante"
                    )
                    
                with col2:
                    apellido = st.text_input(
                        "Apellido *", 
                        value=datos[3],
                        placeholder="Ej: Pérez",
                        help="Apellido del estudiante"
                    )
                    genero = st.selectbox(
                        "Género *",
                        options=["M", "F"],
                        index=0 if datos[5] == "M" else 1,
                        format_func=lambda x: "Masculino" if x == "M" else "Femenino",
                        help="Género del estudiante"
                    )
                    # Selector de sección
                    seccion_seleccionada = st.selectbox(
                        "Sección *",
                        options=opciones_secciones,
                        index=seccion_actual_index,
                        format_func=lambda x: x[1],
                        help="Seleccione la sección del estudiante",
                        key="editar_seccion"
                    )
                
                # Campos adicionales
                col3, col4 = st.columns(2)
                with col3:
                    email = st.text_input(
                        "Email", 
                        value=datos[7] or "",
                        placeholder="juan@example.com",
                        help="Email del estudiante"
                    )
                    telefono = st.text_input(
                        "Teléfono", 
                        value=datos[6] or "",
                        placeholder="987654321",
                        help="Teléfono del estudiante"
                    )
                    turno = st.selectbox(
                        "Turno",
                        options=["mañana", "tarde", "noche"],
                        index=0 if datos[11] == "mañana" else 1 if datos[11] == "tarde" else 2,
                        format_func=lambda x: x.capitalize(),
                        help="Turno del estudiante"
                    )
                with col4:
                    direccion = st.text_input(
                        "Dirección", 
                        value=datos[8] or "",
                        placeholder="Av. Principal 123",
                        help="Dirección del estudiante"
                    )
                    telefono_contacto_emergencia = st.text_input(
                        "Teléfono de Emergencia", 
                        value=datos[10] or "",
                        placeholder="987654321",
                        help="Teléfono del contacto de emergencia"
                    )
                    año_escolar = st.number_input(
                        "Año Escolar", 
                        min_value=1, 
                        max_value=12, 
                        value=datos[12] or 1,
                        help="Año escolar del estudiante"
                    )
                
                # Este campo queda fuera de las columnas
                nombre_contacto_emergencia = st.text_input(
                    "Contacto de Emergencia", 
                    value=datos[9] or "",
                    placeholder="María Pérez",
                    help="Nombre del contacto de emergencia"
                )
                
                # Obtener el ID de la sección seleccionada
                seccion_id = seccion_seleccionada[0] if seccion_seleccionada[0] != "" else None
                
                st.markdown("**\\* Campos obligatorios**")
                
                if st.form_submit_button("💾 Guardar Cambios", use_container_width=True, type="primary"):
                    if dni and nombre and apellido and fecha_nacimiento and genero and seccion_id:
                        try:
                            if not dni.isdigit() or len(dni) != 8:
                                st.error("❌ El DNI debe contener solo números y tener exactamente 8 dígitos")
                            else:
                                # Convertir fecha_nacimiento a string para la base de datos
                                fecha_nacimiento_str = fecha_nacimiento.strftime('%Y-%m-%d')
                                
                                if service.actualizar(
                                    estudiante_id, dni, nombre, apellido, fecha_nacimiento_str, genero,
                                    telefono, email, direccion, nombre_contacto_emergencia,
                                    telefono_contacto_emergencia, turno, año_escolar, seccion_id
                                ):
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
                    # ✅ CORRECCIÓN: Creamos una instancia de CamaraManager con la base de datos
                    camara_manager = CamaraManager(service.db)
                    exito = camara_manager.capturar_rostros_interactivo(
                        estudiante_id=estudiante_id,
                        nombre=nombre,
                        apellido=apellido,
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

'''
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
'''

def descargar_qr_estudiantes(service):
    st.subheader("📄 Descargar Códigos QR de Estudiantes")
    
    # Obtener lista de estudiantes con sus QR
    estudiantes = service.obtener_estudiantes_con_qr()
    
    if not estudiantes:
        st.warning("📝 No hay estudiantes con códigos QR generados.")
        st.info("💡 Los códigos QR se generan automáticamente al registrar nuevos estudiantes.")
        return
    
    # Selector de estudiante
    opciones_estudiantes = [(est[0], f"{est[1]} {est[2]} - DNI: {est[3]} - QR: {est[4]}") for est in estudiantes]
    
    if not opciones_estudiantes:
        st.warning("No hay estudiantes con QR disponibles")
        return
        
    estudiante_seleccionado = st.selectbox(
        "Selecciona un estudiante:",
        options=opciones_estudiantes,
        format_func=lambda x: x[1],
        key="selector_estudiante_qr"
    )
    
    if estudiante_seleccionado:
        estudiante_id = estudiante_seleccionado[0]
        
        # Obtener y mostrar QR
        qr_img = service.obtener_qr_imagen(estudiante_id)
        
        if qr_img:
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # CORRECCIÓN: Convertir PIL Image a bytes para st.image
                import io
                buf = io.BytesIO()
                qr_img.save(buf, format="PNG")
                buf.seek(0)
                
                st.image(buf, caption=f"QR del Estudiante", use_container_width=True)
            
            with col2:
                # Información del estudiante
                estudiante_info = next(est for est in estudiantes if est[0] == estudiante_id)
                st.info(f"""
                **Información del Estudiante:**
                - **Nombre:** {estudiante_info[1]} {estudiante_info[2]}
                - **DNI:** {estudiante_info[3]}
                - **Código QR:** `{estudiante_info[4]}`
                - **Sección:** {estudiante_info[5] or 'No asignada'}
                """)
            
            # Botón de descarga
            buf_download = io.BytesIO()
            qr_img.save(buf_download, format="PNG")
            buf_download.seek(0)
            
            st.download_button(
                label="📥 Descargar Código QR",
                data=buf_download,
                file_name=f"QR_{estudiante_info[1]}_{estudiante_info[2]}.png",
                mime="image/png",
                use_container_width=True
            )
        else:
            st.error("❌ No se pudo generar el código QR para este estudiante")

def gestion_estado_estudiantes(service):
    st.subheader("🚫 Gestión de Estado de Estudiantes")
    
    # Sección para desactivar estudiantes
    st.markdown("### Desactivar Estudiante")
    st.warning("⚠️ La desactivación oculta al estudiante pero mantiene su historial.")
    
    estudiantes_activos = service.obtener_activos()
    if not estudiantes_activos:
        st.info("📝 No hay estudiantes activos para desactivar.")
    else:
        opciones = [f"ID: {e[0]} - {e[2]} {e[3]} (DNI: {e[1]})" for e in estudiantes_activos]
        seleccionado = st.selectbox("Seleccionar Estudiante a Desactivar", opciones, key="desactivar_estudiante")
        
        if seleccionado:
            estudiante_id = estudiantes_activos[opciones.index(seleccionado)][0]
            estudiante_nombre = f"{estudiantes_activos[opciones.index(seleccionado)][2]} {estudiantes_activos[opciones.index(seleccionado)][3]}"
            
            st.error(f"¿Estás seguro de que deseas desactivar a **{estudiante_nombre}**?")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirmar Desactivación", use_container_width=True, type="primary", key="confirmar_desactivar"):
                    if service.desactivar(estudiante_id):
                        st.success(f"✅ Estudiante **{estudiante_nombre}** desactivado correctamente")
                        st.rerun()
                    else:
                        st.error("❌ Error al desactivar el estudiante")
            
            with col2:
                if st.button("❌ Cancelar", use_container_width=True, key="cancelar_desactivar"):
                    st.info("Operación cancelada")
    
    st.divider()
    
    # Sección para estudiantes desactivados
    st.markdown("### Estudiantes Desactivados")
    
    estudiantes_desactivados = service.obtener_inactivos()
    if not estudiantes_desactivados:
        st.info("📝 No hay estudiantes desactivados.")
        return

    st.warning(f"Se encontraron {len(estudiantes_desactivados)} estudiante(s) desactivado(s)")
    
    for estudiante in estudiantes_desactivados:
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