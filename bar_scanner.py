import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Control ENEUN", layout="wide")

EVENTOS_POSIBLES = [
    "Llegada Campus",
    "Salida Campus",
    "Llegada Auditorio",
    "Salida Auditorio"
]

with st.sidebar:
    st.header("Configuracion de Control")

    lugar_control = st.radio(
        "Lugar de Registro:",
        ["Registro Campus", "Registro Auditorio"]
    )

    tipo_movimiento = st.selectbox(
        "Acción:",
        ["Llegada", "Salida"]
    )

    if lugar_control == "Registro Campus":
        evento_actual = f"{tipo_movimiento} Campus"
    else:
        evento_actual = f"{tipo_movimiento} Auditorio"

    st.divider()
    if st.button("Forzar Actualizacion Manual"):
        if 'df' in st.session_state:
            del st.session_state['df']
        st.rerun()

conn = st.connection("gsheets", type=GSheetsConnection)
URL_HOJA = "https://docs.google.com/spreadsheets/d/1ZiONmxy82-cDPqlqgCsK4qPtuEUL76UnjRFzEWyHg5Q/edit"
NOMBRE_PESTANA = "attendees"
NOMBRE_COLUMNA_DOCUMENTO = "identification_number"

col_estado = f"{evento_actual}_Estado"
col_hora = f"{evento_actual}_Hora"

def obtener_datos_frescos():
    df = conn.read(spreadsheet=URL_HOJA, worksheet=NOMBRE_PESTANA, ttl=0)
    df.columns = df.columns.astype(str).str.strip()
    df = df.dropna(how='all')

    if 'email' in df.columns:
        df['email_limpio'] = df['email'].astype(str).str.strip().str.lower().str.replace(" ", "")
    elif 'email_x' in df.columns:
        df['email_limpio'] = df['email_x'].astype(str).str.strip().str.lower().str.replace(" ", "")
    else:
        df['email_limpio'] = ""

    if NOMBRE_COLUMNA_DOCUMENTO in df.columns:
        df['doc_limpio'] = df[NOMBRE_COLUMNA_DOCUMENTO].astype(str).str.replace(".0", "", regex=False).str.strip().str.lower().str.replace(" ", "").str.replace(".", "").str.replace(",", "")
    else:
        df['doc_limpio'] = ""

    for ev in EVENTOS_POSIBLES:
        c_est = f"{ev}_Estado"
        c_hor = f"{ev}_Hora"
        if c_est not in df.columns:
            df[c_est] = 'No'
        if c_hor not in df.columns:
            df[c_hor] = ''
        df[c_est] = df[c_est].fillna('No')
        df[c_hor] = df[c_hor].fillna('')

    return df

if 'df' not in st.session_state:
    try:
        st.session_state.df = obtener_datos_frescos()
    except Exception as e:
        st.error(f"Error inicial: {e}")
        st.stop()
else:
    for ev in EVENTOS_POSIBLES:
        c_est = f"{ev}_Estado"
        c_hor = f"{ev}_Hora"
        if c_est not in st.session_state.df.columns:
            st.session_state.df[c_est] = 'No'
        if c_hor not in st.session_state.df.columns:
            st.session_state.df[c_hor] = ''

st.title(f"{lugar_control} - {tipo_movimiento}")
st.write("Escanea la escarapela o ingresa el dato manualmente.")

col_izq, col_der = st.columns([2, 1])

with col_izq:
    st.subheader("Registro")
    with st.form(key='formulario_escaneo', clear_on_submit=True):
        codigo_escaneado = st.text_input("Correo Electrónico o Documento de Identidad:")
        boton_registrar = st.form_submit_button(label='Registrar Asistencia')

    if boton_registrar and codigo_escaneado:
        try:
            df_fresco = obtener_datos_frescos()
            input_base = codigo_escaneado.strip().lower().replace(" ", "")

            if "@" in input_base:
                filtro = (df_fresco['email_limpio'] == input_base)
            else:
                input_doc = input_base.replace(".", "").replace(",", "")
                filtro = (df_fresco['doc_limpio'] == input_doc)

            if filtro.any():
                indice = df_fresco.index[filtro].tolist()[0]

                if 'badge_name' in df_fresco.columns and pd.notna(df_fresco.at[indice, 'badge_name']):
                    nombre_comp = str(df_fresco.at[indice, 'badge_name']).strip()
                elif 'legal_name' in df_fresco.columns:
                    nombre_comp = str(df_fresco.at[indice, 'legal_name']).strip()
                else:
                    nombre_comp = "Sin Nombre"

                sede_user = df_fresco.at[indice, 'sede'] if 'sede' in df_fresco.columns else "Sin Sede"
                estado_actual = str(df_fresco.at[indice, col_estado]).strip()

                if estado_actual == 'Sí':
                    st.warning(f"REPETIDO: {nombre_comp} ya fue registrado en '{evento_actual}' a las {df_fresco.at[indice, col_hora]}.")
                else:
                    hora_actual = datetime.now().strftime("%H:%M:%S")

                    df_fresco.at[indice, col_estado] = 'Sí'
                    df_fresco.at[indice, col_hora] = hora_actual

                    df_a_guardar = df_fresco.drop(columns=['email_limpio', 'doc_limpio'], errors='ignore')
                    conn.update(
                        spreadsheet=URL_HOJA,
                        worksheet=NOMBRE_PESTANA,
                        data=df_a_guardar
                    )

                    st.session_state.df = df_fresco

                    st.success(f"ASISTENCIA APROBADA Y GUARDADA: {evento_actual}")

                    with st.container(border=True):
                        st.markdown(f"**Participante:** {nombre_comp}")
                        st.markdown(f"**Sede:** {sede_user}")
                        st.markdown(f"**Registro:** {hora_actual}")

            else:
                st.error("DENEGADO: Correo o Documento no encontrado en la base de datos.")

        except Exception as e:
            st.error(f"Error al procesar el registro: {e}")

df_local = st.session_state.df
total_registrados = len(df_local)
total_asistentes = len(df_local[df_local[col_estado] == 'Sí'])
porcentaje = (total_asistentes / total_registrados) if total_registrados > 0 else 0.0

with col_der:
    st.subheader(f"Resumen: {evento_actual}")
    st.metric("Inscritos Totales", total_registrados)
    st.metric("Registrados", total_asistentes)
    st.progress(float(porcentaje))
