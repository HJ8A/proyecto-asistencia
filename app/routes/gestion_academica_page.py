import streamlit as st
import pandas as pd

def gestion_academica(service):
    st.header("🏫 Gestión Académica")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "👨‍🏫 Profesores", 
        "📚 Secciones",
        "🎓 Grados", 
        "🏛️ Niveles"
    ])

    with tab1:
        gestion_profesores(service)

    with tab2:
        gestion_secciones(service)

    with tab3:
        gestion_grados(service)

    with tab4:
        gestion_niveles(service)
# ========== SECCIONES ==========
def gestion_secciones(service):
    st.subheader("📚 Gestión de Secciones")
    
    # Pestañas para diferentes operaciones
    tab1, tab2, tab3 = st.tabs(["📋 Lista de Secciones", "➕ Registrar Sección", "✏️ Editar Sección"])
    
    with tab1:
        mostrar_lista_secciones(service)
    
    with tab2:
        registrar_seccion(service)
    
    with tab3:
        editar_seccion(service)

def mostrar_lista_secciones(service):
    secciones = service.obtener_secciones()
    
    if secciones:
        df = pd.DataFrame(secciones, columns=['ID', 'Nombre', 'Letra', 'Grado', 'Nivel', 'Capacidad', 'Activo'])
        df['Activo'] = df['Activo'].apply(lambda x: '✅ Sí' if x == 1 else '❌ No')

        df_display = df[['Nombre', 'Letra', 'Grado', 'Nivel', 'Capacidad', 'Activo']]
        df_display['Activo'] = df_display['Activo'].apply(lambda x: '✅ Sí' if x == 1 else '❌ No')

        st.dataframe(df_display, use_container_width=True, height=400)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Secciones", len(secciones))
        with col2:
            activas = sum(1 for s in secciones if s[6] == 1)
            st.metric("Secciones Activas", activas)
            
        # Acciones rápidas
        st.subheader("🚀 Acciones Rápidas")
        col1, col2 = st.columns(2)
        with col1:
            seccion_id_desactivar = st.selectbox(
                "Seleccionar sección para desactivar:",
                options=[s[0] for s in secciones if s[6] == 1],
                format_func=lambda x: f"ID {x} - {next(s[1] for s in secciones if s[0] == x)}",
                key="desactivar_seccion_select"
            )
            if seccion_id_desactivar and st.button("🚫 Desactivar Sección", key="btn_desactivar_seccion"):
                if service.desactivar_seccion(seccion_id_desactivar):
                    st.success("✅ Sección desactivada correctamente")
                    st.rerun()
                else:
                    st.error("❌ Error al desactivar la sección")
                    
        with col2:
            secciones_inactivas = [s for s in secciones if s[6] == 0]
            if secciones_inactivas:
                seccion_id_reactivar = st.selectbox(
                    "Seleccionar sección para reactivar:",
                    options=[s[0] for s in secciones_inactivas],
                    format_func=lambda x: f"ID {x} - {next(s[1] for s in secciones_inactivas if s[0] == x)}",
                    key="reactivar_seccion_select"
                )
                if seccion_id_reactivar and st.button("🔄 Reactivar Sección", key="btn_reactivar_seccion"):
                    if service.reactivar_seccion(seccion_id_reactivar):
                        st.success("✅ Sección reactivada correctamente")
                        st.rerun()
                    else:
                        st.error("❌ Error al reactivar la sección")
    else:
        st.info("📝 No hay secciones registradas.")

def registrar_seccion(service):
    st.subheader("➕ Registrar Nueva Sección")
    
    # Obtener grados activos
    grados = service.obtener_grados_activos()
    if not grados:
        st.warning("⚠️ No hay grados activos. Primero registra grados en la pestaña de Grados.")
        return
        
    opciones_grados = [("", "Seleccionar grado...")] + [(g[0], f"{g[3]} - {g[1]}") for g in grados]
    
    with st.form("nueva_seccion", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input(
                "Nombre de la Sección*",
                placeholder="Ej: 1ro Primaria A",
                help="Nombre completo de la sección"
            )
            letra = st.text_input(
                "Letra*",
                placeholder="Ej: A",
                max_chars=1,
                help="Letra que identifica la sección (A, B, C, etc.)"
            )
            
        with col2:
            capacidad = st.number_input(
                "Capacidad",
                min_value=1,
                max_value=50,
                value=30,
                help="Número máximo de estudiantes"
            )
            grado_seleccionado = st.selectbox(
                "Grado*",
                options=opciones_grados,
                format_func=lambda x: x[1],
                help="Seleccione el grado al que pertenece la sección"
            )
        
        # Obtener el ID del grado seleccionado
        grado_id = grado_seleccionado[0] if grado_seleccionado[0] != "" else None
        
        st.markdown("**\\* Campos obligatorios**")
        
        submitted = st.form_submit_button(
            "📝 Registrar Sección", 
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            if not nombre or not letra or not grado_id:
                st.error("❌ Por favor complete todos los campos obligatorios")
            else:
                try:
                    seccion_id = service.agregar_seccion(grado_id, nombre, letra, capacidad)
                    if seccion_id:
                        st.success(f"✅ Sección **{nombre}** registrada correctamente")
                        st.rerun()
                    else:
                        st.error("❌ Error al registrar la sección")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

def editar_seccion(service):
    st.subheader("✏️ Editar Sección")
    
    secciones = service.obtener_secciones_activas()
    if not secciones:
        st.info("📝 No hay secciones activas para editar.")
        return
        
    # Obtener grados activos
    grados = service.obtener_grados_activos()
    opciones_grados = [(g[0], f"{g[3]} - {g[1]}") for g in grados]
    
    opciones_secciones = [("", "Seleccionar sección...")] + [(s[0], f"{s[1]} - {s[3]}") for s in secciones]
    seleccionada = st.selectbox("Seleccionar Sección a Editar", opciones_secciones, format_func=lambda x: x[1])
    
    if seleccionada and seleccionada[0]:
        seccion_id = seleccionada[0]
        datos_seccion = service.obtener_seccion_por_id(seccion_id)
        
        if datos_seccion:
            # Encontrar el índice del grado actual
            grado_actual_id = datos_seccion[3]  # grado_id está en índice 3
            grado_actual_index = 0
            for i, (grado_id, _) in enumerate(opciones_grados):
                if grado_id == grado_actual_id:
                    grado_actual_index = i
                    break
            
            with st.form("editar_seccion"):
                col1, col2 = st.columns(2)
                
                with col1:
                    nombre = st.text_input(
                        "Nombre de la Sección*",
                        value=datos_seccion[1],
                        help="Nombre completo de la sección"
                    )
                    letra = st.text_input(
                        "Letra*",
                        value=datos_seccion[2],
                        max_chars=1,
                        help="Letra que identifica la sección"
                    )
                    
                with col2:
                    capacidad = st.number_input(
                        "Capacidad",
                        min_value=1,
                        max_value=50,
                        value=datos_seccion[5],
                        help="Número máximo de estudiantes"
                    )
                    grado_seleccionado = st.selectbox(
                        "Grado*",
                        options=opciones_grados,
                        index=grado_actual_index,
                        format_func=lambda x: x[1],
                        help="Seleccione el grado al que pertenece la sección"
                    )
                
                st.markdown("**\\* Campos obligatorios**")
                
                if st.form_submit_button("💾 Guardar Cambios", use_container_width=True, type="primary"):
                    if not nombre or not letra:
                        st.error("❌ Por favor complete todos los campos obligatorios")
                    else:
                        try:
                            if service.actualizar_seccion(seccion_id, grado_seleccionado[0], nombre, letra, capacidad):
                                st.success("✅ Sección actualizada correctamente")
                                st.rerun()
                            else:
                                st.error("❌ Error al actualizar la sección")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

# ========== GRADOS ==========
def gestion_grados(service):
    st.subheader("🎓 Gestión de Grados")
    
    tab1, tab2, tab3 = st.tabs(["📋 Lista de Grados", "➕ Registrar Grado", "✏️ Editar Grado"])
    
    with tab1:
        mostrar_lista_grados(service)
    
    with tab2:
        registrar_grado(service)
    
    with tab3:
        editar_grado(service)

def mostrar_lista_grados(service):
    grados = service.obtener_grados()
    
    if grados:
        df = pd.DataFrame(grados, columns=['ID', 'Nivel', 'Nombre', 'Número', 'Activo'])
        # Ocultar la columna ID
        df_display = df[['Nivel', 'Nombre', 'Número', 'Activo']]
        df_display['Activo'] = df_display['Activo'].apply(lambda x: '✅ Sí' if x == 1 else '❌ No')
        
        st.dataframe(df_display, use_container_width=True, height=400)
        
        st.metric("Total Grados", len(grados))
    else:
        st.info("📝 No hay grados registrados.")

def registrar_grado(service):
    st.subheader("➕ Registrar Nuevo Grado")
    
    # Obtener niveles
    niveles = service.obtener_niveles()
    opciones_niveles = [("", "Seleccionar nivel...")] + [(n[0], f"{n[1]}") for n in niveles]
    
    with st.form("nuevo_grado", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input(
                "Nombre del Grado*",
                placeholder="Ej: 1ro Primaria",
                help="Nombre completo del grado"
            )
            
        with col2:
            nivel_seleccionado = st.selectbox(
                "Nivel Educativo*",
                options=opciones_niveles,
                format_func=lambda x: x[1],
                help="Seleccione el nivel educativo"
            )
        
        # Obtener el ID del nivel seleccionado
        nivel_id = nivel_seleccionado[0] if nivel_seleccionado[0] != "" else None
        
        st.markdown("**\\* Campos obligatorios**")
        
        submitted = st.form_submit_button(
            "📝 Registrar Grado", 
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            if not nombre or not nivel_id:
                st.error("❌ Por favor complete todos los campos obligatorios")
            else:
                try:
                    # Calcular automáticamente el número de orden
                    grados_existentes = service.obtener_grados_por_nivel(nivel_id)
                    if grados_existentes:
                        # Encontrar el máximo número actual y sumar 1
                        max_numero = max(grado[2] for grado in grados_existentes)  # índice 2 es el número
                        numero = max_numero + 1
                    else:
                        numero = 1
                    
                    grado_id = service.agregar_grado(nivel_id, nombre, numero)
                    if grado_id:
                        st.success(f"✅ Grado **{nombre}** registrado correctamente (Número: {numero})")
                        st.rerun()
                    else:
                        st.error("❌ Error al registrar el grado")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

def editar_grado(service):
    st.subheader("✏️ Editar Grado")
    
    grados = service.obtener_grados_activos()
    if not grados:
        st.info("📝 No hay grados activos para editar.")
        return
        
    # Obtener niveles
    niveles = service.obtener_niveles()
    opciones_niveles = [(n[0], f"{n[1]}") for n in niveles]
    
    opciones_grados = [("", "Seleccionar grado...")] + [(g[0], f"{g[1]} - {g[2]}") for g in grados]
    seleccionado = st.selectbox("Seleccionar Grado a Editar", opciones_grados, format_func=lambda x: x[1])
    
    if seleccionado and seleccionado[0]:
        grado_id = seleccionado[0]
        datos_grado = service.obtener_grado_por_id(grado_id)
        
        if datos_grado:
            # Encontrar el índice del nivel actual
            nivel_actual_id = datos_grado[1]  # nivel_id está en índice 1
            nivel_actual_index = 0
            for i, (nivel_id, _) in enumerate(opciones_niveles):
                if nivel_id == nivel_actual_id:
                    nivel_actual_index = i
                    break
            
            with st.form("editar_grado"):
                col1, col2 = st.columns(2)
                
                with col1:
                    nombre = st.text_input(
                        "Nombre del Grado*",
                        value=datos_grado[2],
                        help="Nombre completo del grado"
                    )
                    numero = st.number_input(
                        "Número de Orden*",
                        min_value=1,
                        max_value=12,
                        value=datos_grado[3],
                        help="Número que indica el orden del grado"
                    )
                    
                with col2:
                    nivel_seleccionado = st.selectbox(
                        "Nivel Educativo*",
                        options=opciones_niveles,
                        index=nivel_actual_index,
                        format_func=lambda x: x[1],
                        help="Seleccione el nivel educativo"
                    )
                    activo = st.checkbox(
                        "Grado Activo",
                        value=bool(datos_grado[4]),
                        help="Desmarcar para desactivar el grado"
                    )
                
                st.markdown("**\\* Campos obligatorios**")
                
                if st.form_submit_button("💾 Guardar Cambios", use_container_width=True, type="primary"):
                    if not nombre:
                        st.error("❌ Por favor complete todos los campos obligatorios")
                    else:
                        try:
                            if service.actualizar_grado(grado_id, nivel_seleccionado[0], nombre, numero, 1 if activo else 0):
                                st.success("✅ Grado actualizado correctamente")
                                st.rerun()
                            else:
                                st.error("❌ Error al actualizar el grado")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

# ========== NIVELES ==========
def gestion_niveles(service):
    st.subheader("🏛️ Gestión de Niveles Educativos")
    niveles = service.obtener_niveles()
    
    if niveles:
        df = pd.DataFrame(niveles, columns=['ID', 'Nombre', 'Descripción'])
        df_display = df[['Nombre', 'Descripción']]

        st.dataframe(df_display, use_container_width=True, height=400)
        
        st.metric("Total Niveles", len(niveles))
        
        # Edición de niveles
        st.subheader("✏️ Editar Nivel")
        nivel_id_editar = st.selectbox(
            "Seleccionar nivel para editar:",
            options=[n[0] for n in niveles],
            format_func=lambda x: f"ID {x} - {next(n[1] for n in niveles if n[0] == x)}",
            key="editar_nivel_select"
        )
        
        if nivel_id_editar:
            nivel_data = next(n for n in niveles if n[0] == nivel_id_editar)
            with st.form("editar_nivel"):
                nombre = st.text_input("Nombre", value=nivel_data[1])
                descripcion = st.text_area("Descripción", value=nivel_data[2] or "")
                
                if st.form_submit_button("💾 Guardar Cambios", use_container_width=True):
                    if service.actualizar_nivel(nivel_id_editar, nombre, descripcion):
                        st.success("✅ Nivel actualizado correctamente")
                        st.rerun()
                    else:
                        st.error("❌ Error al actualizar el nivel")
    else:
        st.info("📝 No hay niveles registrados.")

# ========== PROFESORES ==========
def gestion_profesores(service):
    st.subheader("👨‍🏫 Gestión de Profesores")
    
    subtab1, subtab2, subtab3, subtab4 = st.tabs([
        "📋 Lista de Profesores", 
        "➕ Registrar Nuevo",
        "✏️ Editar Profesor",
        "🚫 Desactivar Profesor"
    ])

    with subtab1:
        mostrar_lista_profesores(service)

    with subtab2:
        registrar_nuevo_profesor(service)

    with subtab3:
        editar_profesor(service)

    with subtab4:
        desactivar_profesor(service)

def mostrar_lista_profesores(service):
    st.subheader("📊 Lista de Profesores")
    profesores = service.obtener_profesores()
    
    if profesores:
        df = pd.DataFrame(profesores, columns=['ID', 'DNI', 'Nombre', 'Apellido', 'Email', 'Teléfono', 'Activo', 'Fecha Registro'])
        df['Activo'] = df['Activo'].apply(lambda x: '✅ Sí' if x == 1 else '❌ No')
        df['Fecha Registro'] = pd.to_datetime(df['Fecha Registro']).dt.strftime('%d/%m/%Y')
        
        df_display = df[['DNI', 'Nombre', 'Apellido', 'Email', 'Teléfono', 'Activo', 'Fecha Registro']]
        df_display['Activo'] = df_display['Activo'].apply(lambda x: '✅ Sí' if x == 1 else '❌ No')
        df_display['Fecha Registro'] = pd.to_datetime(df_display['Fecha Registro']).dt.strftime('%d/%m/%Y')

        st.dataframe(df_display, use_container_width=True, height=400)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Profesores", len(profesores))
        with col2:
            activos = sum(1 for p in profesores if p[6] == 1)
            st.metric("Profesores Activos", activos)
    else:
        st.info("📝 No hay profesores registrados.")

def registrar_nuevo_profesor(service):
    st.subheader("➕ Registrar Nuevo Profesor")
    
    with st.form("nuevo_profesor", clear_on_submit=True):
        st.markdown(
            '<div style="color: #1a1a1a; background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; font-weight: 600; text-align: center;">'
            '👨‍🏫 Información del Profesor'
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
                key="profesor_dni"
            )
            nombre = st.text_input(
                "Nombre*", 
                placeholder="Carlos",
                help="Nombre del profesor (obligatorio)",
                key="profesor_nombre"
            )
            email = st.text_input(
                "Email", 
                placeholder="carlos@colegio.edu",
                help="Correo electrónico (opcional)",
                key="profesor_email"
            )
            
        with col2:
            apellido = st.text_input(
                "Apellido*", 
                placeholder="Rodríguez",
                help="Apellido del profesor (obligatorio)",
                key="profesor_apellido"
            )
            telefono = st.text_input(
                "Teléfono", 
                placeholder="+51 987654321",
                help="Número de teléfono (opcional)",
                key="profesor_telefono"
            )
        
        st.markdown(
            '<div class="campos-obligatorios">* Campos obligatorios</div>',
            unsafe_allow_html=True
        )
        
        submitted = st.form_submit_button(
            "📝 Registrar Profesor", 
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            errores = []
            
            if not dni:
                errores.append("El DNI es obligatorio")
            if not nombre:
                errores.append("El nombre es obligatorio")
            if not apellido:
                errores.append("El apellido es obligatorio")
            
            if dni:
                if not dni.isdigit():
                    errores.append("El DNI debe contener solo números")
                elif len(dni) != 8:
                    errores.append("El DNI debe tener exactamente 8 dígitos")
                else:
                    try:
                        if service.verificar_dni_profesor_existente(dni):
                            errores.append("El DNI ya está registrado en el sistema")
                    except Exception as e:
                        errores.append(f"Error al verificar DNI: {e}")
            
            if errores:
                for error in errores:
                    st.error(f"❌ {error}")
            else:
                try:
                    profesor_id = service.agregar_profesor(dni, nombre, apellido, email, telefono)
                    if profesor_id:
                        st.success(f"✅ Profesor **{nombre} {apellido}** registrado correctamente con ID: {profesor_id}")
                        st.rerun()
                    else:
                        st.error("❌ Error al registrar el profesor")
                except ValueError as e:
                    st.error(f"❌ {e}")
                except Exception as e:
                    st.error(f"❌ Error inesperado: {e}")

def editar_profesor(service):
    st.subheader("✏️ Editar Información de Profesor")
    
    profesores = service.obtener_profesores_activos()
    if not profesores:
        st.info("📝 No hay profesores activos para editar.")
        return

    opciones = [f"ID: {p[0]} - {p[2]} {p[3]} (DNI: {p[1]})" for p in profesores]
    seleccionado = st.selectbox("Seleccionar Profesor a Editar", opciones, key="editar_profesor")
    
    if seleccionado:
        profesor_id = profesores[opciones.index(seleccionado)][0]
        datos = service.obtener_profesor_por_id(profesor_id)
        
        if datos:
            with st.form("editar_profesor"):
                st.markdown('<div class="form-title">✏️ Editar Información del Profesor</div>', unsafe_allow_html=True)
                
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
                        placeholder="Ej: Carlos",
                        help="Nombre del profesor"
                    )
                    email = st.text_input(
                        "Email", 
                        value=datos[4] or "",
                        placeholder="Ej: carlos@colegio.edu",
                        help="Correo electrónico"
                    )
                    
                with col2:
                    apellido = st.text_input(
                        "Apellido *", 
                        value=datos[3],
                        placeholder="Ej: Rodríguez",
                        help="Apellido del profesor"
                    )
                    telefono = st.text_input(
                        "Teléfono", 
                        value=datos[5] or "",
                        placeholder="Ej: +51 987654321",
                        help="Número de teléfono"
                    )
                
                st.markdown("**\\* Campos obligatorios**")
                
                if st.form_submit_button("💾 Guardar Cambios", use_container_width=True, type="primary"):
                    if dni and nombre and apellido:
                        try:
                            if not dni.isdigit() or len(dni) != 8:
                                st.error("❌ El DNI debe contener solo números y tener exactamente 8 dígitos")
                            else:
                                if service.actualizar_profesor(profesor_id, dni, nombre, apellido, email, telefono):
                                    st.success("✅ Información del profesor actualizada correctamente")
                                    st.rerun()
                                else:
                                    st.error("❌ Error al actualizar la información")
                        except ValueError as e:
                            st.error(f"❌ {e}")
                    else:
                        st.error("❌ Por favor complete todos los campos obligatorios")

def desactivar_profesor(service):
    st.subheader("🚫 Desactivar Profesor")
    st.warning("⚠️ La desactivación oculta al profesor pero mantiene su historial.")
    
    profesores = service.obtener_profesores_activos()
    if not profesores:
        st.info("📝 No hay profesores activos para desactivar.")
        return

    opciones = [f"ID: {p[0]} - {p[2]} {p[3]} (DNI: {p[1]})" for p in profesores]
    seleccionado = st.selectbox("Seleccionar Profesor a Desactivar", opciones, key="desactivar_profesor")
    
    if seleccionado:
        profesor_id = profesores[opciones.index(seleccionado)][0]
        profesor_nombre = f"{profesores[opciones.index(seleccionado)][2]} {profesores[opciones.index(seleccionado)][3]}"
        
        st.error(f"¿Estás seguro de que deseas desactivar a **{profesor_nombre}**?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirmar Desactivación", use_container_width=True, type="primary"):
                if service.desactivar_profesor(profesor_id):
                    st.success(f"✅ Profesor **{profesor_nombre}** desactivado correctamente")
                    st.rerun()
                else:
                    st.error("❌ Error al desactivar el profesor")
        
        with col2:
            if st.button("❌ Cancelar", use_container_width=True):
                st.info("Operación cancelada")
'''
def gestion_secciones(service):
    st.subheader("📚 Gestión de Secciones")
    secciones = service.obtener_secciones()
    
    if secciones:
        df = pd.DataFrame(secciones, columns=['ID', 'Nombre', 'Letra', 'Grado', 'Nivel', 'Capacidad', 'Activo'])
        df['Activo'] = df['Activo'].apply(lambda x: '✅ Sí' if x == 1 else '❌ No')
        
        st.dataframe(df, use_container_width=True, height=400)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Secciones", len(secciones))
        with col2:
            activas = sum(1 for s in secciones if s[6] == 1)
            st.metric("Secciones Activas", activas)
    else:
        st.info("📝 No hay secciones registradas.")



def gestion_grados(service):
    st.subheader("🎓 Gestión de Grados")
    grados = service.obtener_grados()
    
    if grados:
        df = pd.DataFrame(grados, columns=['ID', 'Nivel', 'Nombre', 'Número', 'Activo'])
        df['Activo'] = df['Activo'].apply(lambda x: '✅ Sí' if x == 1 else '❌ No')
        
        st.dataframe(df, use_container_width=True, height=400)
        
        st.metric("Total Grados", len(grados))
    else:
        st.info("📝 No hay grados registrados.")

def gestion_niveles(service):
    st.subheader("🏛️ Gestión de Niveles Educativos")
    niveles = service.obtener_niveles()
    
    if niveles:
        df = pd.DataFrame(niveles, columns=['ID', 'Nombre', 'Descripción'])
        
        st.dataframe(df, use_container_width=True, height=400)
        
        st.metric("Total Niveles", len(niveles))
    else:
        st.info("📝 No hay niveles registrados.")


'''