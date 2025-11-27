import streamlit as st
import requests
import pandas as pd
import os
from datetime import date

st.set_page_config(page_title="Gestión de Equipos", page_icon="📦", layout="wide")
API_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")

st.title("📦 Gestión de Equipos")

def get_data(endpoint, params=None):
    try:
        response = requests.get(f"{API_URL}/api/{endpoint}", params=params)
        if response.status_code == 200: return response.json()
    except: pass
    return []

tab1, tab2 = st.tabs(["📋 Lista de Equipos", "➕ Nuevo Equipo"])

with tab1:
    col1, col2, col3 = st.columns(3)
    categorias = get_data("equipos/categorias")
    cat_opts = ["Todas"] + [c['nombre'] for c in categorias]
    
    with col1: cat_filter = st.selectbox("Categoría", cat_opts)
    with col2: state_filter = st.selectbox("Estado", ["Todos", "operativo", "en_reparacion", "obsoleto"])
    with col3: 
        st.write("")
        if st.button("🔄 Actualizar"):
            pass

    params = {}
    if cat_filter != "Todas": params['categoria'] = cat_filter
    if state_filter != "Todos": params['estado'] = state_filter

    equipos = get_data("equipos/equipos", params)
    
    if equipos:
        df = pd.DataFrame(equipos)
        st.dataframe(df[['codigo_inventario', 'nombre', 'marca', 'modelo', 'estado_operativo', 'ubicacion_nombre']], use_container_width=True)
    else:
        st.info("No se encontraron equipos")

with tab2:
    st.subheader("Registrar Nuevo Equipo")
    with st.form("new_team"):
        c1, c2 = st.columns(2)
        with c1:
            codigo = st.text_input("Código*")
            nombre = st.text_input("Nombre*")
            marca = st.text_input("Marca")
            modelo = st.text_input("Modelo")
            cat_id = st.selectbox("Categoría*", [c['id'] for c in categorias], format_func=lambda x: next((c['nombre'] for c in categorias if c['id']==x),''))
        with c2:
            serie = st.text_input("Serie")
            costo = st.number_input("Costo", min_value=0.0)
            fecha = st.date_input("Fecha Compra")
            ubicaciones = get_data("equipos/ubicaciones")
            ubi_id = st.selectbox("Ubicación", [u['id'] for u in ubicaciones], format_func=lambda x: next((u['nombre_completo'] for u in ubicaciones if u['id']==x),''))

        if st.form_submit_button("Guardar"):
            data = {
                "codigo_inventario": codigo, "nombre": nombre, "marca": marca,
                "modelo": modelo,
                "categoria_id": cat_id, "numero_serie": serie, "costo_compra": costo,
                "fecha_compra": str(fecha), "ubicacion_actual_id": ubi_id
            }
            
            try:
                res = requests.post(f"{API_URL}/api/equipos/equipos", json=data)
                if res.status_code == 200: 
                    # CAMBIO AQUÍ: Usamos toast o success simple, SIN globos ni rerun
                    st.success("✅ Equipo creado exitosamente.")
                    
                    # st.balloons()  <-- ¡COMENTA O BORRA ESTA LÍNEA! (Es la culpable del error React)
                    # st.rerun()     <-- ¡ESTA TAMBIÉN DEBE ESTAR BORRADA!
                else: 
                    st.error(f"Error al crear: {res.text}")
            except Exception as e:
                st.error(f"Error de conexión: {e}")