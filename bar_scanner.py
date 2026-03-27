import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Control ENEUN", layout="wide")

with st.sidebar:
    st.header("Configuracion de Control")
    
    categoria_control = st.selectbox(
        "Tipo de Control:",
        ["Ingreso al ENEUN", "Asistencia a Lugares"]
    )
    
    if categoria_control == "Ingreso al ENEUN":
        evento_actual = st.selectbox("Punto de Ingreso:", ["Llegada", "Salida"])
    elif categoria_control == "Asistencia a Lugares":
        evento_actual = st.selectbox("Lugar:", ["Banos", "Auditorio Principal", "Zona Camping", "Zona de Alimentacion"])

    st.divider()
    if st.button("Forzar Actualizacion Manual"):
        if 'df' in st.session_state:
            del st.session_state['df']
        st.rerun()

# 1. Crear la conexion a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
URL_HOJA = "https://docs.google.com/spreadsheets/d/1ZiONmxy82-cDPqlqgCsK4qPtuEUL76UnjRFzEWyHg5Q/edit"
NOMBRE_PESTANA = "attendees"
NOMBRE_COLUMNA_DOCUMENTO = "identification_number"

col_estado = f"{evento_actual}_Estado"
col_hora = f"{evento_actual}_Hora"

# Funcion para descargar y limpiar la base de datos fresca
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

    if col_estado not in df.columns:
        df[col_estado] = 'No'
    if col_hora not in df.columns:
        df[col_hora] = ''
        
    df[col_estado] = df[col_estado].fillna('No')
    df[col_hora] = df[col_hora].fillna('')
    return df

# Carga inicial para mostrar metricas al abrir la app
if 'df' not in st.session_state:
    try:
        st.session_state.df = obtener_datos_frescos()
    except Exception as e:
        st.error(f"Error inicial: {e}")
        st.stop()

st.title(categoria_control)
st.write(f"Operando control de: **{evento_actual}**")

col_izq, col_der = st.columns([2, 1])

with col_izq:
    st.subheader("Registro")
    with st.form(key='formulario_escaneo', clear_on_submit=True):
        codigo_escaneado = st.text_input("Correo Electrónico o Documento de Identidad:")
        boton_registrar = st.form_submit_button(label='Registrar Entrada')

    if boton_registrar and codigo_escaneado:
        try:
            # Descargamos la tabla fresca
            df_fresco = obtener_datos_frescos()
            
            # Limpieza basica (solo espacios y minusculas)
            input_base = codigo_escaneado.strip().lower().replace(" ", "")
            
            # LOGICA CORREGIDA: Detectar si es correo o documento
            if "@" in input_base:
                # Si tiene arroba, es correo. Buscamos directo en email_limpio
                filtro = (df_fresco['email_limpio'] == input_base)
            else:
                # Si no tiene arroba, asumimos que es documento. Le quitamos los puntos y comas.
                input_doc = input_base.replace(".", "").replace(",", "")
                filtro = (df_fresco['doc_limpio'] == input_doc)

            if filtro.any():
                indice = df_fresco.index[filtro].tolist()[0]
                
                # Obtener datos del usuario
                if 'badge_name' in df_fresco.columns and pd.notna(df_fresco.at[indice, 'badge_name']):
                    nombre_comp = str(df_fresco.at[indice, 'badge_name']).strip()
                elif 'legal_name' in df_fresco.columns:
                    nombre_comp = str(df_fresco.at[indice, 'legal_name']).strip()
                else:
                    nombre_comp = "Sin Nombre"
                    
                sede_user = df_fresco.at[indice, 'sede'] if 'sede' in df_fresco.columns else "Sin Sede"
                estado_actual = str(df_fresco.at[indice, col_estado]).strip()
                            
                if categoria_control == "Ingreso al ENEUN" and estado_actual == 'Sí':
                    st.warning(f"REPETIDO: {nombre_comp} ya fue registrado en {evento_actual} a las {df_fresco.at[indice, col_hora]}.")

                else:
                    hora_actual = datetime.now().strftime("%H:%M:%S")
                    es_reingreso = (categoria_control == "Asistencia a Lugares" and estado_actual == 'Sí')
                    
                    # Actualizar la tabla FRESCA
                    df_fresco.at[indice, col_estado] = 'Sí'
                    df_fresco.at[indice, col_hora] = hora_actual
                    
                    # Guardar inmediatamente en Google Sheets
                    df_a_guardar = df_fresco.drop(columns=['email_limpio', 'doc_limpio'], errors='ignore')
                    conn.update(
                        spreadsheet=URL_HOJA, 
                        worksheet=NOMBRE_PESTANA, 
                        data=df_a_guardar
                    )
                    
                    # Actualizar la pantalla
                    st.session_state.df = df_fresco 
                    
                    if es_reingreso:
                        st.success("REINGRESO APROBADO Y GUARDADO EN LA NUBE")
                    else:
                        st.success("ACCESO APROBADO Y GUARDADO EN LA NUBE")
                    
                    with st.container(border=True):
                        st.markdown(f"**Participante:** {nombre_comp}")
                        st.markdown(f"**Sede:** {sede_user}")
                        st.markdown(f"**Registro:** {hora_actual}")
                    
            else:
                st.error("DENEGADO: Correo o Documento no encontrado en la base de datos.")
                
        except Exception as e:
            st.error(f"Error al procesar el registro: {e}")

# Metricas usando la memoria local (se actualiza sola tras un escaneo)
df_local = st.session_state.df
total_registrados = len(df_local)
total_asistentes = len(df_local[df_local[col_estado] == 'Sí'])
porcentaje = (total_asistentes / total_registrados) if total_registrados > 0 else 0.0

with col_der:
    st.subheader("Resumen en Vivo")
    st.metric("Inscritos Totales", total_registrados)
    st.metric("Registrados hoy", total_asistentes)
    st.progress(float(porcentaje))
