import streamlit as st
import supabase
import os
from supabase import create_client
from io import BytesIO

# Configurar Supabase
import os
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = "imagenes"  # Nombre del bucket en Supabase Storage
supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Función para obtener casos clínicos
@st.cache_data
def obtener_casos():
    response = supabase_client.table("casos_clinicos").select("id, pregunta_principal").execute()
    return response.data if response.data else []

# Función para subir imágenes a Supabase Storage
def subir_imagen(file):
    file_bytes = file.getvalue()
    file_name = file.name
    path = f"{file_name}"
    
    # Subir la imagen
    response = supabase_client.storage.from_(BUCKET_NAME).upload(path, BytesIO(file_bytes), file.type)
    if response:
        return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{path}"
    return None

# Función para ejecutar SQL en Supabase
def ejecutar_sql(query):
    try:
        response = supabase_client.rpc("sql", {"query": query}).execute()
        return response
    except Exception as e:
        return str(e)

# Interfaz en Streamlit
st.title("Gestión de Casos Clínicos")

# Sección: Lista de Casos Clínicos
st.subheader("Casos Clínicos Existentes")
casos = obtener_casos()
caso_seleccionado = st.selectbox("Selecciona un caso", [f"{c['id']} - {c['pregunta_principal']}" for c in casos])

# Sección: Ingreso de SQL
st.subheader("Carga de Datos en SQL")
query = st.text_area("Inserta tu código SQL aquí")
if st.button("Ejecutar SQL"):
    resultado = ejecutar_sql(query)
    st.success("Consulta ejecutada correctamente")
    st.text(resultado)

# Sección: Subida de Imágenes
st.subheader("Subir Imágenes")
imagen = st.file_uploader("Selecciona una imagen", type=["png", "jpg", "jpeg"])
if imagen and st.button("Subir Imagen"):
    url_imagen = subir_imagen(imagen)
    if url_imagen:
        st.success(f"Imagen subida con éxito: {url_imagen}")
    else:
        st.error("Error al subir la imagen")

st.write("Recuerda copiar la URL de la imagen y agregarla a la base de datos correctamente.")
