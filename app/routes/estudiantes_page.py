import streamlit as st
import pandas as pd
from datetime import datetime

def gestion_estudiantes(service):
    st.header("👥 Gestión de Estudiantes")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Lista de Estudiantes", 
        "➕ Registrar Nuevo",
        "✏️ Editar Estudiante", 
        "📷 Capturar Rostros"
    ])

    with tab1:
        mostrar_lista_estudiantes(service)

    with tab2:
        registrar_nuevo_estudiante(service)

    with tab3:
        editar_estudiante(service)

    with tab4:
        capturar_rostros(service)

def mostrar_lista_estudiantes(service):
    estudiantes = service.obtener_todos()
    if estudiantes:
        df = pd.DataFrame(estudiantes, columns=['ID', 'Código', 'Nombre', 'Apellido', 'Edad', 'Sección', 'Fecha Registro'])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No hay estudiantes registrados.")

def registrar_nuevo_estudiante(service):
    st.subheader("Registrar Nuevo Estudiante")
    with st.form("nuevo_estudiante"):
        col1, col2 = st.columns(2)
        nombre = col1.text_input("Nombre *")
        apellido = col2.text_input("Apellido *")
        edad = col1.number_input("Edad", min_value=5, max_value=30, value=15)
        seccion = col2.text_input("Sección")
        codigo = col1.text_input("Código (opcional)")

        if st.form_submit_button("Registrar Estudiante"):
            if nombre and apellido:
                service.registrar(nombre, apellido, edad, seccion, codigo)
                st.success(f"✅ Estudiante {nombre} {apellido} registrado correctamente")
            else:
                st.error("❌ Nombre y Apellido son obligatorios")

def editar_estudiante(service):
    st.subheader("Editar Estudiante")
    estudiantes = service.obtener_todos()
    if not estudiantes:
        st.info("No hay estudiantes registrados.")
        return

    opciones = [f"{e[1]} - {e[2]} {e[3]}" for e in estudiantes]
    seleccionado = st.selectbox("Seleccionar Estudiante", opciones)
    estudiante_id = estudiantes[opciones.index(seleccionado)][0]

    datos = service.obtener_por_id(estudiante_id)
    if datos:
        with st.form("editar_estudiante"):
            nombre = st.text_input("Nombre", value=datos[2])
            apellido = st.text_input("Apellido", value=datos[3])
            edad = st.number_input("Edad", value=datos[4])
            seccion = st.text_input("Sección", value=datos[5] or "")
            if st.form_submit_button("Actualizar Información"):
                service.actualizar(estudiante_id, nombre, apellido, edad, seccion)
                st.success("✅ Información actualizada")

def capturar_rostros(service):
    st.subheader("Capturar Rostros (en desarrollo)")
    st.info("Aquí se integrará la captura facial mediante cámara.")
