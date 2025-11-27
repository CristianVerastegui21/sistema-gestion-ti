import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

st.set_page_config(page_title="Reportes", page_icon="📊", layout="wide")
API_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")

st.title("📊 Reportes y Análisis")

# Función auxiliar segura
def get_data_safe(endpoint):
    try:
        res = requests.get(f"{API_URL}/api/reportes/{endpoint}", timeout=5)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list):
                return data
            else:
                # Si no es lista, es un error del backend devuelto como JSON
                st.warning(f"Respuesta inesperada en {endpoint}: {data}")
                return []
        return []
    except Exception as e:
        st.error(f"Error conectando a {endpoint}: {e}")
        return []

tab1, tab2, tab3 = st.tabs(["📈 Gráficos", "📄 Exportar", "🔍 Análisis"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📍 Equipos por Ubicación")
        data = get_data_safe("equipos-por-ubicacion")
        if data:
            fig = px.bar(pd.DataFrame(data), x='ubicacion', y='cantidad', title="Distribución por Ubicación")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos de ubicación")
            
    with col2:
        st.markdown("### 🟢 Equipos por Estado")
        data = get_data_safe("equipos-por-estado")
        if data:
            # Aseguramos nombres de columnas correctos según el API
            df = pd.DataFrame(data)
            if 'estado' in df.columns and 'cantidad' in df.columns:
                fig = px.pie(df, values='cantidad', names='estado', title="Estado Operativo")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Formato de datos incorrecto")

    st.markdown("---")
    st.markdown("### 💵 Costos Mantenimiento (Año Actual)")
    data = get_data_safe(f"costos-mantenimiento?year={datetime.now().year}")
    if data:
        df = pd.DataFrame(data)
        if not df.empty:
            fig = px.line(df, x='mes', y='total_costo', color='tipo', title="Evolución de Costos")
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Exportar Datos")
    col1, col2 = st.columns(2)
    with col1:
        st.info("Generar PDF con listado de equipos")
        
        # Lógica de descarga directa
        if st.button("📄 Generar PDF"):
            with st.spinner("Generando documento..."):
                try:
                    # Hacemos la petición al backend
                    res = requests.post(f"{API_URL}/api/reportes/export/pdf", json={"type": "equipos"})
                    
                    if res.status_code == 200:
                        # Si es exitoso, mostramos el botón de descarga real
                        st.download_button(
                            label="📥 Descargar PDF Ahora",
                            data=res.content,
                            file_name="reporte_equipos.pdf",
                            mime="application/pdf"
                        )
                        st.success("Documento generado. Haz clic arriba para bajarlo.")
                    else:
                        st.error("Error en el servidor al generar PDF")
                except Exception as e:
                    st.error(f"Fallo conexión: {e}")

with tab3:
    st.subheader("Análisis de Valor")
    data = get_data_safe("equipos-por-categoria")
    if data:
        st.dataframe(pd.DataFrame(data), use_container_width=True)