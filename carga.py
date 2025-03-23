import streamlit as st
from supabase import create_client, Client
from io import BytesIO
import json

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
BUCKET_NAME = "imagenes"

# Crear cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data
def obtener_casos():
    response = supabase.table("casos_clinicos").select("id, diagnostico_principal, imagenes").execute()
    return response.data if response.data else []

def subir_imagen(file, caso):
    try:
        st.write("🧪 tipo de 'caso':", type(caso))
        st.write("🧪 contenido de 'caso':", caso)

        if not isinstance(caso, dict):
            return "⚠️ Error: el caso recibido no es un diccionario."

        file_bytes = file.getvalue()
        extension = file.name.split('.')[-1]
        diagnostico = caso["diagnostico_principal"].replace(" ", "_") if caso["diagnostico_principal"] else "caso"

        try:
            imagenes = caso.get("imagenes")
            if isinstance(imagenes, str):
               imagenes_actuales = json.loads(imagenes)
            elif isinstance(imagenes, list):
               imagenes_actuales = imagenes
            elif imagenes is None:
               imagenes_actuales = []
            else:
               st.write("⚠️ Tipo inesperado en 'imagenes':", type(imagenes))
               return "Error: tipo no compatible en 'imagenes'"
        except Exception as e:
            st.write("⚠️ Excepción al procesar 'imagenes':", str(e))
            return "Error al interpretar el campo 'imagenes'"

        num_imagen = len(imagenes_actuales) + 1
        nuevo_nombre = f"{diagnostico}_{num_imagen}.{extension}"
        path = f"{nuevo_nombre}"

        response = supabase.storage.from_(BUCKET_NAME).upload(path, BytesIO(file_bytes), file.type)
        st.write("🔍 Resultado del upload:", response)

        if not response or hasattr(response, "error") and response.error:
            return f"❌ Error al subir imagen: {getattr(response, 'error', 'desconocido')}"

        url_imagen = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{path}"
        imagenes_actuales.append(url_imagen)

        update_result = supabase.table("casos_clinicos").update(
            {"imagenes": imagenes_actuales}
        ).eq("id", caso["id"]).execute()

        st.write("📝 Resultado de actualización del caso:", update_result)

        return url_imagen
    except Exception as e:
        return f"⚠️ Excepción: {str(e)}"

def cargar_desde_codigo(codigo):
    try:
        contexto = {"supabase": supabase}
        exec(codigo, contexto)
        if "nuevo_caso" in contexto:
            resultado = contexto["supabase"].table("casos_clinicos").insert(contexto["nuevo_caso"]).execute()
            return resultado
        else:
            return {"error": "No se encontró la variable 'nuevo_caso' en el código proporcionado."}
    except Exception as e:
        return {"error": str(e)}

st.title("🧠 Carga de Casos Clínicos")

st.subheader("📋 Casos ya cargados")
casos = obtener_casos()

if casos:
    opciones = {f"{c['id']} - {c['diagnostico_principal'] or '(Sin diagnóstico)'}": c for c in casos}
    seleccion_str = st.selectbox("Selecciona un caso", list(opciones.keys()))
    seleccion = opciones.get(seleccion_str)

    st.write(f"ID del caso seleccionado: {seleccion['id']}")
    st.write("🧪 Tipo de 'seleccion':", type(seleccion))

    st.subheader("🖼️ Imágenes ya asociadas a este caso")
    imagenes_visibles = seleccion.get("imagenes")
    if isinstance(imagenes_visibles, str):
        imagenes_visibles = json.loads(imagenes_visibles)
    if imagenes_visibles:
        for url in imagenes_visibles:
            st.image(url, width=300)
    else:
        st.info("Este caso aún no tiene imágenes asociadas.")

    st.subheader("📤 Subir imagen para caso seleccionado")
    imagen = st.file_uploader("Selecciona una imagen", type=["png", "jpg", "jpeg"])
    if imagen and st.button("Subir Imagen"):
        url_imagen = subir_imagen(imagen, seleccion)
        if url_imagen and isinstance(url_imagen, str) and url_imagen.startswith("http"):
            st.success(f"✅ Imagen subida correctamente: {url_imagen}")
        else:
            st.error(url_imagen)

else:
    st.info("No hay casos cargados todavía.")
    seleccion = None

st.subheader("🐍 Cargar caso clínico desde código Python")
codigo_caso = st.text_area("Pega aquí el bloque de código con la variable 'nuevo_caso'", height=300)
if st.button("Cargar caso desde código"):
    resultado = cargar_desde_codigo(codigo_caso)
    if "error" in resultado:
        st.error(f"❌ Error: {resultado['error']}")
    else:
        st.success("✅ Caso cargado correctamente.")
        st.json(resultado)
