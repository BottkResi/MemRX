import streamlit as st
from supabase_py import create_client, Client
from io import BytesIO

# Variables Supabase directamente en el código (⚠️ solo para pruebas)
SUPABASE_URL = "https://qtaqyphuhqaqbclpzfvv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF0YXF5cGh1aHFhcWJjbHB6ZnZ2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI0MzExNTIsImV4cCI6MjA1ODAwNzE1Mn0.QF82UGW327uqDPSRajpp5DnVqHQXJOQh-TGDMGon3ew"
BUCKET_NAME = "imagenes"

# Debug opcional para validar URL y KEY
st.write("🔌 Conectando a Supabase...")
st.write("URL:", repr(SUPABASE_URL))
st.write("KEY (parcial):", SUPABASE_KEY[:10] + "...")

# Crear cliente Supabase
supabase: Client = create_client(SUPABASE_URL.strip(), SUPABASE_KEY.strip())

# Función para obtener casos existentes
@st.cache_data
def obtener_casos():
    response = supabase.table("casos_clinicos").select("id, pregunta_principal").execute()
    return response.data if response.data else []

# Función para subir imagen
def subir_imagen(file):
    file_bytes = file.getvalue()
    file_name = file.name
    path = f"{file_name}"
    
    response = supabase.storage.from_(BUCKET_NAME).upload(path, BytesIO(file_bytes), file.type)
    if response:
        return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{path}"
    return None

# Función para ejecutar SQL
def ejecutar_sql(query):
    try:
        response = supabase.rpc("sql", {"query": query}).execute()
        return response
    except Exception as e:
        return str(e)

# Interfaz en Streamlit
st.title("🧠 Carga de Casos Clínicos")

# Casos ya cargados
st.subheader("📋 Casos existentes")
casos = obtener_casos()
if casos:
    st.selectbox("Selecciona un caso existente:", [f"{c['id']} - {c['pregunta_principal']}" for c in casos])
else:
    st.info("No hay casos cargados aún.")

# Área para SQL
st.subheader("📥 Cargar nuevo caso en SQL")
query = st.text_area("Pega el código SQL aquí")
if st.button("Ejecutar SQL"):
    resultado = ejecutar_sql(query)
    st.success("Consulta ejecutada.")
    st.text(resultado)

# Subida de imagen
st.subheader("📤 Subir imagen para caso clínico")
imagen = st.file_uploader("Selecciona una imagen (jpg, png)", type=["jpg", "jpeg", "png"])
if imagen and st.button("Subir Imagen"):
    url_imagen = subir_imagen(imagen)
    if url_imagen:
        st.success(f"Imagen subida exitosamente: {url_imagen}")
        st.text("Copiá esta URL en el campo 'imagenes' del caso clínico.")
    else:
        st.error("Error al subir la imagen.")
