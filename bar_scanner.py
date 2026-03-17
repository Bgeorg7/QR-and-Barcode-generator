import streamlit as st
import pandas as pd
from datetime import datetime

# Configuracion inicial de la interfaz
st.set_page_config(page_title="Control de Acceso ENEUN", layout="centered")

st.title("Sistema de Acreditacion y Acceso")

# 1. Cargar la base de datos en la memoria de la sesion
# Esto evita que se borren los datos cada vez que escaneamos a alguien
if 'df' not in st.session_state:
    try:
        # Aqui pones el nombre de tu archivo CSV real generado en la Parte 1
        st.session_state.df = pd.read_csv('datos_eneun.csv')
        
        # Aseguramos que existan las columnas de control
        if 'Asistencia' not in st.session_state.df.columns:
            st.session_state.df['Asistencia'] = 'No'
        if 'Hora_Ingreso' not in st.session_state.df.columns:
            st.session_state.df['Hora_Ingreso'] = ''
            
    except Exception as e:
        st.error(f"Error al cargar la base de datos inicial: {e}")
        st.stop()

# 2. Interfaz de Escaneo (Lectura de la pistola)
st.subheader("Punto de Control")

# Usamos un formulario para que al disparar la pistola (que da Enter automatico), se envie el dato
with st.form(key='formulario_escaneo', clear_on_submit=True):
    codigo_escaneado = st.text_input("Escanee la escarapela aqui:", autofocus=True)
    boton_registrar = st.form_submit_button(label='Registrar Ingreso')

# 3. Logica de validacion
if boton_registrar and codigo_escaneado:
    df = st.session_state.df
    # Limpiamos espacios por si acaso
    codigo_limpio = codigo_escaneado.strip()
    filtro = df['uuid'] == codigo_limpio

    if filtro.any():
        indice = df.index[filtro].tolist()[0]
        nombre = f"{df.at[indice, 'first_name']} {df.at[indice, 'last_name']}"
        sede = df.at[indice, 'SEDE']

        # Validar si ya habia entrado
        if df.at[indice, 'Asistencia'] == 'Sí':
            st.warning(f"Atencion: {nombre} ya habia registrado su ingreso a las {df.at[indice, 'Hora_Ingreso']}.")
        else:
            # Registrar asistencia en la memoria de la sesion
            hora_actual = datetime.now().strftime("%H:%M:%S")
            st.session_state.df.at[indice, 'Asistencia'] = 'Sí'
            st.session_state.df.at[indice, 'Hora_Ingreso'] = hora_actual
            
            st.success(f"Acceso aprobado: {nombre} | Sede: {sede}")
    else:
        st.error("Acceso denegado: El codigo no existe en la base de datos. No puede pasar señor agente.")

# 4. Estadisticas en tiempo real y Exportacion final
st.divider()
st.subheader("Resumen del Evento")

total_registrados = len(st.session_state.df)
total_asistentes = len(st.session_state.df[st.session_state.df['Asistencia'] == 'Sí'])

col1, col2 = st.columns(2)
col1.metric("Total de Estudiantes Inscritos", total_registrados)
col2.metric("Asistentes Confirmados Hoy", total_asistentes)

st.write("Al finalizar la jornada, descargue el archivo actualizado para actualizar la base de datos principal.")

# Convertir el dataframe actualizado a CSV para descargarlo
csv_final = st.session_state.df.to_csv(index=False).encode('utf-8')

st.download_button(
    label="Descargar Reporte de Asistencia Final",
    data=csv_final,
    file_name="asistencia_oficial_eneun.csv",
    mime="text/csv"
)
