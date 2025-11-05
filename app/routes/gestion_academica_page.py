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
        
        st.dataframe(df, use_container_width=True, height=400)
        
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