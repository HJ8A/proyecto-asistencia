import streamlit as st
from datetime import datetime

def mostrar_configuracion(db):
    st.header("⚙️ Configuración del Sistema")
    st.subheader("Horarios")

    with st.form("config_form"):
        hora = st.time_input("Hora de entrada", value=datetime.strptime("08:00", "%H:%M").time())
        tolerancia = st.number_input("Tolerancia (minutos)", min_value=0, max_value=60, value=15)
        if st.form_submit_button("💾 Guardar Configuración"):
            conn = db._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE configuracion 
                SET hora_entrada=?, tolerancia_minutos=?, ultima_actualizacion=CURRENT_TIMESTAMP
                WHERE id=1
            ''', (hora.strftime('%H:%M:%S'), tolerancia))
            conn.commit()
            conn.close()
            st.success("✅ Configuración guardada correctamente")
