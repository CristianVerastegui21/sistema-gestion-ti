import streamlit as st
import requests
import os
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Gestión TI",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL del API Gateway
API_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")

# --- CORRECCIÓN CSS: Título visible en modo oscuro y claro ---
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        padding: 1rem 0;
        /* Quitamos el gradiente que causaba problemas y usamos el color del tema */
        border-bottom: 2px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6; /* Color suave para tarjetas */
        padding: 1rem;
        border-radius: 8px;
        color: black; /* Forzamos texto negro dentro de tarjetas */
    }
    </style>
""", unsafe_allow_html=True)

def get_dashboard_data():
    try:
        # Aumentamos el timeout a 10 segundos por si la DB está lenta
        response = requests.get(f"{API_URL}/api/reportes/dashboard", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        # Imprimimos el error en la consola de Docker para depurar
        print(f"Error conectando al dashboard: {e}")
        return None

def get_notificaciones():
    try:
        response = requests.get(f"{API_URL}/api/agents/notificaciones?leida=false", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                return data
        return []
    except:
        return []

# Título principal con la clase corregida
st.markdown('<div class="main-header">🖥️ Sistema de Gestión de Equipos de TI</div>', unsafe_allow_html=True)
st.markdown("### Universidad - Centro de Tecnología de Información")

# Sidebar
with st.sidebar:
    st.info("**Usuario:** Admin TI")
    st.divider()
    
    st.subheader("🔔 Notificaciones")
    notificaciones = get_notificaciones()
    if notificaciones:
        st.warning(f"**{len(notificaciones)}** pendientes")
        with st.expander("Ver recientes"):
            for notif in notificaciones[:3]:
                st.caption(f"**{notif.get('tipo','Info')}**: {notif.get('mensaje', '')}")
                st.divider()
    else:
        st.success("Sin notificaciones")

    st.divider()
    if st.button("🔄 Ejecutar Agentes", use_container_width=True):
        with st.spinner("Procesando..."):
            try:
                requests.post(f"{API_URL}/api/agents/run-all-agents", timeout=5)
                st.toast("Agentes ejecutados correctamente")
            except:
                st.error("Error al ejecutar agentes")

# Dashboard Logic
dashboard_data = get_dashboard_data()

if dashboard_data:
    # Fila 1
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📦 Total Equipos", dashboard_data.get("total_equipos", 0))
    c2.metric("✅ Disponibilidad", f"{dashboard_data.get('tasa_disponibilidad', 0)}%")
    c3.metric("💰 Valor Inventario", f"${dashboard_data.get('valor_inventario', 0):,.2f}")
    c4.metric("🔧 Mantenimientos", dashboard_data.get("mantenimientos_mes", 0))
    
    st.divider()
    
    # Fila 2
    c1, c2, c3 = st.columns(3)
    c1.metric("🟢 Operativos", dashboard_data.get("equipos_operativos", 0))
    c2.metric("🔴 En Reparación", dashboard_data.get("equipos_reparacion", 0))
    c3.metric("💵 Gasto Mensual", f"${dashboard_data.get('costo_mantenimiento_mes', 0):,.2f}")

else:
    st.error("⚠️ No hay conexión con el Backend.")
    st.info(f"Intentando conectar a: `{API_URL}`")
    st.warning("Verifique los logs: `docker-compose logs api-gateway`")