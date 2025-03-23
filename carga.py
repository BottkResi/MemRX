
import streamlit as st
from supabase import create_client, Client
import json
import re

# Configuración
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
BUCKET_NAME = "imagenes"

# Cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Obtener casos clínicos
@st.cache_data
def obtener_casos():
    response = supabase.table("casos_clinicos").select("id, diagnostico_principal, imagenes").execute()
    return response.data if response.data else []

st.title("📤 Subir imagen y asociar a caso clínico")

# Seleccionar caso
casos = obtener_casos()
if not casos:
    st.warning("No hay casos disponibles en la base de datos.")
    st.stop()

opciones = {f"{c['id']} - {c['diagnostico_principal'] or '(Sin diagnóstico)'}": c for c in casos}
seleccion_str = st.selectbox("Selecciona un caso clínico", list(opciones.keys()))
caso = opciones[seleccion_str]
st.markdown(f"**ID del caso:** {caso['id']}")

# Subir imagen
imagen = st.file_uploader("Selecciona una imagen", type=["png", "jpg", "jpeg"])

if imagen and st.button("Subir Imagen"):
    try:
        file_bytes = imagen.getvalue()
        extension = imagen.name.split('.')[-1]
        diagnostico = caso["diagnostico_principal"] or "caso"
        diagnostico = re.sub(r"[^a-zA-Z0-9_]", "_", diagnostico)  # Reemplaza todo lo no válido

        imagenes_actuales = caso.get("imagenes")
        if isinstance(imagenes_actuales, str):
            imagenes_actuales = json.loads(imagenes_actuales)
        elif isinstance(imagenes_actuales, list):
            imagenes_actuales = imagenes_actuales
        else:
            imagenes_actuales = []

        num_imagen = len(imagenes_actuales) + 1
        nuevo_nombre = f"{diagnostico}_{num_imagen}.{extension}"
        path = f"{nuevo_nombre}"

        response = supabase.storage.from_(BUCKET_NAME).upload(
            path,
            file_bytes,
            {"content-type": imagen.type}
        )
        st.write("📦 Resultado del upload:", response)

        if hasattr(response, "error") and response.error:
            st.error(f"❌ Error al subir imagen: {response.error}")
        else:
            url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{path}"
            imagenes_actuales.append(url)

            update = supabase.table("casos_clinicos").update({
                "imagenes": imagenes_actuales
            }).eq("id", caso["id"]).execute()

            st.success("✅ Imagen subida y asociada al caso clínico")
            st.image(url, caption="Imagen subida", width=300)
            st.code(url, language="text")
            st.write("📝 Resultado de actualización en la base:", update)

    except Exception as e:
        st.error(f"⚠️ Error inesperado: {str(e)}")
