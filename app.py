import streamlit as st
from databricks import sql as dbsql
import pandas as pd
from datetime import datetime
import random
import base64
import io
from PIL import Image

st.set_page_config(page_title="SIGAAV - Alcaldía de Bello", page_icon="🎬", layout="wide")

HOST = st.secrets["DATABRICKS_HOST"]
TOKEN = st.secrets["DATABRICKS_TOKEN"]
HTTP_PATH = st.secrets["DATABRICKS_HTTP_PATH"]

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
    "inauguracion",
    "institucional",
    "educacion",
    "salud",
    "obras",
    "social",
    "cultura",
    "deporte",
    "seguridad",
    "movilidad",
    "juridico",
    "hacienda",
    "planeacion",
    "mujer",
    "riesgo",
]

TIPOS_EVENTO = [
    "Consejo de Gobierno",
    "Consejo de Seguridad",
    "Inauguración de obra",
    "Jornada de salud",
    "Jornada de educación",
    "Jornada comunitaria",
    "Entrega de beneficios",
    "Acto cultural",
    "Rueda de prensa",
    "Recorrido de obras",
    "Capacitación interna",
    "Firma de convenio",
    "Evento deportivo",
    "Festival",
    "Sesión controlada individual",
    "Otro",
]

ROLES = {
    "fotografo": "Fotógrafo / Camarógrafo",
    "disenador": "Diseñador / Comunicador",
    "comunicador": "Comunicador Social",
    "admin": "Administrador",
}

def get_conn():
    return dbsql.connect(server_hostname=HOST, http_path=HTTP_PATH, access_token=TOKEN)

def run_query(query):
    with get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            try:
                return cursor.fetchall_arrow().to_pandas()
            except:
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
            st.session_state['rol'] = 'fotografo'
            st.rerun()
    with col2:
        if st.button("🎨\n\nDiseñador", use_container_width=True):
            st.session_state['rol'] = 'disenador'
            st.rerun()
    with col3:
        if st.button("📢\n\nComunicador\nSocial", use_container_width=True):
            st.session_state['rol'] = 'comunicador'
            st.rerun()
    with col4:
        if st.button("⚙️\n\nAdministrador", use_container_width=True):
            st.session_state['rol'] = 'admin'
            st.rerun()
    st.stop()

# ── HEADER CON ROL ACTIVO ────────────────────────────────────────────────────
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
        st.session_state['rol'] = None
        st.rerun()

# ── TABS SEGÚN ROL ───────────────────────────────────────────────────────────
if rol == 'fotografo':
    tabs = st.tabs(["📋 Registrar consentimiento", "📷 Registrar activo", "📦 Carga por lote"])
    tab_consent, tab_activo, tab_lote = tabs[0], tabs[1], tabs[2]
    tab_buscar = None
    tab_dashboard = None

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
        archivo_b64 = None
        archivo_nombre = None

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
            tipo_val = "sesion_controlada" if a_tipo_evento == "Sesión controlada individual" else "evento_masivo"

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
                with col_info:
                    st.info("La miniatura se genera automáticamente al registrar.")
                miniatura_b64 = image_to_base64(file_bytes)

        a_tags = st.text_input("Palabras clave (separadas por comas)", placeholder="salud, vacunacion, comunidad")
        st.caption("Próximamente: palabras clave generadas automáticamente por IA.")

        # VINCULACIÓN DE CONSENTIMIENTO
        st.markdown("---")
        st.markdown("**Vincular consentimiento**")

        if a_tipo_evento == "Sesión controlada individual":
            st.info("Sesión controlada: debe vincular el formulario F-GCR-08 firmado por la persona.")
            col_id, col_btn = st.columns([3,1])
            with col_id:
                cid_input = st.text_input("Código del consentimiento (CONS-AAAA-MM-DD-XXXX)")
            with col_btn:
                st.write("")
                if st.button("Verificar", key="btn_verificar"):
                    try:
                        df_v = run_query(f"""SELECT c.nombre_persona, c.dependencia,
                            c.archivo_formulario,
                            COUNT(a.id_activo) as fotos_vinculadas
                            FROM sigaav.consentimientos_individuales c
                            LEFT JOIN sigaav.activos_audiovisuales a ON a.id_consentimiento=c.id_consentimiento
                            WHERE c.id_consentimiento='{cid_input}' AND c.estado='verificado'
                            GROUP BY c.nombre_persona, c.dependencia, c.archivo_formulario""")
                        if len(df_v) > 0:
                            persona = df_v.iloc[0]['nombre_persona']
                            dep_c = df_v.iloc[0]['dependencia']
                            fotos = df_v.iloc[0]['fotos_vinculadas']
                            st.success(f"Verificado: **{persona}** ({dep_c})")
                            st.info(f"Este consentimiento ya tiene **{fotos} activo(s)** vinculado(s). Se puede vincular uno más.")
                            st.session_state['consent_ok'] = cid_input
                            st.session_state['consent_persona'] = persona
                        else:
                            st.error("No se encontró ese consentimiento verificado.")
                            st.session_state['consent_ok'] = None
                    except Exception as e:
                        st.error(f"Error: {e}")
        else:
            st.info("Evento masivo: el sistema vincula automáticamente el aviso público colectivo.")
            cid_input = st.text_input("ID del aviso público (AVIS-AAAA-MM-DD-XXXX) — opcional")
            st.session_state['consent_ok'] = 'colectivo'

        if st.button("Registrar activo", type="primary", key="btn_activo"):
            if not a_nombre:
                st.error("Debe subir un archivo primero.")
            elif a_tipo_evento == "Sesión controlada individual" and not st.session_state.get('consent_ok'):
                st.error("Debe verificar el consentimiento individual antes de registrar.")
            else:
                try:
                    hoy = datetime.now()
                    ubicacion = f"{a_dep.replace(' ','-')}/{hoy.year}/{a_nombre}"
                    if a_tipo_evento == "Sesión controlada individual":
                        cid = f"'{st.session_state.get('consent_ok')}'"
                        tipo_db = "sesion_controlada"
                    else:
                        cid = f"'{cid_input}'" if cid_input else "NULL"
                        tipo_db = "evento_masivo"
                    act_id = f"ACT-{int(datetime.now().timestamp())}"
                    min_sql = f"'data:image/jpeg;base64,{miniatura_b64}'" if miniatura_b64 else "NULL"
                    fot_sql = f"'{a_fotografo}'" if a_fotografo else "NULL"
                    run_query(f"""INSERT INTO sigaav.activos_audiovisuales
                        (id_activo,nombre_archivo,formato,tamano_mb,fecha_creacion,ubicacion_origen,
                         categoria,palabras_clave,dependencia,anio,id_consentimiento,tipo_evento,
                         estado_activo,resolucion,fotografo,url_miniatura)
                        VALUES ('{act_id}','{a_nombre}','{a_formato}',0,'{str(hoy.date())}',
                        '{ubicacion}','{a_cat}','{a_tags}','{a_dep}',{hoy.year},{cid},'{tipo_db}',
                        '{a_estado}','{a_resolucion}',{fot_sql},{min_sql})""")
                    persona = st.session_state.get('consent_persona','')
                    msg = f"Activo registrado. ID: `{act_id}`"
                    if persona:
                        msg += f" — Vinculado a: {persona}"
                    st.success(msg)
                    st.session_state.pop('consent_ok', None)
                    st.session_state.pop('consent_persona', None)
                    st.balloons()
                except Exception as e:
                    st.error(f"Error: {e}")

# ── TAB LOTE ─────────────────────────────────────────────────────────────────
if tab_lote:
    with tab_lote:
        st.subheader("Carga por lote desde Excel")
        st.info("Descarga la plantilla, llena los datos y sube el archivo para registrar todos los activos de una vez.")

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

        st.markdown("---")
        archivo_lote = st.file_uploader("Subir Excel con activos", type=["xlsx"], key="lote")

        if archivo_lote:
            df_lote = pd.read_excel(archivo_lote)
            st.markdown(f"**{len(df_lote)} activos encontrados:**")
            st.dataframe(df_lote, use_container_width=True)

            errores = []
            for _, row in df_lote.iterrows():
                tipo_ev = str(row.get('tipo_evento',''))
                es_individual = tipo_ev == "Sesión controlada individual"
                if not row.get('nombre_archivo'):
                    errores.append("Fila sin nombre de archivo")
                if es_individual and not row.get('id_consentimiento'):
                    errores.append(f"{row.get('nombre_archivo','?')}: falta id_consentimiento")
                if tipo_ev not in TIPOS_EVENTO:
                    errores.append(f"{row.get('nombre_archivo','?')}: tipo de evento '{tipo_ev}' no válido")
            if errores:
                st.warning("Advertencias:\n" + "\n".join(errores))

            if st.button("Registrar todos los activos", type="primary", key="btn_lote"):
                progress = st.progress(0)
                ok_count = 0
                err_count = 0
                for i, row in df_lote.iterrows():
                    try:
                        hoy = datetime.now()
                        nombre = str(row['nombre_archivo'])
                        dep = str(row['dependencia'])
                        ubicacion = f"{dep.replace(' ','-')}/{hoy.year}/{nombre}"
                        tipo_ev = str(row.get('tipo_evento','evento_masivo'))
                        es_individual = tipo_ev == "Sesión controlada individual"
                        tipo_db = "sesion_controlada" if es_individual else "evento_masivo"
                        cid_val = str(row.get('id_consentimiento',''))
                        cid = f"'{cid_val}'" if cid_val and cid_val != 'nan' and es_individual else "NULL"
                        act_id = f"ACT-{int(datetime.now().timestamp())}-{i}"
                        fot_val = str(row.get('fotografo',''))
                        fot = f"'{fot_val}'" if fot_val and fot_val != 'nan' else "NULL"
                        tags = str(row.get('palabras_clave',''))
                        cat = str(row.get('categoria','institucional'))
                        fmt = str(row.get('formato','jpg'))
                        res = str(row.get('resolucion',''))
                        est = str(row.get('estado_activo','activo'))
                        run_query(f"""INSERT INTO sigaav.activos_audiovisuales
                            (id_activo,nombre_archivo,formato,tamano_mb,fecha_creacion,ubicacion_origen,
                             categoria,palabras_clave,dependencia,anio,id_consentimiento,tipo_evento,
                             estado_activo,resolucion,fotografo,url_miniatura)
                            VALUES ('{act_id}','{nombre}','{fmt}',0,'{str(hoy.date())}',
                            '{ubicacion}','{cat}','{tags}','{dep}',{hoy.year},{cid},'{tipo_db}',
                            '{est}','{res}',{fot},NULL)""")
                        ok_count += 1
                    except Exception as e:
                        err_count += 1
                    progress.progress((i+1)/len(df_lote))
                if ok_count > 0:
                    st.success(f"Carga completada: {ok_count} activos registrados.")
                    st.balloons()
                if err_count > 0:
                    st.warning(f"{err_count} activos con errores.")

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
                ok = len(df[df['uso_seguro']=='SI']) if total > 0 else 0
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
                                mini = str(row.get('url_miniatura',''))
                                if mini and mini not in ['NULL','None','nan','']:
                                    try:
                                        st.image(mini, width=160)
                                    except:
                                        icono = "🎬" if row['formato'] in ['mp4','mov'] else "🖼️"
                                        st.markdown(f"<div style='width:160px;height:100px;background:#E6F1FB;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:36px'>{icono}</div>", unsafe_allow_html=True)
                                else:
                                    icono = "🎬" if row['formato'] in ['mp4','mov'] else "🖼️"
                                    st.markdown(f"<div style='width:160px;height:100px;background:#E6F1FB;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:36px'>{icono}</div>", unsafe_allow_html=True)

                            with col_info:
                                col_a, col_b = st.columns([3,1])
                                with col_a:
                                    st.markdown(f"**{row['nombre_archivo']}**")
                                    st.caption(f"{row['dependencia']} · {row['categoria']}")
                                    st.caption(f"Palabras clave: {row['palabras_clave']}")
                                    if str(row.get('fotografo','')) not in ['None','NULL','nan','']:
                                        st.caption(f"Fotógrafo: {row['fotografo']}")
                                    if str(row.get('resolucion','')) not in ['None','NULL','nan','']:
                                        st.caption(f"Resolución: {row['resolucion']}")
                                    est_act = str(row.get('estado_activo','activo'))
                                    color = "#EAF3DE" if est_act=='activo' else "#FAEEDA" if est_act=='en_revision' else "#F5F5F5"
                                    st.markdown(f"<span style='background:{color};padding:2px 10px;border-radius:10px;font-size:12px'>{est_act}</span>", unsafe_allow_html=True)
                                with col_b:
                                    if row['uso_seguro'] == 'SI':
                                        st.success("Autorizado")
                                    else:
                                        st.warning("Verificar")
                                    enlace = str(row.get('enlace_sharepoint',''))
                                    if enlace and enlace not in ['None','NULL','nan']:
                                        st.link_button("Abrir archivo", enlace)

                                with st.expander("Ver expediente legal"):
                                    tipo_ev = str(row.get('tipo_evento',''))
                                    if tipo_ev == 'sesion_controlada':
                                        st.markdown("- **Tipo:** Consentimiento individual (F-GCR-08)")
                                        persona = str(row.get('nombre_persona',''))
                                        st.markdown(f"- **Persona:** {persona if persona not in ['None','nan'] else 'No registrado'}")
                                        st.markdown(f"- **Código:** `{row.get('id_consentimiento','')}`")
                                        st.markdown(f"- **Estado:** {'✅ Verificado' if row['uso_seguro']=='SI' else '⚠️ Pendiente'}")
                                        try:
                                            cid_r = str(row.get('id_consentimiento',''))
                                            if cid_r and cid_r not in ['None','nan']:
                                                df_doc = run_query(f"""SELECT archivo_formulario,
                                                    COUNT(*) OVER() as total_activos_vinculados
                                                    FROM sigaav.consentimientos_individuales
                                                    WHERE id_consentimiento='{cid_r}'""")
                                                if len(df_doc) > 0:
                                                    arch = str(df_doc.iloc[0]['archivo_formulario'])
                                                    if arch not in ['None','nan','NULL']:
                                                        st.markdown(f"- **Formulario PDF:** {arch}")
                                                df_count = run_query(f"""SELECT COUNT(*) as total
                                                    FROM sigaav.activos_audiovisuales
                                                    WHERE id_consentimiento='{cid_r}'""")
                                                if len(df_count) > 0:
                                                    total_v = df_count.iloc[0]['total']
                                                    st.markdown(f"- **Activos con este consentimiento:** {total_v}")
                                        except:
                                            pass
                                    else:
                                        st.markdown("- **Tipo:** Consentimiento colectivo (aviso público grabado)")
                                        est_c = str(row.get('estado_consentimiento',''))
                                        if 'restriccion' in est_c:
                                            st.markdown("- **Estado:** ⚠️ Verificado con restricciones — revisar antes de usar")
                                        else:
                                            st.markdown("- **Estado:** ✅ Aviso público sin restricciones")
                                    st.markdown(f"- **Estado legal:** `{row.get('estado_consentimiento','')}`")

                            st.divider()
            except Exception as e:
                st.error(f"Error al consultar: {e}")

# ── TAB DASHBOARD ─────────────────────────────────────────────────────────────
if tab_dashboard:
    with tab_dashboard:
        st.subheader("Dashboard de auditoría")

        if st.button("Actualizar datos", key="btn_refresh"):
            st.rerun()

        try:
            # Métricas generales
            df_gen = run_query("""SELECT
                COUNT(*) as total,
                SUM(CASE WHEN uso_seguro='SI' THEN 1 ELSE 0 END) as autorizados,
                SUM(CASE WHEN uso_seguro='VERIFICAR' THEN 1 ELSE 0 END) as pendientes,
                SUM(CASE WHEN formato IN ('jpg','jpeg','png') THEN 1 ELSE 0 END) as fotos,
                SUM(CASE WHEN formato IN ('mp4','mov') THEN 1 ELSE 0 END) as videos
                FROM sigaav.catalogo_gold""")

            if len(df_gen) > 0:
                row = df_gen.iloc[0]
                total = int(row['total'])
                autorizados = int(row['autorizados'])
                pendientes = int(row['pendientes'])
                fotos = int(row['fotos'])
                videos = int(row['videos'])
                pct = round(autorizados*100/total,1) if total > 0 else 0

                st.markdown("### Resumen general")
                c1,c2,c3,c4,c5 = st.columns(5)
                c1.metric("Total activos", total)
                c2.metric("Autorizados", autorizados, f"{pct}%")
                c3.metric("Requieren revisión", pendientes)
                c4.metric("Fotografías", fotos)
                c5.metric("Videos", videos)

            st.markdown("---")

            # Riesgo por dependencia
            st.markdown("### Riesgo legal por dependencia")
            df_riesgo = run_query("""SELECT dependencia,
                COUNT(*) as total,
                SUM(CASE WHEN uso_seguro='SI' THEN 1 ELSE 0 END) as autorizados,
                SUM(CASE WHEN uso_seguro='VERIFICAR' THEN 1 ELSE 0 END) as pendientes,
                ROUND(SUM(CASE WHEN uso_seguro='SI' THEN 1 ELSE 0 END)*100.0/COUNT(*),1) as pct_autorizado
                FROM sigaav.catalogo_gold
                GROUP BY dependencia ORDER BY pendientes DESC""")

            if len(df_riesgo) > 0:
                for _, r in df_riesgo.iterrows():
                    pct_dep = float(r['pct_autorizado'])
                    color = "🟢" if pct_dep==100 else "🟡" if pct_dep>=50 else "🔴"
                    col_d, col_t, col_a, col_p, col_pct = st.columns([3,1,1,1,1])
                    with col_d:
                        st.write(f"{color} {r['dependencia']}")
                    with col_t:
                        st.write(f"**{int(r['total'])}** total")
                    with col_a:
                        st.write(f"✅ {int(r['autorizados'])}")
                    with col_p:
                        if int(r['pendientes']) > 0:
                            st.write(f"⚠️ {int(r['pendientes'])}")
                        else:
                            st.write("—")
                    with col_pct:
                        st.write(f"{pct_dep}%")

            st.markdown("---")

            # Activos que requieren acción inmediata
            st.markdown("### Activos que requieren acción inmediata")
            df_urgente = run_query("""SELECT nombre_archivo, dependencia,
                estado_consentimiento, tipo_evento
                FROM sigaav.catalogo_gold
                WHERE uso_seguro='VERIFICAR'
                ORDER BY dependencia""")

            if len(df_urgente) == 0:
                st.success("No hay activos pendientes de verificación.")
            else:
                st.warning(f"{len(df_urgente)} activo(s) requieren atención:")
                st.dataframe(df_urgente, use_container_width=True)

            st.markdown("---")

            # Últimos activos registrados
            st.markdown("### Últimos activos registrados")
            df_recientes = run_query("""SELECT nombre_archivo, formato, dependencia,
                fecha_creacion, uso_seguro, fotografo
                FROM sigaav.catalogo_gold
                ORDER BY fecha_creacion DESC LIMIT 10""")
            if len(df_recientes) > 0:
                st.dataframe(df_recientes, use_container_width=True)

            # Consentimientos registrados
            st.markdown("---")
            st.markdown("### Consentimientos registrados")
            df_consent_stats = run_query("""SELECT
                COUNT(*) as total_consentimientos,
                SUM(CASE WHEN estado='verificado' THEN 1 ELSE 0 END) as verificados
                FROM sigaav.consentimientos_individuales""")
            df_avisos_stats = run_query("SELECT COUNT(*) as total_avisos FROM sigaav.avisos_publicos")

            ca, cb = st.columns(2)
            if len(df_consent_stats) > 0:
                ca.metric("Consentimientos individuales", int(df_consent_stats.iloc[0]['total_consentimientos']))
            if len(df_avisos_stats) > 0:
                cb.metric("Avisos públicos colectivos", int(df_avisos_stats.iloc[0]['total_avisos']))

        except Exception as e:
            st.error(f"Error al cargar el dashboard: {e}")
