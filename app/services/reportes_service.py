import pandas as pd
import plotly.express as px
from datetime import date
from app.data.database import DatabaseManager

class ReportesService:
    def __init__(self):
        self.db = DatabaseManager()

    def obtener_metricas_generales(self):
        total_estudiantes = len(self.db.obtener_estudiantes())
        _, _, ids = self.db.cargar_encodings_faciales()
        hoy = date.today()
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT estudiante_id) FROM asistencias WHERE fecha = ?", (hoy,))
        asistencias_hoy = cursor.fetchone()[0]
        conn.close()

        return {
            "total": total_estudiantes,
            "rostros": len(set(ids)),
            "hoy": asistencias_hoy,
            "porcentaje": (asistencias_hoy / total_estudiantes * 100 if total_estudiantes else 0)
        }

    def obtener_grafico_asistencias(self):
        conn = self.db._get_connection()
        df = pd.read_sql_query("""
            SELECT fecha, COUNT(DISTINCT estudiante_id) as asistencias
            FROM asistencias
            WHERE fecha >= date('now', '-7 days')
            GROUP BY fecha
            ORDER BY fecha
        """, conn)
        conn.close()

        if df.empty:
            return px.line(title="Sin datos recientes")
        return px.line(df, x="fecha", y="asistencias", title="Asistencias por Día", markers=True)

    def obtener_ultimas_asistencias(self):
        conn = self.db._get_connection()
        df = pd.read_sql_query("""
            SELECT a.fecha, a.hora, e.nombre || ' ' || e.apellido AS nombre_completo,
                   a.estado, a.metodo_deteccion
            FROM asistencias a
            JOIN estudiantes e ON e.id = a.estudiante_id
            ORDER BY a.fecha DESC, a.hora DESC
            LIMIT 10
        """, conn)
        conn.close()
        return df
