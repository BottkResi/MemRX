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
    response = supabase.table("casos_clinicos").select("id, diagnostico_principal, imagenes").limit(1000).execute()
    return response.data if response.data else []
    
st.title("🧠 Carga de Casos Clínicos y Subida de Imágenes")

# --- SECCIÓN: Cargar caso desde código Python ---
st.subheader("🐍 Cargar nuevo caso clínico en formato Python")

codigo_caso = st.text_area("Pegá el bloque de código con la variable 'nuevo_caso'", height=250)

if st.button("Cargar caso desde código"):
    try:
        contexto = {"supabase": supabase}
        exec(codigo_caso, contexto)
        if "nuevo_caso" in contexto:
            resultado = supabase.table("casos_clinicos").insert(contexto["nuevo_caso"]).execute()
            st.success("✅ Caso cargado correctamente.")
            st.json(resultado)
        else:
            st.error("❌ No se encontró la variable 'nuevo_caso' en el código.")
    except Exception as e:
        st.error(f"⚠️ Error al ejecutar el código: {str(e)}")

# --- SECCIÓN: Subir imagen a un caso clínico existente ---
st.subheader("📤 Subir imagen y asociar a caso clínico")

casos = obtener_casos()
if not casos:
    st.warning("No hay casos disponibles en la base de datos.")
    st.stop()

st.markdown("### 🔍 Selección de caso por ID")
id_input = st.number_input("Ingresá el ID del caso clínico:", min_value=1, step=1)

caso = next((c for c in casos if c["id"] == id_input), None)

if caso:
    st.success(f"✅ Caso seleccionado: {caso['id']} - {caso['diagnostico_principal']}")
else:
    st.warning("⚠️ No se encontró ningún caso con ese ID.")
    st.stop()

st.markdown(f"**ID del caso seleccionado:** {caso['id']}")

# Subir imagen
imagen = st.file_uploader("Selecciona una imagen", type=["png", "jpg", "jpeg"])

if imagen and st.button("Subir Imagen"):
    try:
        file_bytes = imagen.getvalue()
        extension = imagen.name.split('.')[-1]
        diagnostico = caso["diagnostico_principal"] or "caso"
        diagnostico = re.sub(r"[^a-zA-Z0-9_]", "_", diagnostico)

        imagenes_actuales = caso.get("imagenes")
        if isinstance(imagenes_actuales, str):
            imagenes_actuales = json.loads(imagenes_actuales)
        elif not isinstance(imagenes_actuales, list):
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
