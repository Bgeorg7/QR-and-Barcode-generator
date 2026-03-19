import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Control de Acceso ENEUN", layout="centered")

st.title("Sistema de Acreditacion y Acceso")

if 'df' not in st.session_state:
    try:
        st.session_state.df = pd.read_csv('datos_eneun.csv')
        
        if 'Asistencia' not in st.session_state.df.columns:
            st.session_state.df['Asistencia'] = 'No'
        if 'Hora_Ingreso' not in st.session_state.df.columns:
            st.session_state.df['Hora_Ingreso'] = ''
            
    except Exception as e:
        st.error(f"Error al cargar la base de datos inicial: {e}")
        st.stop()

st.subheader("Punto de Control")

with st.form(key='formulario_escaneo', clear_on_submit=True):
    codigo_escaneado = st.text_input("Escanee la escarapela aqui:")
    boton_registrar = st.form_submit_button(label='Registrar Ingreso')

if boton_registrar and codigo_escaneado:
    df = st.session_state.df
    codigo_limpio = codigo_escaneado.strip()
    filtro = df['uuid'] == codigo_limpio

    if filtro.any():
        indice = df.index[filtro].tolist()[0]
        nombre = f"{df.at[indice, 'first_name']} {df.at[indice, 'last_name']}"
        sede = df.at[indice, 'SEDE']

        if df.at[indice, 'Asistencia'] == 'Sí':
            st.warning(f"Atencion: {nombre} ya habia registrado su ingreso a las {df.at[indice, 'Hora_Ingreso']}.")
        else:
            hora_actual = datetime.now().strftime("%H:%M:%S")
            st.session_state.df.at[indice, 'Asistencia'] = 'Sí'
            st.session_state.df.at[indice, 'Hora_Ingreso'] = hora_actual
            
            st.success(f"Acceso aprobado: {nombre} | Sede: {sede}")
    else:
        st.error("Acceso denegado: El codigo no existe en la base de datos. No puede pasar señor agente.")

st.divider()
st.subheader("Resumen del Evento")

total_registrados = len(st.session_state.df)
total_asistentes = len(st.session_state.df[st.session_state.df['Asistencia'] == 'Sí'])

col1, col2 = st.columns(2)
col1.metric("Total de Estudiantes Inscritos", total_registrados)
col2.metric("Asistentes Confirmados Hoy", total_asistentes)

st.write("Al finalizar la jornada, descargue el archivo actualizado para actualizar la base de datos principal.")

csv_final = st.session_state.df.to_csv(index=False).encode('utf-8')

st.download_button(
    label="Descargar Reporte de Asistencia Final",
    data=csv_final,
    file_name="asistencia_oficial_eneun.csv",
    mime="text/csv"
)
