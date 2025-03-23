import streamlit as st
from supabase import create_client, Client
import json
import re

# Configuración
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
BUCKET_NAME = "imagenes"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data
def obtener_casos():
    return supabase.table("casos_clinicos").select("id, diagnostico_principal, imagenes").limit(1000).execute().data

st.title("🧠 Gestión de Casos Clínicos")

# SELECCIÓN POR ID
st.subheader("🔍 Seleccionar caso por ID")
casos = obtener_casos()
id_input = st.number_input("Ingresá el ID del caso clínico:", min_value=1, step=1)
caso = next((c for c in casos if c["id"] == id_input), None)

if not caso:
    st.warning("⚠️ No se encontró ningún caso con ese ID.")
    st.stop()

st.success(f"✅ Caso seleccionado: {caso['id']} - {caso['diagnostico_principal']}")

# MOSTRAR IMÁGENES YA CARGADAS
st.subheader("🖼️ Imágenes asociadas a este caso")
imagenes = caso.get("imagenes") or []
if isinstance(imagenes, str):
    imagenes = json.loads(imagenes)

if imagenes:
    for url in imagenes:
        st.image(url, width=300)
        st.code(url, language="text")
else:
    st.info("Este caso aún no tiene imágenes asociadas.")

# SUBIR NUEVA IMAGEN
st.subheader("📤 Subir imagen nueva al caso")
imagen = st.file_uploader("Selecciona una imagen", type=["png", "jpg", "jpeg"])

if imagen and st.button("Subir Imagen"):
    try:
        file_bytes = imagen.getvalue()
        extension = imagen.name.split('.')[-1]
        diagnostico = caso["diagnostico_principal"] or "caso"
        diagnostico = re.sub(r"[^a-zA-Z0-9_]", "_", diagnostico)

        if not isinstance(imagenes, list):
            imagenes = []

        num_imagen = len(imagenes) + 1
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
            imagenes.append(url)

            update = supabase.table("casos_clinicos").update({
                "imagenes": imagenes
            }).eq("id", caso["id"]).execute()

            st.success("✅ Imagen subida y asociada al caso clínico")
            st.image(url, caption="Imagen subida", width=300)
            st.code(url, language="text")
            st.write("📝 Resultado de actualización:", update)

    except Exception as e:
        st.error(f"⚠️ Error inesperado: {str(e)}")
