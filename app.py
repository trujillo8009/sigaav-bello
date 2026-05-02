import streamlit as st
from databricks import sql as dbsql
import pandas as pd
from datetime import datetime
import random

st.set_page_config(page_title="SIGAAV - Alcaldía de Bello", page_icon="🎬", layout="wide")

HOST = st.secrets["DATABRICKS_HOST"]
TOKEN = st.secrets["DATABRICKS_TOKEN"]
HTTP_PATH = st.secrets["DATABRICKS_HTTP_PATH"]

def get_conn():
    return dbsql.connect(server_hostname=HOST, http_path=HTTP_PATH, access_token=TOKEN)

def run_query(query):
    with get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall_arrow().to_pandas()

def gen_id():
    hoy = datetime.now()
    num = random.randint(1000, 9999)
    return f"CONS-{hoy.year}-{hoy.month:02d}-{hoy.day:02d}-{num}"

st.markdown("""
<div style='text-align:center;padding:1rem;background:#E6F1FB;border-radius:12px;margin-bottom:1rem'>
<h1 style='color:#185FA5;font-size:24px;margin:0'>SIGAAV</h1>
<p style='color:#378ADD;margin:4px 0 0'>Sistema de Gestión de Activos Audiovisuales</p>
<p style='color:#555;font-size:13px;margin:0'>Alcaldía de Bello · Dirección Administrativa de Comunicaciones</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📋 Registrar consentimiento", "📷 Registrar activo", "🔍 Buscar en catálogo"])

DEPENDENCIAS = ["Secretaría del Interior","Secretaría de Salud","Secretaría de Educación",
                "Secretaría de Infraestructura","Secretaría Social","Secretaría de Cultura",
                "Secretaría de Deportes","Despacho del Alcalde"]

with tab1:
    st.subheader("Nuevo consentimiento informado")
    nuevo_id = gen_id()
    st.success(f"**Código generado automáticamente:** `{nuevo_id}`")
    st.caption("Escriba este código en el formulario físico F-GCR-08 antes de que la persona lo firme.")
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre completo")
        fecha = st.date_input("Fecha de firma")
    with col2:
        documento = st.text_input("Documento de identidad")
        dependencia = st.selectbox("Dependencia", DEPENDENCIAS)
    evento = st.text_input("Nombre del evento o sesión")
    archivo = st.text_input("Nombre del PDF escaneado", placeholder="F-GCR-08-2026-05-02-001.pdf")
    if st.button("Registrar consentimiento", type="primary"):
        if not all([nombre, evento, archivo]):
            st.error("Complete todos los campos.")
        else:
            try:
                run_query(f"""INSERT INTO sigaav.consentimientos_individuales VALUES
                    ('{nuevo_id}','{nombre}','{str(fecha)}','{dependencia}','{archivo}','verificado')""")
                st.success(f"Consentimiento registrado. ID: `{nuevo_id}`")
                st.balloons()
            except Exception as e:
                st.error(f"Error: {e}")

with tab2:
    st.subheader("Nuevo activo audiovisual")
    col1, col2 = st.columns(2)
    with col1:
        a_nombre = st.text_input("Nombre del archivo", placeholder="foto_evento.jpg")
        a_dep = st.selectbox("Dependencia ", DEPENDENCIAS)
        a_cat = st.selectbox("Categoría", ["inauguracion","institucional","educacion",
                             "salud","obras","social","cultura","deporte"])
        a_fotografo = st.text_input("Nombre del fotógrafo / camarógrafo")
    with col2:
        a_formato = st.selectbox("Formato", ["jpg","png","mp4","mov"])
        a_resolucion = st.selectbox("Resolución", ["4K (3840x2160)","Full HD (1920x1080)",
                                    "HD (1280x720)","Estándar (1024x768)","Otra"])
        a_estado = st.selectbox("Estado del activo", ["activo","en_revision","archivado"])
        a_miniatura = st.text_input("URL de miniatura (opcional)", placeholder="https://...")

    a_tags = st.text_input("Palabras clave (separadas por comas)")
    a_tipo = st.selectbox("Tipo de consentimiento", [
        "sesion_controlada — Individual (formulario F-GCR-08)",
        "evento_masivo — Colectivo (aviso público grabado)"])
    tipo_val = a_tipo.split(" — ")[0]

    if tipo_val == "sesion_controlada":
        st.markdown("**Verificar consentimiento individual**")
        col_id, col_btn = st.columns([3,1])
        with col_id:
            cid_input = st.text_input("Código del consentimiento", placeholder="CONS-2026-05-02-0001")
        with col_btn:
            st.write("")
            if st.button("Verificar"):
                try:
                    df = run_query(f"""SELECT nombre_persona, dependencia
                        FROM sigaav.consentimientos_individuales
                        WHERE id_consentimiento='{cid_input}' AND estado='verificado'""")
                    if len(df) > 0:
                        st.success(f"Verificado: {df.iloc[0]['nombre_persona']}")
                        st.session_state['consent_ok'] = cid_input
                    else:
                        st.error("No se encontró ese consentimiento.")
                        st.session_state['consent_ok'] = None
                except Exception as e:
                    st.error(f"Error: {e}")

    if st.button("Registrar activo", type="primary"):
        if not a_nombre:
            st.error("Ingrese el nombre del archivo.")
        elif tipo_val == "sesion_controlada" and not st.session_state.get('consent_ok'):
            st.error("Debe verificar el consentimiento individual antes de registrar.")
        else:
            try:
                hoy = datetime.now()
                ubicacion = f"{a_dep.replace(' ','-')}/{hoy.year}/{a_nombre}"
                cid = f"'{st.session_state.get('consent_ok')}'" if tipo_val=="sesion_controlada" else "NULL"
                act_id = f"ACT-{int(datetime.now().timestamp())}"
                min_val = a_miniatura if a_miniatura else "NULL"
                min_sql = f"'{min_val}'" if a_miniatura else "NULL"
                fot_sql = f"'{a_fotografo}'" if a_fotografo else "NULL"
                run_query(f"""INSERT INTO sigaav.activos_audiovisuales
                    (id_activo,nombre_archivo,formato,tamano_mb,fecha_creacion,ubicacion_origen,
                     categoria,palabras_clave,dependencia,anio,id_consentimiento,tipo_evento,
                     estado_activo,resolucion,fotografo,url_miniatura)
                    VALUES ('{act_id}','{a_nombre}','{a_formato}',0,'{str(hoy.date())}',
                    '{ubicacion}','{a_cat}','{a_tags}','{a_dep}',{hoy.year},{cid},'{tipo_val}',
                    '{a_estado}','{a_resolucion}',{fot_sql},{min_sql})""")
                st.success(f"Activo registrado. ID: `{act_id}`")
                st.balloons()
            except Exception as e:
                st.error(f"Error: {e}")

with tab3:
    st.subheader("Catálogo de activos institucionales")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        busq = st.text_input("Buscar por palabras clave")
    with col2:
        filtro_tipo = st.selectbox("Tipo", ["Todos","Fotos (jpg/png)","Videos (mp4/mov)"])
    with col3:
        filtro_estado = st.selectbox("Estado", ["Todos","Solo autorizados","Requieren revisión"])
    with col4:
        filtro_activo = st.selectbox("Estado activo", ["Todos","activo","en_revision","archivado"])

    if st.button("Buscar en catálogo", type="primary"):
        try:
            where = "WHERE 1=1"
            if busq:
                where += f" AND (lower(palabras_clave) LIKE '%{busq.lower()}%' OR lower(nombre_archivo) LIKE '%{busq.lower()}%' OR lower(dependencia) LIKE '%{busq.lower()}%')"
            if filtro_tipo == "Fotos (jpg/png)":
                where += " AND formato IN ('jpg','png')"
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
                enlace_sharepoint, fotografo, resolucion, estado_activo, url_miniatura
                FROM sigaav.catalogo_gold {where} LIMIT 50""")

            total = len(df)
            ok = len(df[df['uso_seguro']=='SI']) if total > 0 else 0
            ver = len(df[df['uso_seguro']=='VERIFICAR']) if total > 0 else 0

            m1, m2, m3 = st.columns(3)
            m1.metric("Total encontrados", total)
            m2.metric("Autorizados", ok)
            m3.metric("Requieren revisión", ver)

            if total == 0:
                st.info("No se encontraron activos.")
            else:
                for _, row in df.iterrows():
                    with st.container():
                        col_img, col_info = st.columns([1, 3])
                        with col_img:
                            if pd.notna(row.get('url_miniatura')) and row['url_miniatura'] and row['url_miniatura'] != 'NULL':
                                st.image(row['url_miniatura'], width=160)
                            else:
                                tipo_icon = "🎬" if row['formato'] in ['mp4','mov'] else "🖼️"
                                st.markdown(f"<div style='width:160px;height:100px;background:#E6F1FB;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:40px'>{tipo_icon}</div>", unsafe_allow_html=True)
                        with col_info:
                            col_a, col_b = st.columns([3,1])
                            with col_a:
                                st.markdown(f"**{row['nombre_archivo']}**")
                                st.caption(f"{row['dependencia']} · {row['categoria']} · {row['palabras_clave']}")
                                if pd.notna(row.get('fotografo')) and row['fotografo'] and row['fotografo'] != 'None':
                                    st.caption(f"Fotografo: {row['fotografo']}")
                                if pd.notna(row.get('resolucion')) and row['resolucion']:
                                    st.caption(f"Resolucion: {row['resolucion']}")
                                consent_txt = row['nombre_persona'] if pd.notna(row['nombre_persona']) else "Aviso publico colectivo"
                                st.caption(f"Consentimiento: {consent_txt} — {row['estado_consentimiento']}")
                                badge_color = "#EAF3DE" if row['estado_activo']=='activo' else "#FAEEDA" if row['estado_activo']=='en_revision' else "#F5F5F5"
                                st.markdown(f"<span style='background:{badge_color};padding:2px 8px;border-radius:10px;font-size:12px'>{row['estado_activo']}</span>", unsafe_allow_html=True)
                            with col_b:
                                if row['uso_seguro'] == 'SI':
                                    st.success("Autorizado")
                                else:
                                    st.warning("Verificar")
                                if pd.notna(row['enlace_sharepoint']):
                                    st.link_button("Abrir archivo", row['enlace_sharepoint'])
                        st.divider()
        except Exception as e:
            st.error(f"Error: {e}")
