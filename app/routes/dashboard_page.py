import streamlit as st
from datetime import datetime, date

def mostrar_dashboard(db):
    st.header("📊 Dashboard")
    
    # Obtener datos de estudiantes
    estudiantes = db.obtener_estudiantes()
    
    if estudiantes:
        total_estudiantes = len(estudiantes)
        
        # Calcular edades a partir de fecha_nacimiento
        edades = []
        hoy = date.today()
        
        for estudiante in estudiantes:
            fecha_nacimiento = estudiante[4]  # índice 4 es fecha_nacimiento
            if fecha_nacimiento:
                try:
                    # Convertir string a fecha
                    if isinstance(fecha_nacimiento, str):
                        fecha_nac = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
                    else:
                        fecha_nac = fecha_nacimiento
                    
                    # Calcular edad
                    edad = hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
                    edades.append(edad)
                except Exception as e:
                    print(f"Error calculando edad: {e}")
        
        edad_promedio = sum(edades) / len(edades) if edades else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Estudiantes", total_estudiantes)
        with col2:
            st.metric("Edad Promedio", f"{edad_promedio:.1f} años")
        with col3:
            # La sección está en el índice 8 (después de los nuevos campos)
            secciones = len(set(e[8] for e in estudiantes if e[8]))
            st.metric("Secciones", secciones)
        
        # Mostrar últimos estudiantes registrados
        st.subheader("Últimos Estudiantes Registrados")
        # Ordenar por fecha de registro (índice 9)
        estudiantes_ordenados = sorted(estudiantes, key=lambda x: x[9] if x[9] else "", reverse=True)[:5]
        
        for estudiante in estudiantes_ordenados:
            # Calcular edad para mostrar
            fecha_nacimiento = estudiante[4]
            edad_display = "N/A"
            if fecha_nacimiento:
                try:
                    if isinstance(fecha_nacimiento, str):
                        fecha_nac = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
                    else:
                        fecha_nac = fecha_nacimiento
                    edad_display = hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
                except:
                    pass
            
            st.write(f"**{estudiante[2]} {estudiante[3]}** - DNI: {estudiante[1]} - Edad: {edad_display}")
    else:
        st.info("No hay estudiantes registrados aún.")