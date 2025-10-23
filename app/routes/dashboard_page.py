import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

def mostrar_dashboard(db):
    st.header("📊 Dashboard Principal")

    total_estudiantes = len(db.obtener_estudiantes())
    _, _, ids = db.cargar_encodings_faciales()
    estudiantes_con_rostro = len(set(ids))

    hoy = date.today()
    conn = db._get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(DISTINCT estudiante_id) FROM asistencias WHERE fecha = ?", (hoy,))
    asistencias_hoy = cursor.fetchone()[0]
    conn.close()

    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Estudiantes", total_estudiantes)
    col2.metric("Con Rostro Registrado", estudiantes_con_rostro)
    col3.metric("Asistencias Hoy", asistencias_hoy)
    col4.metric("Porcentaje Hoy", f"{(asistencias_hoy / total_estudiantes * 100 if total_estudiantes > 0 else 0):.1f}%")

    mostrar_grafico_semanal(db)
    mostrar_ultimas_asistencias(db)

def mostrar_grafico_semanal(db):
    conn = db._get_connection()
    query = '''
        SELECT fecha, COUNT(DISTINCT estudiante_id) as asistencias
        FROM asistencias 
        WHERE fecha >= date('now', '-7 days')
        GROUP BY fecha
        ORDER BY fecha
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()

    if not df.empty:
        fig = px.line(df, x='fecha', y='asistencias', title="Asistencias por Día", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos recientes de asistencias.")

def mostrar_ultimas_asistencias(db):
    conn = db._get_connection()
    query = '''
        SELECT a.fecha, a.hora, e.nombre, e.apellido, a.estado, a.metodo_deteccion
        FROM asistencias a
        JOIN estudiantes e ON a.estudiante_id = e.id
        ORDER BY a.fecha DESC, a.hora DESC
        LIMIT 10
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()

    if not df.empty:
        df['Nombre Completo'] = df['nombre'] + ' ' + df['apellido']
        df['Estado'] = df['estado'].map({
            'presente': '✅ Presente',
            'tardanza': '⚠️ Tardanza',
            'ausente': '❌ Ausente'
        })
        st.dataframe(df[['fecha', 'hora', 'Nombre Completo', 'Estado', 'metodo_deteccion']], use_container_width=True)
    else:
        st.info("No hay asistencias registradas.")
