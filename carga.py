
import streamlit as st
from supabase import create_client, Client
from io import BytesIO

# Configuración de Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
BUCKET_NAME = "imagenes"

# Crear cliente
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Interfaz
st.title("📤 Subir una imagen a Supabase Storage")

# Cargar imagen
imagen = st.file_uploader("Selecciona una imagen", type=["png", "jpg", "jpeg"])

# Subir imagen
if imagen and st.button("Subir Imagen"):
    try:
        file_bytes = imagen.getvalue()
        extension = imagen.name.split('.')[-1]
        nuevo_nombre = f"imagen_test.{extension}"
        path = f"{nuevo_nombre}"

        response = supabase.storage.from_(BUCKET_NAME).upload(
          path,
          BytesIO(file_bytes),
          {"content-type": imagen.type}  # ✅ Pasamos un dict, no un str
        )
        st.write("📦 Resultado del upload:", response)

        if hasattr(response, "error") and response.error:
            st.error(f"❌ Error al subir imagen: {response.error}")
        else:
            url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{path}"
            st.success("✅ Imagen subida correctamente")
            st.image(url, caption="Imagen subida", width=300)
            st.code(url, language="text")

    except Exception as e:
        st.error(f"⚠️ Error inesperado: {str(e)}")
