import streamlit as st
import pandas as pd
from datetime import datetime

def gestion_academica(service):
    st.header("🏫 Académica")
    
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

    #with subtab5:
    #   reactivar_profesor(service)

# ========== SECCIONES ==========
def gestion_secciones(service):
    st.subheader("📚 Gestión de Secciones")
    
    # Mostrar lista de secciones
    secciones = service.obtener_secciones()
    
    if secciones:
        df = pd.DataFrame(secciones, columns=['ID', 'Nombre', 'Letra', 'Grado', 'Nivel', 'Capacidad', 'Activo'])
        df['Activo'] = df['Activo'].apply(lambda x: '✅ Sí' if x == 1 else '❌ No')

        df_display = df[['Nombre', 'Letra', 'Grado', 'Nivel', 'Capacidad', 'Activo']]

        # Calcular altura dinámica basada en el número de filas
        altura_tabla = min(120 + len(df) * 35, 400)
        st.dataframe(df_display, use_container_width=True, height=altura_tabla)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Secciones", len(secciones))
        with col2:
            activas = sum(1 for s in secciones if s[6] == 1)
            st.metric("Secciones Activas", activas)
    else:
        st.info("📝 No hay secciones registradas.")
    
    # Formularios de registro y edición en la misma vista
    col1, col2 = st.columns(2)
    
    with col1:
        registrar_seccion(service)
    
    with col2:
        editar_seccion(service)

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
        
        activo = st.checkbox(
            "Sección Activa",
            value=True,
            help="Marcar si la sección está activa"
        )
        
        # Obtener el ID del grado seleccionado
        grado_id = grado_seleccionado[0] if grado_seleccionado[0] != "" else None
        
        st.markdown("**\\* Campos obligatorios**")
        
        submitted = st.form_submit_button(
            "📝 Registrar Sección", 
            width='stretch',
            type="primary"
        )
        
        if submitted:
            if not nombre or not letra or not grado_id:
                st.error("❌ Por favor complete todos los campos obligatorios")
            else:
                try:
                   
                    seccion_id = service.agregar_seccion(grado_id, nombre, letra, capacidad, 1 if activo else 0)
                    
                    if seccion_id:
                        st.success(f"✅ Sección **{nombre}** registrada correctamente")
                        st.rerun()
                    else:
                        st.error("❌ Error al registrar la sección")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

def editar_seccion(service):
    st.subheader("✏️ Editar Sección")
    
    secciones = service.obtener_secciones() 
    
    if not secciones:
        st.info("📝 No hay secciones registradas.")
        return
        
    # Obtener grados activos (solo para selección)
    grados = service.obtener_grados_activos()
    opciones_grados = [(g[0], f"{g[3]} - {g[1]}") for g in grados]
    
    # Mostrar secciones activas e inactivas - CORREGIDO
    opciones_secciones = [("", "Seleccionar sección...")] 
    for s in secciones:
        # Estructura según debug: (id, nombre, letra, grado_nombre, nivel_nombre, capacidad, activo)
        estado = " (❌ Inactiva)" if not s[6] else ""  # s[6] = activo (índice 6)
        # Mostrar nombre y letra de la sección: s[1] = nombre, s[2] = letra
        opciones_secciones.append((s[0], f"{s[1]} ({s[2]}){estado}"))
    
    seleccionada = st.selectbox("Seleccionar Sección a Editar", opciones_secciones, format_func=lambda x: x[1])
    
    if seleccionada and seleccionada[0]:
        seccion_id = seleccionada[0]
        datos_seccion = service.obtener_seccion_por_id(seccion_id)
        
        if datos_seccion:
            # Estructura según debug: (id, nombre, letra, grado_nombre, nivel_nombre, capacidad, activo)
            # Para encontrar el grado actual, necesitamos obtener el grado_id de otra manera
            # ya que en datos_seccion no tenemos el grado_id directamente
            grado_nombre_actual = datos_seccion[3]  # grado_nombre en índice 3
            
            # Buscar el grado_id basado en el nombre del grado
            grado_actual_id = None
            grado_actual_index = 0
            for i, (grado_id, grado_texto) in enumerate(opciones_grados):
                if grado_nombre_actual in grado_texto:
                    grado_actual_id = grado_id
                    grado_actual_index = i
                    break
            
            with st.form("editar_seccion"):
                col1, col2 = st.columns(2)
                
                with col1:
                    # CORREGIDO: índices según la estructura real
                    nombre = st.text_input(
                        "Nombre de la Sección*",
                        value=datos_seccion[1],  # nombre en índice 1
                        help="Ej: Sección Única Primaria"
                    )
                    letra = st.text_input(
                        "Letra*",
                        value=datos_seccion[2],  # letra en índice 2
                        max_chars=1,
                        help="Letra identificadora (U = Única)"
                    )
                    
                with col2:
                    # CORREGIDO: capacidad en índice 5
                    capacidad_value = datos_seccion[5]
                    if isinstance(capacidad_value, str):
                        try:
                            capacidad_value = int(capacidad_value)
                        except (ValueError, TypeError):
                            capacidad_value = 30
                    
                    capacidad = st.number_input(
                        "Capacidad",
                        min_value=1,
                        max_value=50,
                        value=capacidad_value,
                        help="Número máximo de estudiantes"
                    )
                    
                    grado_seleccionado = st.selectbox(
                        "Grado*",
                        options=opciones_grados,
                        index=grado_actual_index,
                        format_func=lambda x: x[1],
                        help="Seleccione el grado al que pertenece la sección"
                    )
                    
                    # CORREGIDO: activo en índice 6
                    activo_value = datos_seccion[6]
                    # Convertir a booleano - si es 0 será False, si es 1 será True
                    activo_bool = bool(activo_value) if activo_value != 0 else False
                    
                    activo = st.checkbox(
                        "Sección Activa", 
                        value=activo_bool,
                        help="Desmarcar para desactivar la sección"
                    )
                
                st.markdown("**\\* Campos obligatorios**")
                
                submitted = st.form_submit_button(
                    "💾 Guardar Cambios", 
                    width='stretch',
                    type="primary"
                )
                
                if submitted:
                    if not nombre or not letra:
                        st.error("❌ Por favor complete todos los campos obligatorios")
                    else:
                        try:
                            # Actualizar sección con el estado activo
                            if service.actualizar_seccion(seccion_id, grado_seleccionado[0], nombre, letra, capacidad, 1 if activo else 0):
                                estado_msg = "activada" if activo else "desactivada"
                                st.success(f"✅ Sección {estado_msg} y actualizada correctamente")
                                st.rerun()
                            else:
                                st.error("❌ Error al actualizar la sección")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

# ========== GRADOS ==========
def gestion_grados(service):
    st.subheader("🎓 Gestión de Grados")
    
    # Mostrar lista de grados
    grados = service.obtener_grados()
    
    if grados:
        df = pd.DataFrame(grados, columns=['ID', 'Nivel', 'Número', 'Nombre', 'Activo'])
        # Ocultar la columna ID
        df_display = df[['Nivel', 'Nombre', 'Activo']]
        df_display['Activo'] = df_display['Activo'].apply(lambda x: '✅ Sí' if x == 1 else '❌ No')
        
        # Calcular altura dinámica basada en el número de filas
        altura_tabla = min(120 + len(df) * 35, 400)
        st.dataframe(df_display, use_container_width=True, height=altura_tabla)
        
        st.metric("Total Grados", len(grados))
    else:
        st.info("📝 No hay grados registrados.")
    
    # Formularios de registro y edición en la misma vista
    col1, col2 = st.columns(2)
    
    with col1:
        registrar_grado(service)
    
    with col2:
        editar_grado(service)

def registrar_grado(service):
    st.subheader("➕ Registrar Nuevo Grado")
    
    # Obtener niveles
    niveles = service.obtener_niveles()
    opciones_niveles = [("", "Seleccionar nivel...")] + [(n[0], f"{n[1]}") for n in niveles]
    
    with st.form("nuevo_grado", clear_on_submit=True):
        nombre = st.text_input(
            "Nombre del Grado*",
            placeholder="Ej: 1ro Primaria",
            help="Nombre completo del grado"
        )
        
        nivel_seleccionado = st.selectbox(
            "Nivel Educativo*",
            options=opciones_niveles,  # Corregido: era opciones_secciones
            format_func=lambda x: x[1],
            help="Seleccione el nivel educativo"
        )
        
        activo = st.checkbox(
            "Grado Activo",
            value=True,
            help="Marcar si el grado está activo"
        )
        
        # Obtener el ID del nivel seleccionado
        nivel_id = nivel_seleccionado[0] if nivel_seleccionado[0] != "" else None
        
        st.markdown("**\\* Campos obligatorios**")
        
        submitted = st.form_submit_button(
            "📝 Registrar Grado", 
            width='stretch',  # Cambiado por use_container_width=True
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
                    
                    grado_id = service.agregar_grado(nivel_id, nombre, numero, 1 if activo else 0)
                    if grado_id:
                        st.success(f"✅ Grado **{nombre}** registrado correctamente")
                        st.rerun()
                    else:
                        st.error("❌ Error al registrar el grado")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

def editar_grado(service):
    st.subheader("✏️ Editar Grado")
    
    grados = service.obtener_grados()  # Este ya devuelve activos e inactivos
    
    if not grados:
        st.info("📝 No hay grados registrados.")
        return
        
    # Obtener niveles
    niveles = service.obtener_niveles()
    opciones_niveles = [(n[0], f"{n[1]}") for n in niveles]
    
    # Mostrar grados activos e inactivos, marcando los inactivos
    opciones_grados = [("", "Seleccionar grado...")] 
    for g in grados:
        # g[0]=id, g[1]=nombre, g[2]=numero, g[3]=nivel_nombre, g[4]=activo
        estado = " (❌ Inactivo)" if not g[4] else ""  # g[4] = activo
        opciones_grados.append((g[0], f"{g[1]} - {g[3]}{estado}"))
    
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
                nombre = st.text_input(
                    "Nombre del Grado*",
                    value=datos_grado[2],  # nombre en índice 2
                    help="Ej: Primaria Única, Secundaria Única"
                )
                
                nivel_seleccionado = st.selectbox(
                    "Nivel Educativo*",
                    options=opciones_niveles,
                    index=nivel_actual_index,
                    format_func=lambda x: x[1],
                    help="Seleccione el nivel educativo"
                )
                
                activo = st.checkbox(
                    "Grado Activo",
                    value=bool(datos_grado[4]),  # activo en índice 4
                    help="Desmarcar para desactivar el grado (no aparecerá en listas)"
                )
                
                st.markdown("**\\* Campos obligatorios**")
                
                if st.form_submit_button("💾 Guardar Cambios", width='stretch', type="primary"):
                    if not nombre:
                        st.error("❌ Por favor complete todos los campos obligatorios")
                    else:
                        try:
                            # Mantener el número de orden existente (no mostrarlo al usuario)
                            numero_actual = datos_grado[3]  # numero en índice 3
                            
                            if service.actualizar_grado(grado_id, nivel_seleccionado[0], nombre, numero_actual, 1 if activo else 0):
                                estado_msg = "activado" if activo else "desactivado"
                                st.success(f"✅ Grado {estado_msg} y actualizado correctamente")
                                st.rerun()
                            else:
                                st.error("❌ Error al actualizar el grado")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

def mostrar_lista_grados(service):
    grados = service.obtener_grados()
    
    if grados:
        df = pd.DataFrame(grados, columns=['ID', 'Nivel', 'Número', 'Nombre', 'Activo'])
        # Ocultar la columna ID
        df_display = df[['Nivel', 'Nombre', 'Activo']]
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
    
    grados = service.obtener_grados()  # Este ya devuelve activos e inactivos
    
    if not grados:
        st.info("📝 No hay grados registrados.")
        return
        
    # Obtener niveles
    niveles = service.obtener_niveles()
    opciones_niveles = [(n[0], f"{n[1]}") for n in niveles]
    
    # Mostrar grados activos e inactivos, marcando los inactivos
    opciones_grados = [("", "Seleccionar grado...")] 
    for g in grados:
        # g[0]=id, g[1]=nombre, g[2]=numero, g[3]=nivel_nombre, g[4]=activo
        estado = " (❌ Inactivo)" if not g[4] else ""  # g[4] = activo
        opciones_grados.append((g[0], f"{g[1]} - {g[3]}{estado}"))
    
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
                        value=datos_grado[2],  # nombre en índice 2
                        help="Ej: Primaria Única, Secundaria Única"
                    )
                    numero = st.number_input(
                        "Número de Orden*",
                        min_value=1,
                        max_value=12,
                        value=datos_grado[3],  # numero en índice 3
                        help="1 = Primero, 2 = Segundo, etc. Para ordenamiento interno"
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
                        " Grado Activo",
                        value=bool(datos_grado[4]),  # activo en índice 4
                        help="Desmarcar para desactivar el grado (no aparecerá en listas)"
                    )
                
                st.markdown("**\\* Campos obligatorios**")
                st.info("💡 **Número de Orden**: Usado para ordenar grados. 1 = Primero, 2 = Segundo, etc.")
                
                if st.form_submit_button("💾 Guardar Cambios", use_container_width=True, type="primary"):
                    if not nombre:
                        st.error("❌ Por favor complete todos los campos obligatorios")
                    else:
                        try:
                            if service.actualizar_grado(grado_id, nivel_seleccionado[0], nombre, numero, 1 if activo else 0):
                                estado_msg = "activado" if activo else "desactivado"
                                st.success(f"✅ Grado {estado_msg} y actualizado correctamente")
                                st.rerun()
                            else:
                                st.error("❌ Error al actualizar el grado")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

# ========== NIVELES ==========
# ========== NIVELES ==========
def gestion_niveles(service):
    st.subheader("🏛️ Gestión de Niveles Educativos")
    niveles = service.obtener_niveles()
    
    if niveles:
        df = pd.DataFrame(niveles, columns=['ID', 'Nombre', 'Descripción'])
        df_display = df[['Nombre', 'Descripción']]

        # Calcular altura dinámica basada en el número de filas
        # Altura base por fila (aproximadamente 35px por fila + 60px para encabezados)
        altura_fila = 35
        altura_encabezados = 60
        altura_total = len(df) * altura_fila + altura_encabezados
        # Establecer una altura mínima y máxima razonable
        altura_minima = 120
        altura_maxima = 600
        altura_final = max(altura_minima, min(altura_total, altura_maxima))
        
        st.dataframe(df_display, use_container_width=True, height=altura_final)
        
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
        "🔄 Estado Profesor"
    ])

    with subtab1:
        mostrar_lista_profesores(service)

    with subtab2:
        registrar_nuevo_profesor(service)

    with subtab3:
        editar_profesor(service)

    with subtab4:
        estado_profesor(service)

def mostrar_lista_profesores(service):
    st.subheader("📊 Lista de Profesores")
    profesores = service.obtener_profesores()
    
    if profesores:
        df = pd.DataFrame(profesores, columns=[
            'ID', 'DNI', 'Nombre', 'Apellido', 'Fecha_Nacimiento', 'Genero', 
            'Email', 'Teléfono', 'Activo', 'Fecha_Registro'
        ])
        
        # Convertir columnas
        df['Activo'] = df['Activo'].apply(lambda x: '✅ Sí' if x == 1 else '❌ No')
        df['Fecha_Registro'] = pd.to_datetime(df['Fecha_Registro']).dt.strftime('%d/%m/%Y')
        
        # Mostrar solo las columnas que quieres ver
        df_display = df[['DNI', 'Nombre', 'Apellido', 'Email', 'Teléfono', 'Activo', 'Fecha_Registro']]

        # Calcular altura dinámica basada en el número de filas
        altura_tabla = min(120 + len(df) * 35, 400)
        st.dataframe(df_display, use_container_width=True, height=altura_tabla)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Profesores", len(profesores))
        with col2:
            activos = sum(1 for p in profesores if p[8] == 1)  # Activo está en índice 8
            st.metric("Profesores Activos", activos)
        with col3:
            inactivos = sum(1 for p in profesores if p[8] == 0)  # Activo está en índice 8
            st.metric("Profesores Inactivos", inactivos)
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
            fecha_nacimiento = st.date_input(
                "Fecha de Nacimiento*",
                min_value=datetime(1950, 1, 1).date(),
                max_value=datetime.now().date(),
                value=datetime(1980, 1, 1).date(),
                help="Fecha de nacimiento del profesor"
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
            genero = st.selectbox(
                "Género*",
                options=["", "M", "F"],
                format_func=lambda x: "Seleccionar..." if x == "" else "Masculino" if x == "M" else "Femenino",
                help="Género del profesor"
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
            width='stretch',
            type="primary"
        )
        
        if submitted:
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
            
            # Validaciones del DNI
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
                    # Convertir fecha_nacimiento a string para la base de datos
                    fecha_nacimiento_str = fecha_nacimiento.strftime('%Y-%m-%d')
                    
                    profesor_id = service.agregar_profesor(
                        dni, nombre, apellido, fecha_nacimiento_str, genero, 
                        email if email else None, 
                        telefono if telefono else None
                    )
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
            # DEBUG: Ver los datos reales
            #st.write("🔍 Datos del profesor seleccionado:", datos)
            
            # Convertir fecha de nacimiento string a date
            fecha_nacimiento_actual = datetime.strptime(datos[4], '%Y-%m-%d').date() if datos[4] else datetime(1980, 1, 1).date()
            
            with st.form("editar_profesor"):
                #st.markdown('<div class="form-title">✏️ Editar Información del Profesor</div>', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    dni = st.text_input(
                        "DNI *", 
                        value=datos[1],  # DNI en índice 1
                        placeholder="Ej: 75424515",
                        max_chars=8,
                        help="Documento Nacional de Identidad"
                    )
                    nombre = st.text_input(
                        "Nombre *", 
                        value=datos[2],  # Nombre en índice 2
                        placeholder="Ej: Carlos",
                        help="Nombre del profesor"
                    )
                    fecha_nacimiento = st.date_input(
                        "Fecha de Nacimiento *",
                        value=fecha_nacimiento_actual,
                        min_value=datetime(1950, 1, 1).date(),
                        max_value=datetime.now().date(),
                        help="Fecha de nacimiento del profesor"
                    )
                    email = st.text_input(
                        "Email", 
                        value=datos[6] or "",  # Email en índice 6
                        placeholder="Ej: carlos@colegio.edu",
                        help="Correo electrónico"
                    )
                    
                with col2:
                    apellido = st.text_input(
                        "Apellido *", 
                        value=datos[3],  # Apellido en índice 3
                        placeholder="Ej: Rodríguez",
                        help="Apellido del profesor"
                    )
                    genero = st.selectbox(
                        "Género *",
                        options=["M", "F"],
                        index=0 if datos[5] == "M" else 1,  # Género en índice 5
                        format_func=lambda x: "Masculino" if x == "M" else "Femenino",
                        help="Género del profesor"
                    )
                    telefono = st.text_input(
                        "Teléfono", 
                        value=datos[7] or "",  # Teléfono en índice 7
                        placeholder="Ej: +51 987654321",
                        help="Número de teléfono"
                    )
                
                st.markdown("**\\* Campos obligatorios**")
                
                submitted = st.form_submit_button("💾 Guardar Cambios", width='stretch', type="primary")
                
                if submitted:
                    if dni and nombre and apellido and fecha_nacimiento and genero:
                        try:
                            if not dni.isdigit() or len(dni) != 8:
                                st.error("❌ El DNI debe contener solo números y tener exactamente 8 dígitos")
                            else:
                                fecha_nacimiento_str = fecha_nacimiento.strftime('%Y-%m-%d')
                                if service.actualizar_profesor(profesor_id, dni, nombre, apellido, fecha_nacimiento_str, genero, email, telefono):
                                    st.success("✅ Información del profesor actualizada correctamente")
                                    st.rerun()
                                else:
                                    st.error("❌ Error al actualizar la información")
                        except ValueError as e:
                            st.error(f"❌ {e}")
                    else:
                        st.error("❌ Por favor complete todos los campos obligatorios")

def estado_profesor(service):
    st.subheader("🔄 Estado del Profesor")
    
    # Sección para desactivar profesores activos
    st.markdown("### 🚫 Desactivar Profesor")
    st.warning("La desactivación oculta al profesor pero mantiene su historial.")
    
    profesores_activos = service.obtener_profesores_activos()
    if profesores_activos:
        opciones_activos = [f"ID: {p[0]} - {p[2]} {p[3]} (DNI: {p[1]})" for p in profesores_activos]
        seleccionado_desactivar = st.selectbox(
            "Seleccionar Profesor a Desactivar", 
            opciones_activos, 
            key="desactivar_profesor"
        )
        
        if seleccionado_desactivar:
            profesor_id = profesores_activos[opciones_activos.index(seleccionado_desactivar)][0]
            profesor_nombre = f"{profesores_activos[opciones_activos.index(seleccionado_desactivar)][2]} {profesores_activos[opciones_activos.index(seleccionado_desactivar)][3]}"
            
            st.error(f"¿Estás seguro de que deseas desactivar a **{profesor_nombre}**?")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirmar Desactivación", key="btn_desactivar", width='stretch', type="primary"):
                    if service.desactivar_profesor(profesor_id):
                        st.success(f"✅ Profesor **{profesor_nombre}** desactivado correctamente")
                        st.rerun()
                    else:
                        st.error("❌ Error al desactivar el profesor")
            
            with col2:
                if st.button("❌ Cancelar", key="btn_cancelar_desactivar", width='stretch'):
                    st.info("Operación cancelada")
    else:
        st.info("📝 No hay profesores activos para desactivar.")
    
    st.markdown("---")
    
    # Sección para reactivar profesores inactivos
    st.markdown("### ✅ Reactivar Profesor")
    st.success("Reactiva profesores que han sido desactivados previamente.")
    
    profesores_inactivos = service.obtener_profesores_inactivos()
    if profesores_inactivos:
        opciones_inactivos = [f"ID: {p[0]} - {p[2]} {p[3]} (DNI: {p[1]})" for p in profesores_inactivos]
        seleccionado_reactivar = st.selectbox(
            "Seleccionar Profesor a Reactivar", 
            opciones_inactivos, 
            key="reactivar_profesor"
        )
        
        if seleccionado_reactivar:
            profesor_id = profesores_inactivos[opciones_inactivos.index(seleccionado_reactivar)][0]
            profesor_nombre = f"{profesores_inactivos[opciones_inactivos.index(seleccionado_reactivar)][2]} {profesores_inactivos[opciones_inactivos.index(seleccionado_reactivar)][3]}"
            
            st.info(f"¿Estás seguro de que deseas reactivar a **{profesor_nombre}**?")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirmar Reactivación", key="btn_reactivar", width='stretch', type="primary"):
                    if service.reactivar_profesor(profesor_id):
                        st.success(f"✅ Profesor **{profesor_nombre}** reactivado correctamente")
                        st.rerun()
                    else:
                        st.error("❌ Error al reactivar el profesor")
            
            with col2:
                if st.button("❌ Cancelar", key="btn_cancelar_reactivar", width='stretch'):
                    st.info("Operación cancelada")
    else:
        st.info("📝 No hay profesores inactivos para reactivar.")


'''
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
            if st.button("✅ Confirmar Desactivación", width='stretch', type="primary"):
                if service.desactivar_profesor(profesor_id):
                    st.success(f"✅ Profesor **{profesor_nombre}** desactivado correctamente")
                    st.rerun()
                else:
                    st.error("❌ Error al desactivar el profesor")
        
        with col2:
            if st.button("❌ Cancelar", width='stretch'):
                st.info("Operación cancelada")

def reactivar_profesor(service):
    st.subheader("🔄 Reactivar Profesor")
    st.success("✅ Reactiva profesores que han sido desactivados previamente.")
    
    # Obtener profesores inactivos
    profesores = service.obtener_profesores_inactivos()
    if not profesores:
        st.info("📝 No hay profesores inactivos para reactivar.")
        return

    opciones = [f"ID: {p[0]} - {p[2]} {p[3]} (DNI: {p[1]})" for p in profesores]
    seleccionado = st.selectbox("Seleccionar Profesor a Reactivar", opciones, key="reactivar_profesor")
    
    if seleccionado:
        profesor_id = profesores[opciones.index(seleccionado)][0]
        profesor_nombre = f"{profesores[opciones.index(seleccionado)][2]} {profesores[opciones.index(seleccionado)][3]}"
        
        st.info(f"¿Estás seguro de que deseas reactivar a **{profesor_nombre}**?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirmar Reactivación", width='stretch', type="primary"):
                if service.reactivar_profesor(profesor_id):
                    st.success(f"✅ Profesor **{profesor_nombre}** reactivado correctamente")
                    st.rerun()
                else:
                    st.error("❌ Error al reactivar el profesor")
        
        with col2:
            if st.button("❌ Cancelar", width='stretch'):
                st.info("Operación cancelada")
'''