import streamlit as st
from supabase import create_client, Client
from io import BytesIO

# Leer desde secrets
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
BUCKET_NAME = "imagenes"

# Mostrar URL para verificar
st.write("🔌 Conectando a Supabase...")
st.write("URL:", SUPABASE_URL)
st.write("KEY (parcial):", SUPABASE_KEY[:10] + "...")

# Crear cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Función para obtener casos
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

# Interfaz Streamlit
st.title("🧠 Carga de Casos Clínicos")

# Casos existentes
st.subheader("📋 Casos ya cargados")
casos = obtener_casos()
if casos:
    caso_seleccionado = st.selectbox("Selecciona un caso", [f"{c['id']} - {c['pregunta_principal']}" for c in casos])
else:
    st.info("No hay casos cargados todavía.")

# Carga SQL
st.subheader("📝 Cargar caso clínico vía SQL")
query = st.text_area("Pega el código SQL para insertar un nuevo caso.")
if st.button("Ejecutar SQL"):
    resultado = ejecutar_sql(query)
    st.success("Consulta ejecutada.")
    st.text(resultado)

# Subir imágenes
st.subheader("📤 Subir imagen para caso")
imagen = st.file_uploader("Selecciona una imagen", type=["png", "jpg", "jpeg"])
if imagen and st.button("Subir Imagen"):
    url_imagen = subir_imagen(imagen)
    if url_imagen:
        st.success(f"Imagen subida: {url_imagen}")
        st.text("Copiá esta URL y agregala al JSON de imágenes.")
    else:
        st.error("❌ Error al subir la imagen.")
