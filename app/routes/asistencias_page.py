import streamlit as st
from datetime import date, datetime

def registrar_asistencias(service, db):
    st.header("📝 Registro Manual de Asistencias")
    fecha = st.date_input("Fecha", value=date.today())
    estudiantes = db.obtener_estudiantes()
    if not estudiantes:
        st.info("No hay estudiantes registrados.")
        return

    st.subheader("Marcar Asistencias")
    with st.form("asistencias_form"):
        asistencias = []
        for est in estudiantes:
            id_est, _, nombre, apellido, _, seccion, _ = est
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(f"**{nombre} {apellido}** - {seccion or 'Sin sección'}")
            presente = col2.checkbox("Presente", key=f"p_{id_est}")
            tardanza = col3.checkbox("Tardanza", key=f"t_{id_est}")
            if presente or tardanza:
                asistencias.append((id_est, "presente" if presente else "tardanza"))

        if st.form_submit_button("💾 Guardar Asistencias"):
            service.registrar_asistencias(asistencias, fecha)
            st.success(f"✅ {len(asistencias)} asistencias guardadas")
