import streamlit as st
import pandas as pd
import plotly.express as px

def mostrar_reportes(db):
    st.header("📈 Reportes-Estadisticas")

    tab1, tab2, tab3 = st.tabs(["📊 Generales", "📅 Por Período", "👤 Por Estudiante"])
    with tab1:
        mostrar_generales(db)

def mostrar_generales(db):
    conn = db._get_connection()
    query = "SELECT estado, COUNT(*) as count FROM asistencias GROUP BY estado"
    df = pd.read_sql_query(query, conn)
    conn.close()
    if not df.empty:
        fig = px.pie(df, values="count", names="estado", title="Distribución de Asistencias")
        st.plotly_chart(fig, use_container_width=True)
