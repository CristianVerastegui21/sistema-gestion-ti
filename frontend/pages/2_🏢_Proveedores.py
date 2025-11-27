import streamlit as st
import requests
import pandas as pd
import os

st.set_page_config(page_title="Proveedores", page_icon="🏢", layout="wide")
API_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")

st.title("🏢 Gestión de Proveedores")

tab1, tab2 = st.tabs(["Listado", "Nuevo Proveedor"])

with tab1:
    try:
        response = requests.get(f"{API_URL}/api/proveedores/proveedores", timeout=5)
        
        if response.status_code == 200:
            proveedores = response.json()
            
            # --- CORRECCIÓN CLAVE: Verificar si es lista ---
            if isinstance(proveedores, list):
                if len(proveedores) > 0:
                    df = pd.DataFrame(proveedores)
                    # Seleccionamos columnas que existan para evitar errores
                    cols = [c for c in ['razon_social', 'ruc', 'telefono', 'email', 'contacto_nombre'] if c in df.columns]
                    st.dataframe(df[cols], use_container_width=True)
                else:
                    st.info("No hay proveedores registrados aún.")
            else:
                st.error(f"Error inesperado en datos: {proveedores}")
        else:
            st.error(f"Error del servidor: {response.status_code}")
            st.write(response.text)
            
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")

with tab2:
    with st.form("nuevo_prov"):
        col1, col2 = st.columns(2)
        with col1:
            razon = st.text_input("Razón Social*")
            ruc = st.text_input("RUC*")
            email = st.text_input("Email")
        with col2:
            contacto = st.text_input("Nombre Contacto")
            telefono = st.text_input("Teléfono")
            web = st.text_input("Sitio Web")
            
        if st.form_submit_button("Registrar Proveedor"):
            if not razon or not ruc:
                st.warning("Razón Social y RUC son obligatorios")
            else:
                data = {
                    "razon_social": razon, "ruc": ruc, "email": email, 
                    "contacto_nombre": contacto, "telefono": telefono, "sitio_web": web
                }
                try:
                    res = requests.post(f"{API_URL}/api/proveedores/proveedores", json=data)
                    if res.status_code == 200: 
                        st.success("Proveedor registrado")
                    else: 
                        st.error(f"Error: {res.text}")
                except Exception as e:
                    st.error(f"Error al enviar: {e}")