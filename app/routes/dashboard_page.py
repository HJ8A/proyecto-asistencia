import streamlit as st
def mostrar_dashboard(db):
    st.header("📊 Dashboard")
    
    # Obtener datos de estudiantes
    estudiantes = db.obtener_estudiantes()
    
    if estudiantes:
        total_estudiantes = len(estudiantes)
        # Calcular estadísticas básicas
        edades = [e[4] for e in estudiantes if e[4] is not None]
        edad_promedio = sum(edades) / len(edades) if edades else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Estudiantes", total_estudiantes)
        with col2:
            st.metric("Edad Promedio", f"{edad_promedio:.1f} años")
        with col3:
            secciones = len(set(e[5] for e in estudiantes if e[5]))
            st.metric("Secciones", secciones)
        
        # Mostrar últimos estudiantes registrados
        st.subheader("Últimos Estudiantes Registrados")
        # Ordenar por fecha de registro (asumiendo que el último elemento es la fecha)
        estudiantes_ordenados = sorted(estudiantes, key=lambda x: x[6] if x[6] else "", reverse=True)[:5]
        
        for estudiante in estudiantes_ordenados:
            st.write(f"**{estudiante[2]} {estudiante[3]}** - DNI: {estudiante[1]} - Edad: {estudiante[4]}")
    else:
        st.info("No hay estudiantes registrados aún.")