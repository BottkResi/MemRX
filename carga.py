import streamlit as st
import supabase
import os
import json
from supabase import create_client
from io import BytesIO

# Configurar Supabase
SUPABASE_URL = "TU_SUPABASE_URL"
SUPABASE_KEY = "TU_SUPABASE_KEY"
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

# Función para insertar un caso clínico en Supabase
def insertar_caso(datos):
    try:
        response = supabase_client.table("casos_clinicos").insert(datos).execute()
        return response
    except Exception as e:
        return str(e)

# Interfaz en Streamlit
st.title("Gestión de Casos Clínicos")

# Sección: Lista de Casos Clínicos
st.subheader("Casos Clínicos Existentes")
casos = obtener_casos()
caso_seleccionado = st.selectbox("Selecciona un caso", [f"{c['id']} - {c['pregunta_principal']}" for c in casos])

# Sección: Ingreso de Datos
st.subheader("Carga de Datos del Caso Clínico")

diagnostico_principal = st.text_input("Diagnóstico Principal")
diferenciales = st.text_area("Diagnósticos Diferenciales (separados por coma)")
pregunta_principal = st.text_input("Pregunta Principal")
opciones = st.text_area("Opciones (separadas por coma)")
respuesta_correcta = st.number_input("Índice de la Respuesta Correcta", min_value=0, max_value=4, step=1)
explicacion_correcta = st.text_area("Explicación Correcta")
explicaciones_diferenciales = st.text_area("Explicaciones Diferenciales (formato JSON)")
nivel_dificultad = st.selectbox("Nivel de Dificultad", ["Residente de 1° año", "Residente de 2° año", "Residente de 3° año", "Residente de 4° año", "Fellow"])
etiquetas = st.text_area("Etiquetas (separadas por coma)")
preguntas_adicionales = st.text_area("Preguntas Adicionales (formato JSON)")

# Subir imágenes y generar URL
st.subheader("Subir Imágenes")
imagen = st.file_uploader("Selecciona una imagen", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

imagenes_urls = []
if imagen:
    for img in imagen:
        url_imagen = subir_imagen(img)
        if url_imagen:
            imagenes_urls.append(url_imagen)
    st.success("Imágenes subidas con éxito")

# Botón para subir caso
if st.button("Subir Caso Clínico"):
    datos_caso = {
        "diagnostico_principal": diagnostico_principal,
        "diferenciales": json.dumps(diferenciales.split(",")),
        "pregunta_principal": pregunta_principal,
        "opciones": json.dumps(opciones.split(",")),
        "respuesta_correcta": respuesta_correcta,
        "explicacion_correcta": explicacion_correcta,
        "explicaciones_diferenciales": explicaciones_diferenciales,
        "nivel_dificultad": nivel_dificultad,
        "etiquetas": json.dumps(etiquetas.split(",")),
        "preguntas_adicionales": preguntas_adicionales,
        "imagenes": json.dumps(imagenes_urls)
    }
    resultado = insertar_caso(datos_caso)
    st.success("Caso clínico subido correctamente")
    st.text(resultado)
