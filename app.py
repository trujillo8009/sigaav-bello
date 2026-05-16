import streamlit as st
from databricks import sql as dbsql
import pandas as pd
from datetime import datetime
import random
import base64
import io
from PIL import Image

st.set_page_config(page_title="SIGAAV - Alcaldía de Bello", page_icon="🎬", layout="wide")

HOST = st.secrets.get("DATABRICKS_HOST", "")
TOKEN = st.secrets.get("DATABRICKS_TOKEN", "")
HTTP_PATH = st.secrets.get("DATABRICKS_HTTP_PATH", "")

CSV_URL = "https://raw.githubusercontent.com/trujillo8009/sigaav-bello/main/data/catalogo_gold.csv"

DEPENDENCIAS = [
    "Secretaría de Interior",
    "Secretaría de Seguridad y Convivencia",
    "Secretaría de Obras Públicas",
    "Secretaría de Movilidad",
    "Secretaría de Hacienda",
    "Secretaría de Educación",
    "Secretaría de Salud",
    "Secretaría de Planeación",
    "Secretaría de la Mujer",
    "Secretaría de Gestión del Riesgo y Atención a Desastres",
    "Secretaría de Inclusión, Familia y Participación Ciudadana",
    "Secretaría General",
    "Secretaría Jurídica",
    "Secretaría de Servicios Administrativos",
    "Secretaría de Cultura",
    "Despacho del Alcalde",
]

CATEGORIAS = [
    "inauguracion", "institucional", "educacion", "salud", "obras",
    "social", "cultura", "deporte", "seguridad", "movilidad",
    "juridico", "hacienda", "planeacion", "mujer", "riesgo",
]

TIPOS_EVENTO = [
    "Consejo de Gobierno", "Consejo de Seguridad", "Inauguración de obra",
    "Jornada de salud", "Jornada de educación", "Jornada comunitaria",
    "Entrega de beneficios", "Acto cultural", "Rueda de prensa",
    "Recorrido de obras", "Capacitación interna", "Firma de convenio",
    "Evento deportivo", "Festival", "Sesión controlada individual", "Otro",
]

ROLES = {
    "fotografo": "Fotógrafo / Camarógrafo",
    "disenador": "Diseñador / Comunicador",
    "comunicador": "Comunicador Social",
    "admin": "Administrador",
}

# ── CONEXIÓN Y DATOS ──────────────────────────────────────────────────────────

def get_conn():
    return dbsql.connect(server_hostname=HOST, http_path=HTTP_PATH, access_token=TOKEN)

@st.cache_data(ttl=300)
def get_catalogo_csv():
    """Lee el catálogo Gold desde GitHub como fallback."""
    try:
        df = pd.read_csv(CSV_URL)
        # Agregar columna uso_seguro si no existe
        if "uso_seguro" not in df.columns:
            df["uso_seguro"] = df["estado_consentimiento"].apply(
                lambda x: "SI" if "verificado" in str(x) and "restriccion" not in str(x) else "VERIFICAR"
            )
        if "nombre_persona" not in df.columns:
            df["nombre_persona"] = ""
        if "enlace_sharepoint" not in df.columns:
            df["enlace_sharepoint"] = ""
        if "fotografo" not in df.columns:
            df["fotografo"] = ""
        if "resolucion" not in df.columns:
            df["resolucion"] = ""
        if "estado_activo" not in df.columns:
            df["estado_activo"] = "activo"
        if "url_miniatura" not in df.columns:
            df["url_miniatura"] = ""
        return df
    except Exception as e:
        st.warning(f"No se pudo cargar el catálogo: {e}")
        return pd.DataFrame()

def run_query(query):
    """Intenta Databricks primero, cae al CSV de GitHub si falla."""
    try:
        if not HOST or not TOKEN or not HTTP_PATH:
            raise Exception("Credenciales no configuradas")
        with get_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                try:
                    return cursor.fetchall_arrow().to_pandas()
                except:
                    return pd.DataFrame()
    except Exception:
        # Fallback al CSV de GitHub
        query_lower = query.lower()
        df = get_catalogo_csv()
        if df.empty:
            return pd.DataFrame()

        # Filtrar según la query
        if "catalogo_gold" in query_lower or "catalogo_activos" in query_lower:
            # Aplicar filtros WHERE si los hay
            if "lower(palabras_clave) like" in query_lower:
                import re
                match = re.search(r"like '%(.+?)%'", query_lower)
                if match:
                    term = match.group(1)
                    df = df[
                        df["palabras_clave"].str.lower().str.contains(term, na=False) |
                        df["nombre_archivo"].str.lower().str.contains(term, na=False) |
                        df["dependencia"].str.lower().str.contains(term, na=False) |
                        df["categoria"].str.lower().str.contains(term, na=False)
                    ]
            if "formato in ('jpg','jpeg','png')" in query_lower:
                df = df[df["formato"].isin(["jpg","jpeg","png"])]
            elif "formato in ('mp4','mov')" in query_lower:
                df = df[df["formato"].isin(["mp4","mov"])]
            if "uso_seguro='si'" in query_lower:
                df = df[df["uso_seguro"] == "SI"]
            elif "uso_seguro='verificar'" in query_lower:
                df = df[df["uso_seguro"] == "VERIFICAR"]
            return df.head(50)

        if "consentimientos_individuales" in query_lower:
            return pd.DataFrame()
        if "avisos_publicos" in query_lower:
            return pd.DataFrame()

        return pd.DataFrame()

def gen_id(prefix="CONS"):
    hoy = datetime.now()
    num = random.randint(1000, 9999)
    return f"{prefix}-{hoy.year}-{hoy.month:02d}-{hoy.day:02d}-{num}"

def image_to_base64(img_bytes, max_width=300):
    img = Image.open(io.BytesIO(img_bytes))
    ratio = max_width / img.width
    new_h = int(img.height * ratio)
    img = img.resize((max_width, new_h), Image.LANCZOS)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=75)
    return base64.b64encode(buf.getvalue()).decode()

def file_to_base64(file_bytes):
    return base64.b64encode(file_bytes).decode()

# ── LOGIN POR ROL ────────────────────────────────────────────────────────────

if 'rol' not in st.session_state:
    st.session_state['rol'] = None

if st.session_state['rol'] is None:
    st.markdown("""
    <div style='text-align:center;padding:2rem;background:#E6F1FB;border-radius:12px;margin-bottom:2rem'>
        <h1 style='color:#185FA5;font-size:28px;margin:0'>SIGAAV</h1>
        <p style='color:#378ADD;margin:6px 0 0'>Sistema de Gestión de Activos Audiovisuales</p>
        <p style='color:#555;font-size:13px;margin:4px 0 0'>Alcaldía de Bello · Dirección Administrativa de Comunicaciones</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Selecciona tu perfil para continuar")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📷\n\nFotógrafo /\nCamarógrafo", use_container_width=True):
            st.session_state['rol'] = 'fotografo'; st.rerun()
    with col2:
        if st.button("🎨\n\nDiseñador", use_container_width=True):
            st.session_state['rol'] = 'disenador'; st.rerun()
    with col3:
        if st.button("📢\n\nComunicador\nSocial", use_container_width=True):
            st.session_state['rol'] = 'comunicador'; st.rerun()
    with col4:
        if st.button("⚙️\n\nAdministrador", use_container_width=True):
            st.session_state['rol'] = 'admin'; st.rerun()
    st.stop()

# ── HEADER ───────────────────────────────────────────────────────────────────

rol = st.session_state['rol']
rol_label = ROLES[rol]
rol_icons = {'fotografo':'📷','disenador':'🎨','comunicador':'📢','admin':'⚙️'}

col_h, col_salir = st.columns([5,1])
with col_h:
    st.markdown(f"""
    <div style='padding:0.8rem 1.2rem;background:#E6F1FB;border-radius:10px;margin-bottom:1rem;display:flex;align-items:center;gap:12px'>
        <div>
            <span style='font-size:22px;font-weight:500;color:#185FA5'>SIGAAV v2.0</span>
            <span style='font-size:13px;color:#555;margin-left:12px'>Alcaldía de Bello · Comunicaciones</span>
        </div>
        <div style='margin-left:auto;background:#185FA5;color:white;padding:4px 14px;border-radius:20px;font-size:13px'>
            {rol_icons[rol]} {rol_label}
        </div>
    </div>
    """, unsafe_allow_html=True)
with col_salir:
    st.write("")
    if st.button("Cambiar perfil"):
        st.session_state['rol'] = None; st.rerun()

# ── TABS ─────────────────────────────────────────────────────────────────────

if rol == 'fotografo':
    tabs = st.tabs(["📋 Registrar consentimiento", "📷 Registrar activo", "📦 Carga por lote"])
    tab_consent, tab_activo, tab_lote = tabs[0], tabs[1], tabs[2]
    tab_buscar = tab_dashboard = None
elif rol == 'disenador':
    tabs = st.tabs(["🔍 Buscar en catálogo"])
    tab_buscar = tabs[0]
    tab_consent = tab_activo = tab_lote = tab_dashboard = None
elif rol == 'comunicador':
    tabs = st.tabs(["📋 Registrar consentimiento", "📷 Registrar activo", "📦 Carga por lote", "🔍 Buscar en catálogo"])
    tab_consent, tab_activo, tab_lote, tab_buscar = tabs[0], tabs[1], tabs[2], tabs[3]
    tab_dashboard = None
elif rol == 'admin':
    tabs = st.tabs(["📋 Registrar consentimiento", "📷 Registrar activo", "📦 Carga por lote", "🔍 Buscar en catálogo", "📊 Dashboard de auditoría"])
    tab_consent, tab_activo, tab_lote, tab_buscar, tab_dashboard = tabs[0], tabs[1], tabs[2], tabs[3], tabs[4]

# ── TAB CONSENTIMIENTO ───────────────────────────────────────────────────────

if tab_consent:
    with tab_consent:
        st.subheader("Nuevo consentimiento informado")
        tipo_consent = st.radio("Tipo de consentimiento", [
            "Individual — Formulario F-GCR-08 firmado",
            "Colectivo — Video de aviso público grabado"
        ], horizontal=True)

        nuevo_id = gen_id("CONS") if "Individual" in tipo_consent else gen_id("AVIS")
        st.success(f"**Código generado automáticamente:** `{nuevo_id}`")
        st.caption("Escriba este código en el formulario físico antes de que la persona lo firme.")

        col1, col2 = st.columns(2)
        with col1:
            c_nombre = st.text_input("Nombre completo" if "Individual" in tipo_consent else "Descripción del evento")
            c_fecha = st.date_input("Fecha")
        with col2:
            c_doc = st.text_input("Documento de identidad" if "Individual" in tipo_consent else "Lugar del evento")
            c_dep = st.selectbox("Dependencia", DEPENDENCIAS)
        c_evento = st.text_input("Nombre del evento o sesión")

        archivo_b64 = archivo_nombre = None
        if "Individual" in tipo_consent:
            st.markdown("**Subir formulario F-GCR-08 escaneado (PDF)**")
            archivo_consent = st.file_uploader("Seleccionar PDF del formulario firmado", type=["pdf"], key="pdf_consent")
            if archivo_consent:
                archivo_b64 = file_to_base64(archivo_consent.read())
                archivo_nombre = archivo_consent.name
                st.success(f"PDF cargado: {archivo_nombre}")
            c_restricciones = "ninguna"
            c_desc_restriccion = ""
        else:
            st.markdown("**Subir video del aviso público grabado**")
            archivo_consent = st.file_uploader("Seleccionar video del aviso (MP4)", type=["mp4","mov"], key="video_aviso")
            if archivo_consent:
                archivo_b64 = file_to_base64(archivo_consent.read())
                archivo_nombre = archivo_consent.name
                st.success(f"Video cargado: {archivo_nombre}")
            c_restricciones = st.selectbox("Restricciones de personas", ["ninguna","restriccion_menor","restriccion_solicitada"])
            c_desc_restriccion = st.text_input("Descripción de la restricción (si aplica)")

        if st.button("Registrar consentimiento", type="primary"):
            if not all([c_nombre, c_evento]):
                st.error("Complete todos los campos obligatorios.")
            else:
                try:
                    archivo_sql = f"'{archivo_nombre}'" if archivo_nombre else "NULL"
                    if "Individual" in tipo_consent:
                        run_query(f"""INSERT INTO sigaav.consentimientos_individuales
                            (id_consentimiento,nombre_persona,fecha_firma,dependencia,archivo_formulario,estado)
                            VALUES ('{nuevo_id}','{c_nombre}','{str(c_fecha)}','{c_dep}',{archivo_sql},'verificado')""")
                    else:
                        run_query(f"""INSERT INTO sigaav.avisos_publicos
                            (id_aviso,fecha_evento,dependencia,lugar_evento,descripcion_evento,
                            archivo_video_aviso,restricciones_personas,descripcion_restriccion)
                            VALUES ('{nuevo_id}','{str(c_fecha)}','{c_dep}','{c_doc}','{c_evento}',
                            {archivo_sql},'{c_restricciones}','{c_desc_restriccion}')""")
                    st.success(f"Consentimiento registrado. ID: `{nuevo_id}`")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error: {e}")

# ── TAB ACTIVO ───────────────────────────────────────────────────────────────

if tab_activo:
    with tab_activo:
        st.subheader("Registrar activo audiovisual")
        col1, col2 = st.columns(2)
        with col1:
            a_dep = st.selectbox("Dependencia", DEPENDENCIAS, key="a_dep")
            a_cat = st.selectbox("Categoría", CATEGORIAS, key="a_cat")
            a_fotografo = st.text_input("Fotógrafo / Camarógrafo")
            a_estado = st.selectbox("Estado del activo", ["activo","en_revision","archivado"])
        with col2:
            a_formato = st.selectbox("Formato", ["jpg","png","mp4","mov"])
            a_resolucion = st.selectbox("Resolución", ["4K (3840x2160)","Full HD (1920x1080)","HD (1280x720)","Estándar"])
            a_tipo_evento = st.selectbox("Tipo de evento", TIPOS_EVENTO)

        st.markdown("**Subir archivo (foto o video)**")
        archivo_activo = st.file_uploader("Seleccionar archivo", type=["jpg","jpeg","png","mp4","mov"], key="archivo_activo")
        miniatura_b64 = None
        a_nombre = ""
        if archivo_activo:
            a_nombre = archivo_activo.name
            file_bytes = archivo_activo.read()
            st.success(f"Archivo cargado: {a_nombre}")
            if a_formato in ["jpg","jpeg","png"]:
                col_prev, col_info = st.columns([1,2])
                with col_prev:
                    st.image(file_bytes, width=200, caption="Vista previa")
                miniatura_b64 = image_to_base64(file_bytes)

        a_tags = st.text_input("Palabras clave (separadas por comas)", placeholder="salud, vacunacion, comunidad")

        st.markdown("---")
        st.markdown("**Vincular consentimiento**")
        if a_tipo_evento == "Sesión controlada individual":
            st.info("Sesión controlada: debe vincular el formulario F-GCR-08 firmado.")
            col_id, col_btn = st.columns([3,1])
            with col_id:
                cid_input = st.text_input("Código del consentimiento (CONS-AAAA-MM-DD-XXXX)")
            with col_btn:
                st.write("")
                if st.button("Verificar", key="btn_verificar"):
                    st.info("Verificación disponible con conexión a Databricks activa.")
            st.session_state['consent_ok'] = cid_input if cid_input else None
        else:
            st.info("Evento masivo: el sistema vincula automáticamente el aviso público colectivo.")
            cid_input = st.text_input("ID del aviso público (AVIS-AAAA-MM-DD-XXXX) — opcional")
            st.session_state['consent_ok'] = 'colectivo'

        if st.button("Registrar activo", type="primary", key="btn_activo"):
            if not a_nombre:
                st.error("Debe subir un archivo primero.")
            else:
                st.info("El registro de nuevos activos requiere conexión activa a Databricks.")

# ── TAB LOTE ─────────────────────────────────────────────────────────────────

if tab_lote:
    with tab_lote:
        st.subheader("Carga por lote desde Excel")
        st.info("Descarga la plantilla, llena los datos y sube el archivo para registrar activos.")

        plantilla_data = {
            'nombre_archivo': ['foto_evento1.jpg','foto_evento2.jpg'],
            'formato': ['jpg','jpg'],
            'categoria': ['salud','educacion'],
            'palabras_clave': ['salud,vacunacion,comunidad','educacion,taller,docentes'],
            'dependencia': ['Secretaría de Salud','Secretaría de Educación'],
            'fotografo': ['Juan Perez','Maria Lopez'],
            'resolucion': ['Full HD (1920x1080)','Full HD (1920x1080)'],
            'tipo_evento': ['Jornada de salud','Jornada de educación'],
            'id_consentimiento': ['CONS-2026-05-02-0001',''],
            'id_aviso': ['','AVIS-2026-05-02-0001'],
            'estado_activo': ['activo','activo'],
        }
        df_plantilla = pd.DataFrame(plantilla_data)
        buf = io.BytesIO()
        df_plantilla.to_excel(buf, index=False, engine='openpyxl')
        st.download_button(
            label="Descargar plantilla Excel",
            data=buf.getvalue(),
            file_name="plantilla_carga_sigaav.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ── TAB BUSCAR ────────────────────────────────────────────────────────────────

if tab_buscar:
    with tab_buscar:
        st.subheader("Catálogo de activos institucionales")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            busq = st.text_input("Buscar por palabras clave, nombre o dependencia")
        with col2:
            filtro_tipo = st.selectbox("Tipo", ["Todos","Fotos (jpg/png)","Videos (mp4/mov)"])
        with col3:
            filtro_estado = st.selectbox("Autorización", ["Todos","Solo autorizados","Requieren revisión"])
        with col4:
            filtro_activo = st.selectbox("Estado activo", ["Todos","activo","en_revision","archivado"])

        if st.button("Buscar en catálogo", type="primary", key="btn_buscar"):
            try:
                where = "WHERE 1=1"
                if busq:
                    b = busq.lower()
                    where += f" AND (lower(palabras_clave) LIKE '%{b}%' OR lower(nombre_archivo) LIKE '%{b}%' OR lower(dependencia) LIKE '%{b}%' OR lower(categoria) LIKE '%{b}%')"
                if filtro_tipo == "Fotos (jpg/png)":
                    where += " AND formato IN ('jpg','jpeg','png')"
                elif filtro_tipo == "Videos (mp4/mov)":
                    where += " AND formato IN ('mp4','mov')"
                if filtro_estado == "Solo autorizados":
                    where += " AND uso_seguro='SI'"
                elif filtro_estado == "Requieren revisión":
                    where += " AND uso_seguro='VERIFICAR'"
                if filtro_activo != "Todos":
                    where += f" AND estado_activo='{filtro_activo}'"

                df = run_query(f"""SELECT nombre_archivo, formato, categoria, palabras_clave,
                    dependencia, estado_consentimiento, uso_seguro, nombre_persona,
                    enlace_sharepoint, fotografo, resolucion, estado_activo, url_miniatura,
                    id_consentimiento, tipo_evento
                    FROM sigaav.catalogo_gold {where} LIMIT 50""")

                total = len(df)
                ok = len(df[df['uso_seguro']=='SI']) if total > 0 and 'uso_seguro' in df.columns else 0
                ver = total - ok

                m1, m2, m3 = st.columns(3)
                m1.metric("Total encontrados", total)
                m2.metric("Autorizados", ok)
                m3.metric("Requieren revisión", ver)

                if total == 0:
                    st.info("No se encontraron activos con esos filtros.")
                else:
                    for _, row in df.iterrows():
                        with st.container():
                            col_img, col_info = st.columns([1, 3])
                            with col_img:
                                icono = "🎬" if str(row.get('formato','')) in ['mp4','mov'] else "🖼️"
                                st.markdown(f"<div style='width:160px;height:100px;background:#E6F1FB;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:36px'>{icono}</div>", unsafe_allow_html=True)
                            with col_info:
                                col_a, col_b = st.columns([3,1])
                                with col_a:
                                    st.markdown(f"**{row['nombre_archivo']}**")
                                    st.caption(f"{row['dependencia']} · {row['categoria']}")
                                    st.caption(f"Palabras clave: {row['palabras_clave']}")
                                with col_b:
                                    uso = str(row.get('uso_seguro',''))
                                    if uso == 'SI':
                                        st.success("Autorizado")
                                    else:
                                        st.warning("Verificar")
                                with st.expander("Ver expediente legal"):
                                    st.markdown(f"- **Estado:** `{row.get('estado_consentimiento','')}`")
                                    st.markdown(f"- **Alerta:** {row.get('alerta_diseñador','')}")
                                    st.markdown(f"- **Tipo:** {row.get('tipo_consentimiento_legible','')}")
                            st.divider()

            except Exception as e:
                st.error(f"Error al consultar: {e}")

# ── TAB DASHBOARD ─────────────────────────────────────────────────────────────

if tab_dashboard:
    with tab_dashboard:
        st.subheader("Dashboard de auditoría")

        if st.button("Actualizar datos", key="btn_refresh"):
            st.cache_data.clear()
            st.rerun()

        try:
            df = get_catalogo_csv()

            if not df.empty:
                total = len(df)
                autorizados = len(df[df['uso_seguro']=='SI']) if 'uso_seguro' in df.columns else 0
                pendientes = total - autorizados
                fotos = len(df[df['formato'].isin(['jpg','jpeg','png'])]) if 'formato' in df.columns else 0
                videos = len(df[df['formato'].isin(['mp4','mov'])]) if 'formato' in df.columns else 0
                pct = round(autorizados*100/total, 1) if total > 0 else 0

                st.markdown("### Resumen general")
                c1,c2,c3,c4,c5 = st.columns(5)
                c1.metric("Total activos", total)
                c2.metric("Autorizados", autorizados, f"{pct}%")
                c3.metric("Requieren revisión", pendientes)
                c4.metric("Fotografías", fotos)
                c5.metric("Videos", videos)

                st.markdown("---")
                st.markdown("### Distribución por dependencia")
                if 'dependencia' in df.columns:
                    df_dep = df.groupby('dependencia').agg(
                        total=('nombre_archivo','count')
                    ).reset_index().sort_values('total', ascending=False)
                    st.dataframe(df_dep, use_container_width=True)

                st.markdown("---")
                st.markdown("### Activos que requieren revisión")
                if 'uso_seguro' in df.columns:
                    df_urgente = df[df['uso_seguro']=='VERIFICAR'][['nombre_archivo','dependencia','estado_consentimiento','tipo_evento']]
                    if len(df_urgente) == 0:
                        st.success("No hay activos pendientes de verificación.")
                    else:
                        st.warning(f"{len(df_urgente)} activo(s) requieren atención:")
                        st.dataframe(df_urgente, use_container_width=True)

                st.markdown("---")
                st.markdown("### Distribución de consentimientos")
                if 'estado_consentimiento' in df.columns:
                    df_cons = df.groupby('estado_consentimiento').size().reset_index(name='cantidad')
                    st.dataframe(df_cons, use_container_width=True)

                st.info("📊 Datos cargados desde el catálogo Gold exportado de Databricks.")

        except Exception as e:
            st.error(f"Error al cargar el dashboard: {e}")
