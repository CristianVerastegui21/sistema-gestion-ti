import streamlit as st
import requests
import pandas as pd
import os
from datetime import date

st.set_page_config(page_title="Mantenimiento", page_icon="🔧", layout="wide")
API_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")

st.title("🔧 Gestión de Mantenimiento")

def get_data(endpoint):
    try:
        res = requests.get(f"{API_URL}/api/{endpoint}", timeout=5)
        if res.status_code == 200:
            return res.json()
    except: pass
    return []

tab1, tab2 = st.tabs(["📅 Calendario y Estado", "➕ Programar Mantenimiento"])

with tab1:
    st.subheader("Historial y Programación")
    mantenimientos = get_data("mantenimientos/mantenimientos")
    
    if mantenimientos and isinstance(mantenimientos, list):
        df = pd.DataFrame(mantenimientos)
        
        # Aseguramos que las columnas existan antes de mostrar
        cols_to_show = ['fecha_programada', 'equipo_nombre', 'codigo_inventario', 'tipo', 'prioridad', 'estado']
        cols_validas = [c for c in cols_to_show if c in df.columns]
        
        if not df.empty:
            # Colorear según prioridad
            def color_priority(val):
                color = 'red' if val == 'urgente' else 'orange' if val == 'alta' else 'green'
                return f'color: {color}'
            
            st.dataframe(df[cols_validas].style.applymap(color_priority, subset=['prioridad'] if 'prioridad' in df.columns else None), use_container_width=True)
        else:
            st.info("No hay mantenimientos registrados.")
    else:
        st.info("No se encontraron registros o hubo un error de conexión.")

with tab2:
    st.subheader("Nueva Orden de Mantenimiento")
    
    # Cargamos equipos para el dropdown
    equipos = get_data("equipos/equipos")
    if equipos and isinstance(equipos, list):
        opciones = {e['id']: f"{e['codigo_inventario']} - {e['nombre']}" for e in equipos}
        
        with st.form("form_mantenimiento"):
            col1, col2 = st.columns(2)
            
            with col1:
                equipo_id = st.selectbox("Seleccionar Equipo", options=list(opciones.keys()), format_func=lambda x: opciones[x])
                tipo = st.selectbox("Tipo de Mantenimiento", ["Preventivo", "Correctivo", "Actualización Software"])
                prioridad = st.selectbox("Prioridad", ["Baja", "Media", "Alta", "Urgente"])
            
            with col2:
                fecha = st.date_input("Fecha Programada", value=date.today())
                descripcion = st.text_area("Descripción del problema / tarea", placeholder="Ej: Limpieza de ventiladores y cambio de pasta térmica")
            
            submitted = st.form_submit_button("💾 Programar Mantenimiento")
            
            if submitted:
                payload = {
                    "equipo_id": equipo_id,
                    "tipo": tipo.lower(),
                    "fecha_programada": str(fecha),
                    "descripcion": descripcion,
                    "prioridad": prioridad.lower()
                }
                
                try:
                    res = requests.post(f"{API_URL}/api/mantenimientos/mantenimientos", json=payload)
                    if res.status_code == 200:
                        st.success("✅ Mantenimiento programado exitosamente")
                    else:
                        st.error(f"Error al programar: {res.text}")
                except Exception as e:
                    st.error(f"Error de conexión: {e}")
    else:
        st.error("No se pudieron cargar los equipos. Verifique el servicio de Equipos.")