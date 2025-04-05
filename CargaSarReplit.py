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

# --- SECCIÓN: Cargar casos múltiples desde bloques 'nuevo_caso = {...}' ---
st.subheader("🐍 Cargar casos clínicos desde múltiples bloques 'nuevo_caso'")

codigo_caso = st.text_area("Pegá varios bloques con la variable 'nuevo_caso = {...}'", height=400)

if st.button("Cargar casos múltiples"):
    try:
        bloques = re.findall(r"(nuevo_caso\s*=\s*{(?:[^{}]|{[^{}]*})*})", codigo_caso, re.DOTALL)
        nuevos_casos = []
        for bloque in bloques:
            contexto = {}
            exec(bloque, contexto)
            if "nuevo_caso" in contexto:
                nuevos_casos.append(contexto["nuevo_caso"])
        
        if nuevos_casos:
            resultado = supabase.table("casos_clinicos").insert(nuevos_casos).execute()
            st.success(f"✅ {len(nuevos_casos)} casos cargados correctamente.")
            st.json(resultado)
        else:
            st.warning("⚠️ No se encontró ningún bloque 'nuevo_caso' válido.")
    except Exception as e:
        st.error(f"⚠️ Error al procesar los bloques: {str(e)}")

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
        nuevo_nombre = f"{diagnostico}_{caso['id']}_{num_imagen}.{extension}"
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

# --- SECCIÓN: Subir imágenes y asociar a casos clínicos secuenciales ---
st.subheader("📥 Subir imágenes y asociar a casos clínicos secuenciales")

id_inicio = st.number_input("Ingresá el ID del primer caso clínico:", min_value=1, step=1, key="multi_id_input")
imagenes = st.file_uploader("Selecciona múltiples imágenes", accept_multiple_files=True, type=["png", "jpg", "jpeg"], key="multi_image_upload")

# Vista preliminar
if imagenes:
    st.markdown("### 👀 Vista previa de asignación:")
    preview_data = []
    casos_dict = {c["id"]: c for c in casos}
    for i, img in enumerate(imagenes):
        id_actual = id_inicio + i
        caso = casos_dict.get(id_actual)
        if caso:
            preview_data.append({
                "ID": id_actual,
                "Diagnóstico": caso["diagnostico_principal"],
                "Nombre de imagen": img.name
            })
        else:
            preview_data.append({
                "ID": id_actual,
                "Diagnóstico": "❌ No encontrado",
                "Nombre de imagen": img.name
            })
    st.dataframe(preview_data)

# Botón para confirmar subida
if imagenes and st.button("Subir imágenes secuenciales"):
    errores = []
    for i, imagen in enumerate(imagenes):
        id_actual = id_inicio + i
        caso = casos_dict.get(id_actual)
        if not caso:
            errores.append(f"ID {id_actual} no encontrado.")
            continue

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
            nuevo_nombre = f"{diagnostico}_{id_actual}_{num_imagen}.{extension}"
            path = f"{nuevo_nombre}"

            response = supabase.storage.from_(BUCKET_NAME).upload(
                path,
                file_bytes,
                {"content-type": imagen.type}
            )

            if hasattr(response, "error") and response.error:
                errores.append(f"Error al subir imagen para ID {id_actual}: {response.error}")
                continue

            url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{path}"
            imagenes_actuales.append(url)

            update = supabase.table("casos_clinicos").update({
                "imagenes": imagenes_actuales
            }).eq("id", id_actual).execute()
        except Exception as e:
            errores.append(f"ID {id_actual}: {str(e)}")

    if errores:
        st.warning("⚠️ Algunos errores durante la subida:")
        for e in errores:
            st.text(f"- {e}")
    else:
        st.success("✅ Todas las imágenes fueron subidas correctamente.")
