import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Control ENEUN", layout="wide")

with st.sidebar:
    st.header("Configuracion de Control")
    
    categoria_control = st.selectbox(
        "Tipo de Control:",
        [
            "Ingreso al ENEUN", 
            "Asistencia a Lugares"
        ]
    )
    
    if categoria_control == "Ingreso al ENEUN":
        evento_actual = st.selectbox("Punto de Ingreso:", ["Llegada", "Salida"])
    elif categoria_control == "Asistencia a Lugares":
        evento_actual = st.selectbox("Lugar:", ["Banos", "Auditorio Principal", "Zona Camping", "Zona de Alimentacion"])

    st.divider()
    if st.button("Reiniciar Historial de Sesion"):
        if 'df' in st.session_state:
            del st.session_state['df']
        st.success("Base de datos local reiniciada. Se han vuelto a cargar los datos persistentes de la nube.")
        st.rerun()

# 1. Crear la conexion a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

URL_HOJA = "https://docs.google.com/spreadsheets/d/1ZiONmxy82-cDPqlqgCsK4qPtuEUL76UnjRFzEWyHg5Q/edit"
NOMBRE_PESTANA = "attendees"

# Actualizado con el nombre real de tu columna
NOMBRE_COLUMNA_DOCUMENTO = "identification_number"

if 'df' not in st.session_state:
    try:
        # 2. Leer los datos desde la nube
        # ELIMINAMOS el limite de columnas y filas para que lea la hoja completa
        # y no borre las columnas nuevas de asistencia.
        df_inicial = conn.read(
            spreadsheet=URL_HOJA,
            worksheet=NOMBRE_PESTANA,
            ttl=0 
        )
        
        # Limpiar espacios en los nombres de las columnas
        df_inicial.columns = df_inicial.columns.astype(str).str.strip()
        
        # Eliminar filas que esten completamente vacias por si Sheets lee filas extra
        df_inicial = df_inicial.dropna(how='all')
        
        # Limpiar columna de Correo
        if 'email' in df_inicial.columns:
            df_inicial['email_limpio'] = df_inicial['email'].astype(str).str.strip().str.lower().str.replace(" ", "")
        elif 'email_x' in df_inicial.columns:
            df_inicial['email_limpio'] = df_inicial['email_x'].astype(str).str.strip().str.lower().str.replace(" ", "")
        else:
            st.error("No se encontro una columna de correo electronico valida en la base de datos.")
            st.stop()
            
        # Limpiar columna de Documento (quita puntos, comas y espacios)
        if NOMBRE_COLUMNA_DOCUMENTO in df_inicial.columns:
            # Eliminamos el .0 al final si pandas lo leyo como decimal, y quitamos puntos/comas
            df_inicial['doc_limpio'] = df_inicial[NOMBRE_COLUMNA_DOCUMENTO].astype(str).str.replace(".0", "", regex=False).str.strip().str.lower().str.replace(" ", "").str.replace(".", "").str.replace(",", "")
        else:
            df_inicial['doc_limpio'] = ""
            st.warning(f"No se encontro la columna '{NOMBRE_COLUMNA_DOCUMENTO}'. Solo se buscara por correo.")
            
        st.session_state.df = df_inicial
    except Exception as e:
        st.error(f"Error conectando con Google Sheets: {e}. Verifica tus credenciales y el enlace.")
        st.stop()

col_estado = f"{evento_actual}_Estado"
col_hora = f"{evento_actual}_Hora"

# Crear columnas si no existen en el DataFrame traido de Sheets
if col_estado not in st.session_state.df.columns:
    st.session_state.df[col_estado] = 'No'
if col_hora not in st.session_state.df.columns:
    st.session_state.df[col_hora] = ''

# Asegurarse de que si habia valores nulos (NaN) en la nube, se traten como 'No' o vacios
st.session_state.df[col_estado] = st.session_state.df[col_estado].fillna('No')
st.session_state.df[col_hora] = st.session_state.df[col_hora].fillna('')

df_local = st.session_state.df

st.title(categoria_control)
st.write(f"Operando control de: **{evento_actual}**")

col_izq, col_der = st.columns([2, 1])

with col_izq:
    st.subheader("Registro")
    with st.form(key='formulario_escaneo', clear_on_submit=True):
        codigo_escaneado = st.text_input("Correo Electrónico o Documento de Identidad:")
        boton_registrar = st.form_submit_button(label='Registrar Entrada')

    if boton_registrar and codigo_escaneado:
        # Limpiamos el texto ingresado
        input_limpio = codigo_escaneado.strip().lower().replace(" ", "").replace(".", "").replace(",", "")
        
        filtro = (df_local['email_limpio'] == input_limpio) | (df_local['doc_limpio'] == input_limpio)

        if filtro.any():
            indice = df_local.index[filtro].tolist()[0]
            
            if 'badge_name' in df_local.columns and pd.notna(df_local.at[indice, 'badge_name']):
                nombre_comp = str(df_local.at[indice, 'badge_name']).strip()
            elif 'legal_name' in df_local.columns:
                nombre_comp = str(df_local.at[indice, 'legal_name']).strip()
            else:
                nombre_comp = "Sin Nombre"
                
            sede_user = df_local.at[indice, 'sede'] if 'sede' in df_local.columns else "Sin Sede"
            estado_actual = str(df_local.at[indice, col_estado]).strip()
                        
            if categoria_control == "Ingreso al ENEUN" and estado_actual == 'Sí':
                st.warning(f"REPETIDO: {nombre_comp} ya fue registrado en {evento_actual} a las {df_local.at[indice, col_hora]}.")

            else:
                hora_actual = datetime.now().strftime("%H:%M:%S")
                es_reingreso = (categoria_control == "Asistencia a Lugares" and estado_actual == 'Sí')
                
                # Actualizar memoria local
                st.session_state.df.at[indice, col_estado] = 'Sí'
                st.session_state.df.at[indice, col_hora] = hora_actual
                
                # Guardar el cambio directamente en Google Sheets
                try:
                    # Quitamos las columnas temporales de busqueda antes de subir a la nube
                    df_a_guardar = st.session_state.df.drop(columns=['email_limpio', 'doc_limpio'], errors='ignore')
                    conn.update(
                        spreadsheet=URL_HOJA, 
                        worksheet=NOMBRE_PESTANA, 
                        data=df_a_guardar
                    )
                    
                    if es_reingreso:
                        st.success("REINGRESO APROBADO Y GUARDADO EN LA NUBE")
                    else:
                        st.success("ACCESO APROBADO Y GUARDADO EN LA NUBE")
                except Exception as e:
                    st.error(f"Acceso aprobado localmente, pero fallo al guardar en Google Sheets: {e}")
                
                with st.container(border=True):
                    st.markdown(f"**Participante:** {nombre_comp}")
                    st.markdown(f"**Sede:** {sede_user}")
                    st.markdown(f"**Registro:** {hora_actual}")
                
        else:
            st.error("DENEGADO: Correo o Documento no encontrado en la base de datos.")

total_registrados = len(df_local)
total_asistentes = len(df_local[df_local[col_estado] == 'Sí'])
porcentaje = (total_asistentes / total_registrados) if total_registrados > 0 else 0.0

with col_der:
    st.subheader("Resumen en Vivo")
    st.metric("Inscritos Totales", total_registrados)
    st.metric("Registrados hoy", total_asistentes)
    st.progress(float(porcentaje))
